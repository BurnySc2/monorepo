"""
Extract mp4 clips where someone in the video says a specific word from the list.
"""
from __future__ import annotations

import subprocess
from collections import Counter, OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable

import dataset  # pyre-fixme[21]
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
db_abs_path = str(db_path.resolve())

# Create table
# pyre-fixme[11]
db: dataset.Database = dataset.connect(f"sqlite:///{db_abs_path}")
# pyre-fixme[11]
words_table: dataset.Table = db["words"]
sentences_table: dataset.Table = db["sentences"]

"""
Schema 'words' table
    video_relative_path TEXT
    word_start_timestamp REAL
    word_end_timestamp REAL
    word TEXT
Schema 'sentences' table
    video_relative_path TEXT
    sentence_start_timestamp REAL
    sentence_end_timestamp REAL
    sentence TEXT
Schema 'done_extracting' table
    video_relative_path TEXT
"""

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

    If depth == 0: only return file path
    If depth == 1: if given a folder, return containing file paths
    Depth > 1 allow recursively to go through folders up to a given depth
    """
    if path.is_file():
        yield path
    elif path.is_dir() and depth > 0:
        for subfile_path in sorted(path.iterdir()):
            yield from recurse_path(subfile_path, depth=depth - 1)


def extract_with_ffmpeg(
    input_file_str: str,  # The input file path from which to extract a clip.
    clip_out_path: Path,  # The output file path where the extracted clip will be saved.
    clip_start_str: str,  # The start time of the clip in seconds.
    clip_end_str: str,  # The end time of the clip in seconds.
) -> None:
    """
    Extract a clip from the input video file using ffmpeg.
    """
    # Extract .mp4 clip
    clip_out_path_str = str(clip_out_path.resolve())
    subprocess.check_call(
        f'ffmpeg -ss {clip_start_str} -to {clip_end_str} -i "{input_file_str}" -c copy -loglevel error -stats "{clip_out_path_str}"',  # noqa: E501
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def extract_info(_executor: ThreadPoolExecutor, input_file: Path) -> None:
    """
    Extract words and timestamps from a given video file.

    This function extracts words and timestamps from a given video file. It first checks if the video file has already been processed. If not, it extracts .wav files in 5-minute chunks and transcribes them using the Whisper model. The extracted words and sentences are then stored in the respective database tables.
    """  # noqa: E501
    global words_table, sentences_table
    input_file_str = str(input_file.resolve())
    done_extracting_table: dataset.Table = db["done_extracting"]
    already_done: OrderedDict | None = done_extracting_table.find_one(video_relative_path=input_file_str)
    if already_done:
        return
    video_length = 0
    # https://superuser.com/questions/650291/how-to-get-video-duration-in-seconds
    # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
    # ffprobe -v error -select_streams v:0 -show_entries stream=duration
    # -of default=noprint_wrappers=1:nokey=1 input.mp4
    video_length = float(
        subprocess.check_output(
            f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{input_file_str}"',
            shell=True,
        ).decode()
    )
    logger.info(
        f"Extracting words and timestamps from {input_file.name} with a total length of {int(video_length) // 60} minutes"  # noqa: E501
    )

    # Continue where we left off
    pick_up_row: OrderedDict = (
        words_table.find_one(video_relative_path=input_file_str, order_by=["-word_end_timestamp"]) or {}
    )
    pick_up_time: float = pick_up_row.get("word_end_timestamp", 0)

    # Extract .wav files in 5 minutes chunks, because whisper seems to lose accuracy if the video is too long.
    chunk_start = pick_up_time - pick_up_time % CHUNK_SIZE

    # Delete entries to prevent duplicates and then parse from this chunk time again
    words_table.delete(video_relative_path=input_file_str, word_start_timestamp={">": chunk_start})
    sentences_table.delete(video_relative_path=input_file_str, word_start_timestamp={">": chunk_start})

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
            subprocess.check_call(
                f"ffmpeg -ss {chunk} -to {chunk + CHUNK_SIZE + BUFFER_SIZE} -i {input_file_str} -loglevel error -stats {chunk_wav_path_str}",  # noqa: E501
                shell=True,
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
                words_table.insert(
                    {
                        "video_relative_path": input_file_str,
                        "word_start_timestamp": word.start + chunk,
                        "word_end_timestamp": word.end + chunk,
                        "word": word.word.strip().strip(SYMBOLS).lower(),
                    }
                )
                if any(word.word.endswith(x) for x in SENTENCE_END_SYMBOLS):
                    sentences_table.insert(
                        {
                            "video_relative_path": input_file_str,
                            "sentence_start_timestamp": sentence[0].start + chunk,
                            "sentence_end_timestamp": sentence[-1].end + chunk,
                            "sentence": "".join([w.word for w in sentence]),
                        }
                    )
                    sentence = []
        # Delete .wav file after processing
        chunk_out_path.unlink()
    done_extracting_table.insert(
        {
            "video_relative_path": input_file_str,
        }
    )
    logger.info(f"Done extracting from {input_file.name}")


def print_words_overview() -> None:
    """
    Prints a summary of the words found in the videos.

    This function prints a summary of the words found in the videos. It retrieves the words from the database and counts their occurrences in each video. The function then prints the top 10 most common words for each video.
    """  # noqa: E501
    global words_table
    results = words_table.find(video_relative_path={"like": r"%part_of_video%"}, order_by=["video_relative_path"])
    counters: dict[str, Counter] = {}
    for row in results:
        video_relative_path, word = row["video_relative_path"], row["word"]
        if video_relative_path not in counters:
            counters[video_relative_path] = Counter()
        counters[video_relative_path][word] += 1
    counter: Counter
    for video_relative_path, counter in counters.items():
        logger.info(f"{video_relative_path} has words:")
        print(counter.most_common(10))
    # pyre-fixme[6, 9]
    total_counter: Counter = sum(counters.values(), start=Counter())
    # Write total word count to file
    words_path = Path(__file__).parent / "words.txt"
    with words_path.open("w") as f:
        for word, count in total_counter.most_common():
            f.write(f"{word}: {count}\n")


def extract_matched_words(
    executor: ThreadPoolExecutor,
    input_file: Path,
    words: list[str],
) -> None:
    """
    Extracts clips from the input video file for the given list of words.

    This function extracts clips from the input video file for the given list of words. It retrieves the words from the database and finds the corresponding timestamps. For each word, it extracts a clip starting 3 seconds before the word and ending 3 seconds after the word. The extracted clips are saved in the output directory with a filename containing the input file name, start and end timestamps, and the word.
    """  # noqa: E501
    global words_table
    assert len(words) >= 1
    input_file_str = str(input_file.resolve())
    results = words_table.find(video_relative_path=input_file_str, word=words, order_by=["word_start_timestamp"])
    for row in results:
        start_time, end_time, word = row["word_start_timestamp"], row["word_end_timestamp"], row["word"]
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
