"""
A argparser to run commands from terminal. For examples see at the bottom
"""

import enum
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel, format_timestamp
from faster_whisper.transcribe import TranscriptionInfo
from loguru import logger
from simple_parsing import ArgumentParser
from tqdm import tqdm

MODELS_ROOT = os.getenv("MODELS_ROOT", "./whisper_models")


class Task(enum.Enum):
    Transcribe = 0
    Translate = 1
    Detect = 2


class ModelSize(enum.Enum):
    tiny = 0
    base = 1
    small = 2
    medium = 3
    large = 4
    # largev1 = 5


@dataclass
class TranscriberOptions:
    file: str  # Choose file
    task: Task = Task.Transcribe  # Transcribe, translate or detect language
    language: str | None = None  # Force this language to transcribe or translate, e.g. "en"
    model: ModelSize | None = None  # One of the models: tiny, base, small, medium, large, largev1
    update_progress_to_supabase: bool = True
    output_dir: str | None = None
    write_srt_file: bool = True
    write_txt_file: bool = True
    keep_nested_file_structure: bool = False
    num_workers: int = 0
    cpu_threads: int = 1


MODEL_MAP = {
    ModelSize.tiny: "tiny",
    ModelSize.base: "base",
    ModelSize.small: "small",
    ModelSize.medium: "medium",
    ModelSize.large: "large",
    # ModelSize.largev1: "large-v1",
}


def get_model_string(options: TranscriberOptions) -> str:
    model_map = MODEL_MAP.copy()
    if options.language == "en":
        # Use better english models if forced language was "en"
        model_map = {
            **model_map,
            ModelSize.tiny: "tiny.en",
            ModelSize.base: "base.en",
            ModelSize.small: "small.en",
            ModelSize.medium: "medium.en",
        }
    return model_map[options.model]


def get_total_length_of_file(file_path: Path) -> float:
    # Sanity checks
    assert file_path.is_file()
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path.absolute()),
        ],
        capture_output=True
    )
    assert result.returncode == 0
    return float(result.stdout)


def detect_language(options: TranscriberOptions) -> TranscriptionInfo:
    # Sanity checks
    file_path = Path(options.file)
    assert file_path.is_file()

    model_size = get_model_string(options)
    model = WhisperModel(model_size, device="cpu", compute_type="int8", download_root=MODELS_ROOT)
    _, info = model.transcribe(str(file_path.absolute()), beam_size=5, language=options.language)
    # TODO Upload info to supabase and mark job as finished
    for language_code, probability in reversed(info.all_language_probs[:10]):
        logger.info(f"{language_code} - {probability}")
    return info


def transcribe(options: TranscriberOptions):
    # Sanity checks
    file_path = Path(options.file)
    assert file_path.is_file()
    output_paths = get_file_paths(options)
    if output_paths["out_srt"].is_file():
        logger.info(f"Already transcribed '{Path(options.file).name}'")
        return

    # TODO Allow more languages, or extract from open_whisper
    assert options.language in {"en", "de", None}

    # Load model
    t0 = time.perf_counter()
    model_size = get_model_string(options)
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
        download_root=MODELS_ROOT,
        num_workers=options.num_workers,
        cpu_threads=options.cpu_threads,
    )
    logger.debug(f"Loading model {model_size} took {time.perf_counter() - t0:3f} seconds")

    segments, info = model.transcribe(str(file_path.absolute()), beam_size=5, language=options.language)
    logger.debug(f"Detected language '{info.language}' with probability {info.language_probability}")

    # Start transcribing / translating
    t0 = time.perf_counter()
    total_mp3_duration = get_total_length_of_file(Path(options.file))
    last_value = 0
    transcribed_data: list[tuple[float, float, str]] = []
    with tqdm(total=int(total_mp3_duration), mininterval=1) as progress_bar:
        for segment in segments:
            progress_bar.update(int(segment.end) - last_value)
            last_value = int(segment.end)
            transcribed_data.append((segment.start, segment.end, segment.text.lstrip()))
            # print(f"{segment.start:.2f} {segment.end:.2f} {segment.text}")
            # TODO Upload info to supabase
            continue

    logger.debug(f"Done transcribing after {time.perf_counter() - t0:3f} seconds")
    # TODO Write to .zip in memory to be uploaded to supabase directly
    write_data(transcribed_data, options)


def get_file_paths(options: TranscriberOptions) -> dict[str, Path]:
    file_path = Path(options.file)
    file_name = file_path.stem
    output_path = Path(options.output_dir) if options.output_dir is not None else Path(options.file).parent
    if options.keep_nested_file_structure:
        output_path = output_path / file_path.parent.relative_to(".")
    return {
        "output_folder_path": output_path,
        "out_txt": output_path / f"{file_name}.txt",
        "out_txt_temp": output_path / f"{file_name}.txt.temp",
        "out_srt": output_path / f"{file_name}.srt",
        "out_srt_temp": output_path / f"{file_name}.srt.temp",
    }


def write_data(transcribed_data: list[tuple[float, float, str]], options: TranscriberOptions):
    output_paths = get_file_paths(options)
    output_folder_path = output_paths["output_folder_path"]
    output_folder_path.mkdir(parents=True, exist_ok=True)
    if options.write_txt_file:
        out_txt, out_txt_temp = output_paths["out_txt"], output_paths["out_txt_temp"]
        with out_txt_temp.open("w") as f:
            for line in transcribed_data:
                f.write(f"{line[2]}\n")
        out_txt_temp.rename(out_txt)

    # def seconds_to_timestamp(seconds: float) -> str:
    #     minutes, seconds = divmod(seconds, 60)
    #     hours, minutes = divmod(minutes, 60)
    #     milliseconds = f"{seconds:.3f}".split(".")[1]
    #     return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds}"

    if options.write_srt_file:
        out_srt, out_srt_temp = output_paths["out_srt"], output_paths["out_srt_temp"]
        with out_srt_temp.open("w") as f:
            for i, line in enumerate(transcribed_data, start=1):
                f.write(f"{i}\n")
                start = format_timestamp(line[0], always_include_hours=True, decimal_marker=",")
                end = format_timestamp(line[1], always_include_hours=True, decimal_marker=",")
                f.write(f"{start} --> {end}\n")
                f.write(f"{line[2]}\n\n")
        out_srt_temp.rename(out_srt)


parser = ArgumentParser()
parser.add_arguments(TranscriberOptions, dest="options")  # pyre-fixme[6]


def main():
    args = parser.parse_args()
    options: TranscriberOptions = args.options
    logger.debug(f"Options: {options}")
    if options.task in {Task.Transcribe, Task.Translate}:
        transcribe(options)
    elif options.task == Task.Detect:
        detect_language(options)


if __name__ == "__main__":
    """
poetry run python src/argparser.py --file "test/Eclypxe - Black Roses (ft. Annamarie Rosanio) Copyright Free Music.mp3" --task Transcribe --model tiny

poetry run python src/argparser.py --file "test/Eclypxe - Black Roses (ft. Annamarie Rosanio) Copyright Free Music.mp3" --task Transcribe --language en --model tiny

poetry run python src/argparser.py --file "test/Eclypxe - Black Roses (ft. Annamarie Rosanio) Copyright Free Music.mp3" --task Detect --model tiny

poetry run python src/argparser.py --file "test/Eclypxe - Black Roses (ft. Annamarie Rosanio) Copyright Free Music.mp3" --task Translate --model tiny

poetry run python src/argparser.py --file "test/Eclypxe - Black Roses (ft. Annamarie Rosanio) Copyright Free Music.mp3" --output_dir result --task Transcribe --model tiny --cpu_threads 0 --num_workers 1
    """
    main()
