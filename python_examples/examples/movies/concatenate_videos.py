"""
From multiple input folders, merge all .mp4 files to one using ffmpeg.
"""

import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


INPUT_FOLDERS: list[str] = os.getenv("CONCATENATE_FOLDERS").split(";")
for folder in INPUT_FOLDERS:
    assert Path(folder).is_dir(), folder
OUTPUT_FILE = Path(os.getenv("CONCATENATE_OUTPUT_FILE"))
OUTPUT_FILE.parent.mkdir(exist_ok=True, parents=True)


def main():
    # Collect all .mp4 files
    input_files: list[Path] = []
    for folder in INPUT_FOLDERS:
        folder_path = Path(folder)
        for file_path in sorted(folder_path.iterdir()):
            if file_path.suffix not in {".mp4"}:
                continue
            # Exclude 'output.mp4'
            if file_path.name in {"output.mp4"}:
                continue
            input_files.append(file_path)

    # Write file list
    """Pattern:
    file '<absolute_filepath>'
    """
    filelist_files = [f"file '{file.as_posix()}'" for file in input_files]
    filelist_string = "\n".join(filelist_files) + "\n"

    filelist_path = OUTPUT_FILE.parent / "filelist.txt"
    filelist_path.write_text(filelist_string)

    # Issue ffmpeg to merge using file list
    command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        f"{filelist_path.as_posix()}",
        "-c:v",
        "libx264",
        "-crf",
        "20",
        "-acodec",
        "aac",
        f"{OUTPUT_FILE.as_posix()}",
    ]
    process = subprocess.Popen(command)
    process.communicate()


if __name__ == "__main__":
    main()
