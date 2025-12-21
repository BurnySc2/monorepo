# https://github.com/m-bain/whisperX
import os
from pathlib import Path
from typing import Literal

import torch
from dotenv import load_dotenv
from loguru import logger
from whisperx.alignment import align, load_align_model
from whisperx.asr import load_model
from whisperx.audio import load_audio
from whisperx.schema import AlignedTranscriptionResult

from hard_burn_subtitles import hard_burn_subtitles
from srt_writer import get_srt_content

load_dotenv()


# --- Start of temp fix
# https://github.com/m-bain/whisperX/issues/1304#issuecomment-3591660486
_original_torch_load = torch.load


def _trusted_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)


torch.load = _trusted_load
# --- End of temp fix

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
    compute_type = "float32"
    # Lower accuracy but lower memory:
    # compute_type = "int8"

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
            # Subtitle from a german video generating english subtitles
            # result = transcribe_file(input_file_path, task="translate", model_size="large", language="de")
            # Subtitle from a english video generating english subtitles
            result = transcribe_file(input_file_path, task="transcribe", model_size="turbo", language="en")
            subtitle_data = get_srt_content(result)
            subtitle_path.write_text(subtitle_data.getvalue().decode())
            logger.info(f"Done translating {input_file_path.name}")
        output_file_path = input_file_path.parent / f"{input_file_path.stem}_EN.mp4"
        hard_burn_subtitles(input_file_path, subtitle_path, output_file_path)
