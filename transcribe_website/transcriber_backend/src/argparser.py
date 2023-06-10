"""
A argparser to run commands from terminal. 
For examples see at the bottom.
"""
from __future__ import annotations

import datetime
import json
import sys
import time
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from faster_whisper import WhisperModel, format_timestamp
from faster_whisper.transcribe import TranscriptionInfo
from loguru import logger
from pony import orm
from simple_parsing import ArgumentParser
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from db_transcriber import JobItem, JobStatus, ModelSize, OutputResult, Task
from src.secrets_loader import SECRETS


@dataclass
class TranscriberOptions:
    input_file: str  # Choose file
    output_file: str | None = None
    task: Task = Task.Transcribe  # Transcribe, translate or detect language
    language: str | None = None  # Force this language to transcribe or translate, e.g. "en"
    model: ModelSize | None = None  # One of the models: tiny, base, small, medium, large, largev1
    update_progress_to_database: bool = True
    # If given, will update the database entry
    database_job_id: int | None = None
    # TODO what do these do
    num_workers: int = 1
    cpu_threads: int = 0

    @property
    def input_file_path(self) -> Path:
        return Path(self.input_file)

    @property
    def output_file_path(self) -> Path:
        if self.output_file is None:
            parent_folder = self.input_file_path.parent
            file_name_stem = self.input_file_path.stem
            return parent_folder / f"{file_name_stem}.ending"
        return Path(self.output_file)

    @property
    def txt_file_path(self) -> Path:
        parent_folder = self.output_file_path.parent
        file_name_stem = self.output_file_path.stem
        return parent_folder / f"{file_name_stem}.txt"

    @property
    def srt_file_path(self) -> Path:
        parent_folder = self.output_file_path.parent
        file_name_stem = self.output_file_path.stem
        return parent_folder / f"{file_name_stem}.srt"

    @property
    def zip_file_path(self) -> Path:
        parent_folder = self.output_file_path.parent
        file_name_stem = self.output_file_path.stem
        return parent_folder / f"{file_name_stem}.zip"


MODEL_MAP = {
    ModelSize.Tiny: "tiny",
    ModelSize.Base: "base",
    ModelSize.Small: "small",
    ModelSize.Medium: "medium",
    ModelSize.Large: "large-v2",
}


def update_job_status(
    job_id: int | None,
    new_status: JobStatus,
    result: BytesIO | None = None,
    job_started: datetime.datetime | None = None,
) -> None:
    if job_id is not None:
        with orm.db_session():
            job_info = JobItem[job_id]
            job_info.status = new_status.name
            if result is not None:
                job_info.output_zip_data = OutputResult(
                    job_item=job_info,
                    zip_data=result.getvalue(),
                )
                job_info.job_completed = datetime.datetime.utcnow()
                # Delete input mp3 file and db entry to clear up storage
                job_info.input_file_mp3.delete()
                job_info.input_file_mp3 = None
            if job_started is not None:
                job_info.job_started = job_started


def get_model_string(options: TranscriberOptions) -> str:
    model_map = MODEL_MAP.copy()
    if options.language == "en":
        # Use better english models if forced language was "en"
        model_map = {
            **model_map,
            ModelSize.Tiny: "tiny.en",
            ModelSize.Base: "base.en",
            ModelSize.Small: "small.en",
            ModelSize.Medium: "medium.en",
        }
    return model_map[options.model]


def detect_language(options: TranscriberOptions) -> TranscriptionInfo:
    model_size = get_model_string(options)
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
        download_root="./whisper_models",
    )
    update_job_status(options.database_job_id, new_status=JobStatus.PROCESSING)

    if options.input_file == "-":
        data = BytesIO(sys.stdin.buffer.read())
        _, info = model.transcribe(data)
    else:
        assert options.input_file_path.is_file()
        _, info = model.transcribe(str(options.input_file_path.absolute()))

    # Upload info to db and mark job as finished
    sorted_results: list[tuple[str, float]] = sorted(info.all_language_probs, key=lambda x: x[1], reverse=True)
    update_job_status(options.database_job_id, new_status=JobStatus.DONE, result=json.dumps(sorted_results).encode())
    logger.debug(sorted_results[:10])
    return info


def transcribe(options: TranscriberOptions) -> None:
    # Sanity checks
    assert options.input_file == "-" or options.input_file_path.is_file(), "Input file does not exist"
    assert not options.output_file_path.is_file(), "Output already exists"

    # Load model
    t0 = time.perf_counter()
    model_size = get_model_string(options)
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
        download_root="./whisper_models",
        # TODO What does this do
        num_workers=options.num_workers,
        cpu_threads=options.cpu_threads,
    )

    logger.debug(f"Loading model {model_size} took {time.perf_counter() - t0:3f} seconds")

    if options.input_file == "-":
        data = BytesIO(sys.stdin.buffer.read())
        segments, info = model.transcribe(data, language=options.language)
    else:
        segments, info = model.transcribe(str(options.input_file_path.absolute()), language=options.language)

    if options.language is None:
        logger.debug(f"Detected language '{info.language}' with probability {info.language_probability}")

    # Start transcribing / translating
    # Not needed?
    update_job_status(
        options.database_job_id,
        JobStatus.PROCESSING,
        job_started=datetime.datetime.now(),
    )
    t0 = time.perf_counter()
    last_progress_bar_value: int = 0
    last_job_progress_value: int = 0
    transcribed_data: list[tuple[float, float, str]] = []
    total_mp3_duration = int(info.duration)
    with tqdm(total=total_mp3_duration, mininterval=1) as progress_bar:
        for segment in segments:
            progress_bar.update(int(segment.end) - last_progress_bar_value)
            last_progress_bar_value = int(segment.end)
            transcribed_data.append((segment.start, segment.end, segment.text.lstrip()))
            # print(f"{segment.start:.2f} {segment.end:.2f} {segment.text}")
            # Upload info to database
            if options.database_job_id is not None:
                # Update only if percentage value changed
                new_job_progress_value = int(100 * last_progress_bar_value / total_mp3_duration)
                if last_job_progress_value != new_job_progress_value:
                    last_job_progress_value = new_job_progress_value
                    with orm.db_session():
                        job = JobItem[options.database_job_id]
                        job.progress = new_job_progress_value

    logger.debug(f"Done transcribing after {time.perf_counter() - t0:3f} seconds")
    update_job_status(options.database_job_id, JobStatus.FINISHING)
    # Write to .zip in memory to be uploaded to supabase directly
    write_data(transcribed_data, options)


def generate_txt_data(transcribed_data: list[tuple[float, float, str]]) -> str:
    data_list = []
    for line in transcribed_data:
        data_list.append(f"{line[2]}\n")
    return "".join(data_list)


def generate_srt_data(transcribed_data: list[tuple[float, float, str]]) -> str:
    # def seconds_to_timestamp(seconds: float) -> str:
    #     minutes, seconds = divmod(seconds, 60)
    #     hours, minutes = divmod(minutes, 60)
    #     milliseconds = f"{seconds:.3f}".split(".")[1]
    #     return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds}"
    data_list = []
    for i, line in enumerate(transcribed_data, start=1):
        data_list.append(f"{i}\n")
        start = format_timestamp(line[0], always_include_hours=True, decimal_marker=",")
        end = format_timestamp(line[1], always_include_hours=True, decimal_marker=",")
        data_list.append(f"{start} --> {end}\n")
        data_list.append(f"{line[2]}\n\n")
    return "".join(data_list)


def compress_files(files: dict[str, str]) -> BytesIO:
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
        for file_name, file_content in files.items():
            zip_file.writestr(file_name, file_content)
    return zip_data


def write_data(transcribed_data: list[tuple[float, float, str]], options: TranscriberOptions) -> None:
    """
    From the transcribed data, generate the txt or srt files or a zip-file with both.
    Write result to "output_file"
    Special cases:
        output_file = "-"
            Write resulting .zip to stdout
        output_file = "*.txt"
            Write resulting .txt to target file
        output_file = "*.srt"
            Write resulting .srt to target file
        output_file = "*.zip"
            Write resulting .zip to target file
    """
    txt_data: str = generate_txt_data(transcribed_data)
    srt_data: str = generate_srt_data(transcribed_data)
    zip_data: BytesIO = compress_files({
        "transcribed.txt": txt_data,
        "transcribed.srt": srt_data,
    })

    if options.database_job_id is not None:
        update_job_status(
            options.database_job_id,
            new_status=JobStatus.DONE,
            result=zip_data,
        )
        return

    if options.output_file == "-":
        sys.stdout.buffer.write(zip_data.getvalue())
        return

    if options.output_file is None:
        with options.txt_file_path.open("w") as f:
            f.write(txt_data)
        with options.srt_file_path.open("w") as f:
            f.write(srt_data)
        with options.zip_file_path.open("wb") as f:
            f.write(zip_data.getvalue())
        return

    if options.output_file_path.suffix == ".txt":
        with options.output_file_path.open("w") as f:
            f.write(txt_data)
        return
    if options.output_file_path.suffix == ".srt":
        with options.output_file_path.open("w") as f:
            f.write(srt_data)
        return
    if options.output_file_path.suffix == ".zip":
        with options.output_file_path.open("wb") as f:
            f.write(zip_data)
        return
    assert False, f"Shouldn't get here, output_file was {options.output_file}"


parser = ArgumentParser()
parser.add_arguments(TranscriberOptions, dest="options")  # pyre-fixme[6]


def main():
    args = parser.parse_args()
    options: TranscriberOptions = args.options
    # logger.debug(f"Options: {options}")
    # Not needed?
    update_job_status(options.database_job_id, JobStatus.ACCEPTED)
    if options.task in {Task.Transcribe, Task.Translate}:
        transcribe(options)
    elif options.task == Task.Detect:
        detect_language(options)


if __name__ == "__main__":
    """
poetry run python src/argparser.py --input_file "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3" --task Transcribe --model Small

poetry run python src/argparser.py --input_file "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3" --task Transcribe --model Small --output_file - > result.zip

poetry run python src/argparser.py --input_file "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3" --task Transcribe --language en --model Small

poetry run python src/argparser.py --input_file "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3" --task Transcribe --language en --model Small --output_file - > result.zip

poetry run python src/argparser.py --input_file - --task Transcribe --language en --model Small --output_file - > result2.zip < test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3

poetry run python src/argparser.py --input_file "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3" --task Detect --model Small

poetry run python src/argparser.py --input_file - --task Detect --model Small < "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3"

poetry run python src/argparser.py --input_file "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3" --task Translate --model Tiny
    """
    main()
