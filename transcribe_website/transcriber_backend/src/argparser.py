"""
A argparser to run commands from terminal.
For examples, see at the bottom.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from faster_whisper import WhisperModel  # pyre-fixme[21]
from faster_whisper.transcribe import TranscriptionInfo  # pyre-fixme[21]
from loguru import logger
from simple_parsing import ArgumentParser
from tqdm import tqdm

sys.path.append(".")

from src.models.db import (  # noqa: E402 I001
    ModelSize, Task, compress_files, generate_srt_data, generate_txt_data,
)


@dataclass
class TranscriberOptions:
    input_file: str  # Choose file
    output_file: str | None = None
    task: Task = Task.Transcribe  # Transcribe, translate or detect language
    language: str | None = None  # Force this language to transcribe or translate, e.g. "en"
    model: ModelSize | None = None  # One of the models: tiny, base, small, medium, large, largev1

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


def get_model_string(options: TranscriberOptions) -> str:
    model_map = MODEL_MAP.copy()
    # TODO Use general model first to detect language, then use 'en' model if english was detected?!
    # What if an audio has multiple languages?
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


# pyre-fixme[11]
def detect_language(options: TranscriberOptions) -> TranscriptionInfo:
    model_size = get_model_string(options)
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
        download_root="./whisper_models",
    )

    if options.input_file == "-":
        data = BytesIO(sys.stdin.buffer.read())
        _, info = model.transcribe(data)
    else:
        assert options.input_file_path.is_file()
        _, info = model.transcribe(str(options.input_file_path.absolute()))

    # Upload info to db and mark job as finished
    sorted_results: list[tuple[str, float]] = sorted(info.all_language_probs, key=lambda x: x[1], reverse=True)
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
    )

    logger.debug(f"Loading model {model_size} took {time.perf_counter() - t0:3f} seconds")

    if options.input_file == "-":
        data = BytesIO(sys.stdin.buffer.read())
        segments, info = model.transcribe(data, language=options.language, task=options.task.name.lower())
    else:
        segments, info = model.transcribe(
            str(options.input_file_path.absolute()), language=options.language, task=options.task.name.lower()
        )

    if options.language is None:
        logger.debug(f"Detected language '{info.language}' with probability {info.language_probability}")

    # Start transcribing / translating
    t0 = time.perf_counter()
    last_progress_bar_value: int = 0
    transcribed_data: list[tuple[float, float, str]] = []
    total_mp3_duration = int(info.duration)
    with tqdm(total=total_mp3_duration, mininterval=1) as progress_bar:
        for segment in segments:
            progress_bar.update(int(segment.end) - last_progress_bar_value)
            last_progress_bar_value = int(segment.end)
            transcribed_data.append((segment.start, segment.end, segment.text.lstrip()))
            # TODO Translate from english to german
            # print(f"{segment.start:.2f} {segment.end:.2f} {segment.text}")

    logger.debug(f"Done transcribing/translating after {time.perf_counter() - t0:3f} seconds")
    # Write to .zip in memory to be uploaded to supabase directly
    write_data(transcribed_data, options)


def write_data(transcribed_data: list[tuple[float, float, str]], options: TranscriberOptions) -> None:
    # TODO Batch translate non-english texts? Requires a new column in the database
    # https://github.com/nidhaloff/deep-translator
    # translated = GoogleTranslator(detected_language, 'en').translate_batch(transcribed)
    txt_data: str = generate_txt_data(transcribed_data)
    srt_data: str = generate_srt_data(transcribed_data)

    zip_data: BytesIO = compress_files({
        "transcribed.txt": txt_data,
        "transcribed.srt": srt_data,
    })

    if options.output_file == "-":
        # pyre-fixme[6]
        sys.stdout.buffer.write(zip_data.getbuffer())
        return

    if options.output_file is None:
        with options.txt_file_path.open("w") as f:
            f.write(txt_data)
        with options.srt_file_path.open("w") as f:
            f.write(srt_data)
        with options.zip_file_path.open("wb") as f:
            f.write(zip_data.getbuffer())
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
            f.write(zip_data.getbuffer())
        return
    assert False, f"Shouldn't get here, output_file was {options.output_file}"


# TODO Burn subtitles into video, or add subtitles to video (selectable language)
parser = ArgumentParser()
parser.add_arguments(TranscriberOptions, dest="options")  # pyre-fixme[6]


def main():
    args = parser.parse_args()
    options: TranscriberOptions = args.options
    # logger.debug(f"Options: {options}")
    # Not needed?
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

poetry run python src/argparser.py --input_file "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3" --task Translate --model Large

poetry run python src/argparser.py --input_file "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3" --task Translate --language en --model Large --output_file - > result.zip

# TODO Add option to add subtitles to video (hardcoded or soft subtitles)
    """ # noqa: E501
    main()
