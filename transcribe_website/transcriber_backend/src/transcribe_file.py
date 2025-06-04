# https://github.com/m-bain/whisperX
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from loguru import logger
from whisperx.alignment import align, load_align_model
from whisperx.asr import load_model
from whisperx.audio import load_audio
from whisperx.types import AlignedTranscriptionResult, SingleAlignedSegment, SingleWordSegment

from hard_burn_subtitles import hard_burn_subtitles
from helper import recurse_path
from prisma import Prisma  # pyrefly: ignore
from srt_writer import get_srt_content

load_dotenv()

# from faster_whisper import utils
# See "faster_whisper/utils.py:_MODELS"
# https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/utils.py
type model_sizes = Literal[
    "tiny",
    "base",
    "small",
    "medium",
    "large",
    # turbo model works only well for transcribing (all languages)
    "turbo",
    # Only works for transcribing english
    "tiny.en",
    "base.en",
    "small.en",
    "medium.en",
    # https://huggingface.co/distil-whisper/distil-large-v2
    # Only works for transcribing english
    "distil-large-v2",
    "distil-large-v3",
    "distil-medium.en",
    "distil-small.en",
]
type language_codes = Literal["en", "fr", "de", "es", "it", "ja", "zh", "nl", "uk", "pt"]


def transcribe_file(
    file_path: Path,
    model_size: model_sizes,
    task: Literal["transcribe", "translate"] = "transcribe",
    language: language_codes | None = None,
) -> AlignedTranscriptionResult:
    # Models: https://github.com/openai/whisper#available-models-and-languages

    device = "cpu"
    batch_size = 8
    compute_type = "int8"

    # save model to local path (optional)
    model_dir = "whisper_models"

    # TODO Reply to issues:
    # https://github.com/m-bain/whisperX/issues/333
    # https://github.com/m-bain/whisperX/issues/466
    # Maybe using model that only supports english?

    model = load_model(model_size, device, compute_type=compute_type, download_root=model_dir)

    # pyrefly: ignore
    audio = load_audio(file_path)
    result = model.transcribe(audio, batch_size=batch_size, language=language, task=task)

    # delete model if low on GPU resources
    # import gc; gc.collect(); torch.cuda.empty_cache(); del model

    # Align whisper output
    model_a, metadata = load_align_model(language_code=result["language"], device=device)
    result2: AlignedTranscriptionResult = align(
        result["segments"],
        model_a,
        metadata,
        audio,
        device,
        # Does it increase accuracy if True?
        return_char_alignments=False,
    )

    # pyrefly: ignore
    result2["language"] = result["language"]
    return result2


def get_all_paths_already_in_db() -> set[str]:
    with Prisma() as db:
        result = db.word.find_many(distinct=["file_felative_path"])

    return {w.file_felative_path for w in result}


def save_result_to_db(
    input_file_path: Path,
    result: AlignedTranscriptionResult,
) -> None:
    input_file_str = input_file_path.as_posix()
    sentences_to_insert = []
    words_to_insert = []

    sentence_segment: SingleAlignedSegment
    for sentence_segment in result["segments"]:
        # Keys required in sentence_segment
        if not ({"text", "start", "end"} <= set(sentence_segment.keys())):
            continue
        start, end, text = sentence_segment["start"], sentence_segment["end"], sentence_segment["text"]
        sentences_to_insert.append(
            # pyrefly: ignore
            {
                "file_felative_path": input_file_str,
                "sentence_start_timestamp": start,
                "sentence_end_timestamp": end,
                "sentence_text": text,
            }
        )

    word_segment: SingleWordSegment
    for word_segment in result["word_segments"]:
        # Keys required in word_segment
        if not ({"word", "start", "end"} <= set(word_segment.keys())):
            continue
        start, end, word = word_segment["start"], word_segment["end"], word_segment["word"]
        words_to_insert.append(
            {
                "file_felative_path": input_file_str,
                "word_start_timestamp": start,
                "word_end_timestamp": end,
                "word_text": word,
            }
        )

    with Prisma() as db:
        # pyrefly: ignore
        db.word.create_many(data=words_to_insert)
        db.sentence.create_many(data=sentences_to_insert)


def mass_transcribe(
    input_folder_path: Path,
    model_size: model_sizes,
    language: language_codes | None = None,
) -> None:
    already_in_db = get_all_paths_already_in_db()
    for file_path in recurse_path(input_folder_path, depth=1):
        if file_path.as_posix() in already_in_db:
            continue
        logger.info(f"Started transcribing: {file_path.as_posix()}")
        result = transcribe_file(file_path, model_size=model_size, language=language)
        logger.info(f"Saving result to database: {file_path.as_posix()}")
        save_result_to_db(file_path, result)


if __name__ == "__main__":
    # Can be run with:
    # PYTHONPATH=$(pwd) uv run python src/transcribe_file.py

    # This example mass transcribes files and loads them into database for later use

    # pyrefly: ignore
    input_folder_path = Path(os.getenv("MASS_TRANSCRIBE_INPUT_DIRECTORY"))
    # mass_transcribe(input_folder_path, model_size="tiny", language="de")
    # mass_transcribe(input_folder_path, model_size="medium", language="de")

    paths = """
/my/absolute/path/to/file.mp4
"""
    paths_split = [Path(p.strip()) for p in paths.splitlines() if p.strip()]

    for input_file_path in paths_split:
        # Example of writing german subtitles
        subtitle_path = input_file_path.parent / f"{input_file_path.stem}_DE.srt"
        if not subtitle_path.is_file():
            logger.info(f"Started transcribing {input_file_path.name}")
            result = transcribe_file(input_file_path, model_size="turbo", language="de")
            subtitle_data = get_srt_content(result)
            subtitle_path.write_text(subtitle_data.getvalue().decode())
            logger.info(f"Done transcribing {input_file_path.name}")
        output_file_path = input_file_path.parent / f"{input_file_path.stem}_DE.mp4"
        hard_burn_subtitles(input_file_path, subtitle_path, output_file_path)

        # Example of writing english subtitles
        subtitle_path = input_file_path.parent / f"{input_file_path.stem}_EN.srt"
        if not subtitle_path.is_file():
            # "language" specifies the input language,
            # task "translate" translates to english (no other language possible as of yet)
            logger.info(f"Started translating {input_file_path.name}")
            result = transcribe_file(input_file_path, task="translate", model_size="large", language="de")
            subtitle_data = get_srt_content(result)
            subtitle_path.write_text(subtitle_data.getvalue().decode())
            logger.info(f"Done translating {input_file_path.name}")
        output_file_path = input_file_path.parent / f"{input_file_path.stem}_EN.mp4"
        hard_burn_subtitles(input_file_path, subtitle_path, output_file_path)
