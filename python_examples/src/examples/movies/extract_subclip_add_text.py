"""
Input:
Folder with video files
A "clip.txt" file containing start and end timestamp

Iterates over the timestamps from clip.txt and videos in folder
Cuts video and stores it as a separate file
"""

import gc
import os
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from moviepy.editor import CompositeVideoClip, TextClip, VideoFileClip

load_dotenv()


# The folders containing the video files
videos_folder_path = [Path(p) for p in os.getenv("VIDEO_FOLDER_PATHS").split(";")]
# Where to store the cut files to
out_folder_path = Path(os.getenv("VIDEO_OUT_PATHS"))
# Text to be added to video
TEXT_DESCRIPTION: str | None = os.getenv("VIDEO_TEXT_DESCRPITION")
CLIP_CONTEXT = float(os.getenv("VIDEO_CONTEXT"))

# Name of file containing the start- and end-timestamps
timestamp_file_name = "clip.txt"
out_folder_path.mkdir(parents=True, exist_ok=True)


def get_timestamps_from_file(my_file: Path) -> list[tuple[float, float]]:
    # Example entry:
    # 51-185
    timestamps: list[tuple[float, float]] = []
    for line in my_file.read_text().split("\n"):
        if line.startswith("#"):
            continue
        if "-" not in line:
            continue
        start, end = line.strip().split("-")
        if start == end:
            timestamps.append((0, 0))
            continue
        # Extract if time in frames are given
        timestamps.append(
            (
                # Start and end is listed in frames but we need seconds
                float(start) / 60,
                float(end) / 60 + 1 / 60,
            ),
        )

    return timestamps


def recurse_path(path: Path, depth: int = 0) -> Iterable[Path]:
    if path.is_file() and path.suffix in [".mp4", ".mkv", ".webm"]:
        yield path
    elif path.is_dir() and depth > 0:
        for subfile_path in sorted(path.iterdir()):
            yield from recurse_path(subfile_path, depth=depth - 1)


def convert_clip(
    video_path: Path,
    out_folder_path: Path,
    timestamp_start: float,
    timestamp_end: float,
    clip_index: int,
    word_count: int,
) -> None:
    global TEXT_DESCRIPTION, CLIP_CONTEXT
    clip_out_path = out_folder_path / f"{clip_index:04d}.mp4"
    if clip_out_path.is_file():
        return

    # Add context, half transition duration
    timestamp_start = timestamp_start - CLIP_CONTEXT
    timestamp_end = timestamp_end + CLIP_CONTEXT
    clip: VideoFileClip = VideoFileClip(str(video_path.absolute())).subclip(timestamp_start, timestamp_end)

    # Display text counter
    text: TextClip | None = None
    if TEXT_DESCRIPTION is not None:
        # If text given: add count to overlay
        text = TextClip(f"{TEXT_DESCRIPTION}{word_count}", fontsize=70, color="white")
        text = text.set_position((360, clip.size[1] - text.size[1] - 10))
        text = text.set_start(clip.start)
        text = text.set_duration(clip.duration)

        clip = CompositeVideoClip([clip, text])

    # Write result
    # https://moviepy.readthedocs.io/en/latest/ref/videotools.html?highlight=write_videofile#moviepy.video.tools.credits.CreditsClip.write_videofile
    logger.info(video_path.name, timestamp_start, timestamp_end)
    clip.write_videofile(
        clip_out_path.as_posix(),
        codec="libx264",
        preset="faster",
        ffmpeg_params=["-crf", "20", "-c:a", "copy"],
    )
    # Force release memory
    if text is not None:
        text.close()
    clip.close()
    gc.collect()


clip_number = int(os.getenv("CLIP_NUMBER_START"))
word_count = int(os.getenv("WORD_NUMBER_START"))
with ThreadPoolExecutor(max_workers=4) as executor:
    for video_folder_path in videos_folder_path:
        video_file_paths = list(recurse_path(video_folder_path, depth=1))

        timestamps_file_path = video_folder_path / timestamp_file_name
        if not timestamps_file_path.is_file():
            continue

        timestamps = get_timestamps_from_file(timestamps_file_path)
        for video_path, (timestamp_start, timestamp_end) in zip(video_file_paths, timestamps):
            clip_number += 1
            if timestamp_start == timestamp_end:
                continue
            # Add context, half transition duration
            timestamp_start = timestamp_start - CLIP_CONTEXT
            timestamp_end = timestamp_end + CLIP_CONTEXT
            executor.submit(
                convert_clip,
                video_path,
                out_folder_path,
                timestamp_start,
                timestamp_end,
                clip_number - 1,
                word_count,
            )
            word_count += 1
