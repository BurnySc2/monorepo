"""
Extract mp4 clips where someone in the video says a specific word from the list.
"""
from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from faster_whisper import WhisperModel

input_files = [
    Path("PATH_TO_VIDEO_FILE1"),
    Path("PATH_TO_VIDEO_FILE2"),
]

looking_for_lower_case_words = ["words", "to", "look", "for"]

out_path = Path("OUTPUT_FOLGER_PATH")

out_path.mkdir(parents=True, exist_ok=True)
log_file = out_path / "timestamps.txt"

# https://github.com/openai/whisper#available-models-and-languages
MODEL_SIZE = "medium"
model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8",
    download_root="./whisper_models",
)


def extract_with_ffmpeg(
    input_file_str: str,
    clip_out_path: Path,
    clip_start_str: str,
    clip_end_str: str,
) -> None:
    # Extract .mp4 clip
    cmd = [
        "ffmpeg",
        "-ss",
        f"{clip_start_str}",
        "-to",
        f"{clip_end_str}",
        "-i",
        input_file_str,
        "-c",
        "copy",
        "-loglevel",
        "error",
        "-stats",
        str(clip_out_path.resolve()),
    ]
    proc = subprocess.Popen(cmd)
    proc.communicate()


def extract(executor: ThreadPoolExecutor, input_file: Path) -> None:
    input_file_str = str(input_file.resolve())
    file_length = 0
    # https://superuser.com/questions/650291/how-to-get-video-duration-in-seconds
    # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
    # ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
    file_length = float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                input_file_str,
            ]
        ).decode()
    )

    # Extract .wav files in 10 minutes chunks, because whisper seems to lose accuracy if the video is too long.
    CHUNK_SIZE = 600  # 10 minutes chunk size
    buffer_size = 10  # 10 extra seconds
    for chunk in range(int(file_length) // CHUNK_SIZE):
        chunk_out_path = out_path / f"{input_file.stem}_{chunk:02d}.wav"
        chunk_out_path_str = str(chunk_out_path.resolve())
        if not chunk_out_path.is_file():
            # Extract .wav chunk
            subprocess.call(
                [
                    "ffmpeg",
                    "-ss",
                    f"{chunk * CHUNK_SIZE}",
                    "-to",
                    f"{(chunk + 1) * CHUNK_SIZE + buffer_size}",
                    "-i",
                    input_file_str,
                    "-loglevel",
                    "error",
                    "-stats",
                    chunk_out_path_str,
                ]
            )

        # Transcribe chunk
        segments, _info = model.transcribe(
            chunk_out_path_str,
            word_timestamps=True,
            language="de",
        )

        for segment in segments:
            for word in segment.words:
                my_word = word.word.strip().strip(",.!?").lower()
                if my_word not in looking_for_lower_case_words:
                    continue

                buffer = 5
                chunk_offset = chunk * CHUNK_SIZE
                clip_start = max(0, word.start - buffer) + chunk_offset
                clip_end = word.end + buffer + chunk_offset

                clip_start_str = f"{clip_start:.3f}"
                clip_end_str = f"{clip_end:.3f}"

                clip_out_path = out_path / f"{input_file.stem} {clip_start_str} {clip_end_str}.mp4"
                with log_file.open("a") as f:
                    f.write(
                        f"{input_file_str} {clip_start_str} {clip_end_str} {clip_out_path}\n",
                    )
                # Extract clip in new thread
                executor.submit(
                    extract_with_ffmpeg,
                    input_file_str,
                    clip_out_path,
                    clip_start_str,
                    clip_end_str,
                )


if __name__ == "__main__":
    with ThreadPoolExecutor() as exec:
        for my_file in input_files:
            extract(exec, my_file)
