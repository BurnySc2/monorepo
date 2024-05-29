"""
Input:
Folder with video files
A "clip.txt" file containing start and end timestamp

Iterates over the timestamps from clip.txt and videos in folder
Cuts video and stores it as a separate file
TODO Then finaally all cut videos are merged together with ffmpeg
"""

import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from moviepy.editor import CompositeVideoClip, TextClip, VideoFileClip  # pyre-fixme[21]

load_dotenv()


# The folders containing the video files
# pyre-fixme[16]
videos_folder_path = [Path(p) for p in os.getenv("VIDEO_FOLDER_PATHS").split(":")]
# Where to store the cut files to
# pyre-fixme[6]
out_folder_path = Path(os.getenv("VIDEO_OUT_PATHS"))
# Text to be added to video
text_description = os.getenv("VIDEO_TEXT_DESCRPITION")


# Name of file containing the start- and end-timestamps
timestamp_file_name = "clip.txt"


CLIP_CONTEXT = 0.0


out_folder_path.mkdir(parents=True, exist_ok=True)


def get_timestamps_from_file(my_file: Path) -> list[tuple[float, float]]:
    # Example entry:
    # 1.56-2.31
    timestamps: list[tuple[float, float]] = []
    for line in my_file.read_text().split("\n"):
        if line.startswith("#"):
            continue
        if "-" not in line:
            continue
        start, end = line.strip().split("-")
        start_sec, start_ms = start.split(".")
        end_sec, end_ms = end.split(".")
        timestamps.append(
            (
                float(start_sec) + float(start_ms) / 60,
                float(end_sec) + float(end_ms) / 60,
            )
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
    # Add context, half transition duration
    timestamp_start = timestamp_start - CLIP_CONTEXT
    timestamp_end = timestamp_end + CLIP_CONTEXT
    # pyre-fixme[11]
    clip: VideoFileClip = VideoFileClip(str(video_path.absolute())).subclip(timestamp_start, timestamp_end)

    # Display text counter
    # pyre-fixme[11]
    text: TextClip = TextClip(f"{text_description}{word_count}", fontsize=70, color="white")
    text = text.set_position((360, clip.size[1] - text.size[1] - 10))
    text = text.set_start(clip.start)
    text = text.set_duration(clip.duration)

    clip = CompositeVideoClip([clip, text])
    clip_out_path = out_folder_path / f"{clip_index:04d}.mp4"

    # Write result
    # https://moviepy.readthedocs.io/en/latest/ref/videotools.html?highlight=write_videofile#moviepy.video.tools.credits.CreditsClip.write_videofile
    print(video_path.name, timestamp_start, timestamp_end)
    clip.write_videofile(
        # transitioned_clips.write_videofile(
        str(clip_out_path.absolute()),
        codec="libx264",
        # codec="libx265",
        preset="faster",
        ffmpeg_params=["-crf", "20", "-c:a", "copy"],
    )


clip_number = 0
word_count = 0
with ProcessPoolExecutor(max_workers=4) as executor:
    for video_folder_path in videos_folder_path:
        video_file_paths = list(recurse_path(video_folder_path, depth=1))

        timestamps_file_path = video_folder_path / timestamp_file_name
        if not timestamps_file_path.is_file():
            continue
        # TODO Only convert if target file does not exist?!
        timestamps = get_timestamps_from_file(timestamps_file_path)
        for index, (video_path, (timestamp_start, timestamp_end)) in enumerate(zip(video_file_paths, timestamps)):
            clip_number += 1
            if timestamp_start == timestamp_end:
                continue
            word_count += 1
            # Add context, half transition duration
            timestamp_start = timestamp_start - CLIP_CONTEXT
            timestamp_end = timestamp_end + CLIP_CONTEXT
            executor.submit(
                convert_clip,
                video_path,
                out_folder_path,
                timestamp_start,
                timestamp_end,
                clip_number,
                word_count,
            )
    # TODO from all extracted clips in out_folder_path, create one concatenated video
