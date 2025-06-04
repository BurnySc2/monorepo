"""
Extract mp4 clips where someone in the video says a specific word from the list.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# pyrefly: ignore
from prisma import Prisma

load_dotenv()

# pyre-fixme[16]
looking_for_lower_case_words: list[str] = os.getenv("WORDS_EXTRACTOR_WORDS").split(";")

# pyre-fixme[6]
out_path = Path(os.getenv("WORDS_EXTRACTOR_OUTPUT_DIRECTORY"))
out_path.mkdir(parents=True, exist_ok=True)

# pyrefly: ignore
CLIP_BUFFER = float(os.getenv("WORDS_EXTRACTOR_CONTEXT_DURATION_SECONDS"))


def extract_with_ffmpeg(
    input_file_path: Path,  # The input file path from which to extract a clip.
    clip_out_path: Path,  # The output file path where the extracted clip will be saved.
    clip_start_str: str,  # The start time of the clip in seconds.
    clip_end_str: str,  # The end time of the clip in seconds.
) -> None:
    logger.info(f"Extracting: {clip_out_path.as_posix()}")
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir_path = Path(temp_dir_str)
        temp_path = temp_dir_path / clip_out_path.name
        subprocess.check_call(
            [
                "ffmpeg",
                "-ss",
                clip_start_str,
                "-to",
                clip_end_str,
                "-i",
                input_file_path.as_posix(),
                "-c",
                "copy",
                "-loglevel",
                "error",
                "-stats",
                temp_path.as_posix(),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        shutil.move(temp_path, clip_out_path)


def print_words_overview() -> None:
    """
    Prints a summary of the words found in the videos.

    This function prints a summary of the words found in the videos. It retrieves the words from the database and counts their occurrences in each video. The function then prints the top 10 most common words for each video.
    """  # noqa: E501
    part_of_path = os.getenv("WORDS_EXTRACTOR_PART_OF_PATH")
    with Prisma() as db:
        results = db.query_raw(
            """
SELECT LOWER(word_text) AS word_text, COUNT(*) AS count FROM word
WHERE
    file_felative_path LIKE '%' || ? || '%'
GROUP BY LOWER(word_text)
ORDER BY count DESC, word_text ASC;
""",
            part_of_path,
        )
    counter = Counter({i["word_text"]: i["count"] for i in results})
    # Write total word count to file
    words_path = Path(__file__).parent / "words.txt"
    words_path.write_text("".join(f"{word}: {count}\n" for word, count in counter.most_common()))


def extract_matched_words(
    exec: ThreadPoolExecutor,
    part_of_path: str,
    words_list: list[str],
) -> None:
    """
    Extracts clips from the input video file for the given list of words.

    This function extracts clips from the input video file for the given list of words. It retrieves the words from the database and finds the corresponding timestamps. For each word, it extracts a clip starting 3 seconds before the word and ending 3 seconds after the word. The extracted clips are saved in the output directory with a filename containing the input file name, start and end timestamps, and the word.
    """  # noqa: E501
    # pyrefly: ignore
    output_folder_path = Path(os.getenv("WORDS_EXTRACTOR_OUTPUT_DIRECTORY"))
    output_folder_path.mkdir(parents=True, exist_ok=True)
    with Prisma() as db:
        for word in words_list:
            results = db.word.find_many(
                # pyrefly: ignore
                where={
                    "file_felative_path": {
                        "contains": part_of_path,
                    },
                    "word_text": {"contains": word},
                }
            )
            word_subdir_path = output_folder_path / word
            if len(results) > 0:
                word_subdir_path.mkdir(parents=True, exist_ok=True)
            for result in results:
                input_file_path = Path(result.file_felative_path)
                clip_start = max(0.0, result.word_start_timestamp - CLIP_BUFFER)
                clip_end = result.word_end_timestamp + CLIP_BUFFER

                clip_start_str = f"{clip_start:.3f}"
                clip_end_str = f"{clip_end:.3f}"

                clip_out_path = (
                    word_subdir_path / f"{input_file_path.stem} {clip_start_str} {clip_end_str} - {word}.mp4"
                )
                if clip_out_path.is_file():
                    continue
                # Extract clip in new thread
                exec.submit(
                    extract_with_ffmpeg,
                    input_file_path,
                    clip_out_path,
                    clip_start_str,
                    clip_end_str,
                )


if __name__ == "__main__":
    print_words_overview()

    # with ThreadPoolExecutor(max_workers=8) as exec:
    #     extract_matched_words(
    #         exec,
    #         os.getenv("WORDS_EXTRACTOR_PART_OF_PATH"),
    #         words_list=sorted(os.getenv("WORDS_EXTRACTOR_WORDS").split(";")),
    #     )
