import gc
import os
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from moviepy.editor import CompositeVideoClip, TextClip, VideoFileClip

load_dotenv()


def get_same_disk_temp_folder(dir_path: Path) -> Path:
    info_old = os.statvfs(dir_path)
    while True:
        dir_path_old = dir_path
        dir_path = dir_path.parent
        info = os.statvfs(dir_path)
        if info.f_blocks != info_old.f_blocks or dir_path == dir_path_old:
            return dir_path_old
        info_old = info


def add_text_to_clip(
    clip_input_path: Path,
    clip_output_path: Path,
    text_to_add: int,
    temp_folder: Path,
) -> None:
    logger.info(f"Processing: {clip_input_path.as_posix()}")
    clip: VideoFileClip = VideoFileClip(clip_input_path.as_posix())

    # Display text counter
    text: TextClip = TextClip(text_to_add, fontsize=70, color="white")
    text = text.set_position((360, clip.size[1] - text.size[1] - 10))
    text = text.set_start(clip.start)
    text = text.set_duration(clip.duration)

    clip = CompositeVideoClip([clip, text])

    with tempfile.TemporaryDirectory(dir=temp_folder.as_posix()) as temp_dir_str:
        temp_dir_path = Path(temp_dir_str)
        temp_path = temp_dir_path / clip_output_path.name
        clip.write_videofile(
            temp_path.as_posix(),
            codec="libx264",
            preset="faster",
            ffmpeg_params=["-crf", "20", "-c:a", "copy"],
        )
        shutil.move(temp_path, clip_output_path)
    # Force release memory
    text.close()
    clip.close()
    gc.collect()


def main():
    input_folder_path = Path(os.getenv("ADD_TEXT_INPUT_FOLDER"))
    output_folder_path = Path(os.getenv("ADD_TEXT_OUTPUT_FOLDER"))
    initial_text = os.getenv("ADD_TEXT_TEXT_DESCRIPTION")
    temp_folder = get_same_disk_temp_folder(input_folder_path) / "temp"
    temp_folder.mkdir(parents=True, exist_ok=True)

    logger.info(f"{input_folder_path=}")
    logger.info(f"{output_folder_path=}")
    logger.info(f"{initial_text=}")

    assert input_folder_path.is_dir()
    output_folder_path.mkdir(parents=True, exist_ok=True)

    index = 1
    for input_file_path in sorted(input_folder_path.iterdir()):
        if not input_file_path.is_file():
            continue
        clip_output_path = output_folder_path / f"{index:04d}.mp4"
        if clip_output_path.is_file():
            index += 1
            continue
        text_to_add = f"{initial_text}\n{index}"
        try:
            add_text_to_clip(
                input_file_path,
                clip_output_path,
                text_to_add,
                temp_folder,
            )
            index += 1
        except KeyError:
            # May encounter keyerror reading fps because file is too short
            # self.fps = infos['video_fps']
            continue


if __name__ == "__main__":
    main()
