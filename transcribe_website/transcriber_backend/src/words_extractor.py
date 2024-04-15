"""
Extract mp4 clips where someone in the video says a specific word from the list.
"""
from __future__ import annotations

import sqlite3
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable

from faster_whisper import WhisperModel  # pyre-fixme[21]
from loguru import logger
from tqdm import tqdm

input_directory = Path("my_input_files")

looking_for_lower_case_words = ["words", "to", "look", "for"]

out_path = Path("OUTPUT_FOLGER_PATH")

out_path.mkdir(parents=True, exist_ok=True)

SYMBOLS = "!?.,"
SENTENCE_END_SYMBOLS = "!?."
CHUNK_SIZE = 300  # 5 minutes chunk size
BUFFER_SIZE = 10  # 10 extra seconds
CLIP_BUFFER = 3

db_path = Path(__file__).parent / "word_extract.db"
conn = sqlite3.connect(str(db_path.resolve()))

# Create table
conn.execute(
    """
CREATE TABLE IF NOT EXISTS words (
    video_relative_path TEXT,
    word_start_timestamp REAL,
    word_end_timestamp REAL,
    word TEXT
);
    """
)
conn.execute(
    """
CREATE TABLE IF NOT EXISTS sentences (
    video_relative_path TEXT,
    sentence_start_timestamp REAL,
    sentence_end_timestamp REAL,
    sentence TEXT
);
    """
)
conn.execute(
    """
CREATE TABLE IF NOT EXISTS done_extracting (
    video_relative_path TEXT
);
    """
)
conn.commit()

# https://github.com/openai/whisper#available-models-and-languages
MODEL_SIZE = "small"
model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8",
    download_root=str((Path(__file__).parent.parent / "whisper_models").resolve()),
)


def recurse_path(path: Path, depth: int = 0) -> Iterable[Path]:
    """
    Go through a given path recursively and return file paths

    If depth == 0: only allow file path
    If depth == 1: if given a folder, return containing file paths
    Depth > 1 allow recursively to go through folders up to a given depth
    """
    if path.is_file():
        yield path
    elif path.is_dir() and depth > 0:
        for subfile_path in sorted(path.iterdir()):
            yield from recurse_path(subfile_path, depth=depth - 1)


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


def extract_info(executor: ThreadPoolExecutor, input_file: Path) -> None:
    input_file_str = str(input_file.resolve())
    already_done = conn.execute(
        """
SELECT 1 FROM done_extracting
WHERE video_relative_path = ?
        """,
        [input_file_str],
    ).fetchone()
    if already_done:
        return
    video_length = 0
    # https://superuser.com/questions/650291/how-to-get-video-duration-in-seconds
    # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
    # ffprobe -v error -select_streams v:0 -show_entries stream=duration
    # -of default=noprint_wrappers=1:nokey=1 input.mp4
    video_length = float(
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
    logger.info(
        f"Extracting words and timestamps from {input_file.name} with a total length of {int(video_length) // 60} minutes"  # noqa: E501
    )

    # Continue where we left off
    pick_up_time: float = (
        conn.execute(
            """
SELECT max(word_end_timestamp) FROM words
WHERE video_relative_path = ?
""",
            [input_file_str],
        ).fetchone()[0]
        or 0
    )

    # Extract .wav files in 5 minutes chunks, because whisper seems to lose accuracy if the video is too long.
    chunk_start = pick_up_time - pick_up_time % CHUNK_SIZE
    conn.execute(
        """
DELETE FROM words
WHERE video_relative_path = ? AND ? < word_start_timestamp
""",
        [input_file_str, chunk_start],
    )
    conn.execute(
        """
DELETE FROM sentences
WHERE video_relative_path = ? AND ? < sentence_start_timestamp
""",
        [input_file_str, chunk_start],
    )
    conn.commit()

    total_chunks_count = int(video_length - chunk_start) // CHUNK_SIZE + 1
    for chunk in tqdm(
        range(
            int(chunk_start),
            int(video_length),
            CHUNK_SIZE,
        ),
        total=total_chunks_count,
    ):
        chunk_out_path = out_path / f"{input_file.stem}_{chunk:02d}.wav"
        chunk_wav_path_str = str(chunk_out_path.resolve())
        if not chunk_out_path.is_file():
            # Extract .wav chunk
            subprocess.call(
                [
                    "ffmpeg",
                    "-ss",
                    f"{chunk}",
                    "-to",
                    f"{chunk + CHUNK_SIZE + BUFFER_SIZE}",
                    "-i",
                    input_file_str,
                    "-loglevel",
                    "error",
                    "-stats",
                    chunk_wav_path_str,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Transcribe chunk
        segments, _info = model.transcribe(
            chunk_wav_path_str,
            word_timestamps=True,
            language="de",
            vad_filter=True,
        )

        sentence = []
        for segment in segments:
            for word in segment.words:
                sentence.append(word)
                # if not any(word.word.endswith(x) for x in ascii_letters + "."):
                #     logger.info(f"Word not ending with End-Symbol: {word.word}")

                conn.execute(
                    """
INSERT INTO words
(video_relative_path, word_start_timestamp, word_end_timestamp, word)
VALUES (?, ?, ?, ?);
                    """,
                    [
                        input_file_str,
                        word.start + chunk,
                        word.end + chunk,
                        word.word.strip().strip(SYMBOLS).lower(),
                    ],
                )

                if any(word.word.endswith(x) for x in SENTENCE_END_SYMBOLS):
                    conn.execute(
                        """
INSERT INTO sentences
(video_relative_path, sentence_start_timestamp, sentence_end_timestamp, sentence)
VALUES (?, ?, ?, ?);
                        """,
                        [
                            input_file_str,
                            sentence[0].start + chunk,
                            sentence[-1].end + chunk,
                            "".join([w.word for w in sentence]),
                        ],
                    )
                    sentence = []
            conn.commit()
        # Delete .wav file after processing
        chunk_out_path.unlink()
    conn.execute(
        """
INSERT INTO done_extracting
(video_relative_path) VALUES (?)
        """,
        [input_file_str],
    )
    conn.commit()
    logger.info(f"Done extracting from {input_file.name}")


def print_words_overview() -> None:
    results = conn.execute(
        """
SELECT video_relative_path, word FROM words
WHERE video_relative_path LIKE ?
ORDER BY video_relative_path
        """,
        [r"%part_of_video%"],
    ).fetchall()
    counters: dict[str, Counter] = {}
    for video_relative_path, word in results:
        if video_relative_path not in counters:
            counters[video_relative_path] = Counter()
        counters[video_relative_path][word] += 1
    counter: Counter
    for video_relative_path, counter in counters.items():
        logger.info(f"{video_relative_path} has words:")
        print(counter.most_common())
    # pyre-fixme[6, 9]
    total_counter: Counter = sum(counters.values(), start=Counter())
    # Write total word count to file
    with Path("words.txt").open("w") as f:
        for word, count in total_counter.most_common():
            f.write(f"{word}: {count}\n")


def extract_matched_words(
    executor: ThreadPoolExecutor,
    input_file: Path,
    words: list[str],
) -> None:
    assert len(words) >= 1
    input_file_str = str(input_file.resolve())
    placeholder_list = ", ".join("?" for _ in words)
    results = conn.execute(
        f"""
SELECT word_start_timestamp, word_end_timestamp, word FROM words
WHERE video_relative_path = ? AND word IN ({placeholder_list});
        """,
        [input_file_str, *words],
    )

    for start_time, end_time, word in results:
        clip_start = max(0, start_time - CLIP_BUFFER)
        clip_end = end_time + CLIP_BUFFER

        clip_start_str = f"{clip_start:.3f}"
        clip_end_str = f"{clip_end:.3f}"

        clip_out_path = out_path / f"{input_file.stem} {clip_start_str} {clip_end_str} - {word}.mp4"
        if clip_out_path.is_file():
            continue
        # Extract clip in new thread
        executor.submit(
            extract_with_ffmpeg,
            input_file_str,
            clip_out_path,
            clip_start_str,
            clip_end_str,
        )


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as exec:
        for my_file in recurse_path(input_directory, depth=2):
            if my_file.suffix != (".mp4"):
                continue
            extract_info(exec, my_file)
            extract_matched_words(
                exec,
                my_file,
                looking_for_lower_case_words,
            )
    print_words_overview()
