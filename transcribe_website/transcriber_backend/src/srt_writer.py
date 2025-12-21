"""
Credits: https://github.com/m-bain/whisperX/issues/883
"""

import io
import re
from pathlib import Path

from deepmultilingualpunctuation import PunctuationModel
from whisperx.schema import AlignedTranscriptionResult

# Initialize PunctuationModel
punct_model = PunctuationModel()


def format_timestamp(seconds: float) -> str:
    if seconds is None:
        return "00:00:00,000"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace(".", ",")


def split_subtitle(text, max_chars=42):
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_chars and current_line:
            # pyrefly: ignore
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1

    if current_line:
        # pyrefly: ignore
        lines.append(" ".join(current_line))

    return "\n".join(lines)


def extract_words(text):
    return set(re.findall(r"\b[\w\']+\b", text.lower()))


def split_at_sentence_end(text, word_data):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    result = []
    current_word_index = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            sentence_word_count = len(sentence.split())
            sentence_word_data = word_data[current_word_index : current_word_index + sentence_word_count]
            if sentence_word_data:
                start_time = next((word["start"] for word in sentence_word_data if "start" in word), None)
                end_time = next((word["end"] for word in reversed(sentence_word_data) if "end" in word), None)
                if start_time is not None and end_time is not None:
                    result.append({"text": sentence, "start": start_time, "end": end_time})
                else:
                    # If start or end time is missing, use the previous valid timestamp
                    if result:
                        prev_end = result[-1]["end"]
                        result.append(
                            {
                                "text": sentence,
                                "start": prev_end,
                                "end": prev_end + 1,  # Add 1 second as a placeholder duration
                            }
                        )
                    else:
                        # If it's the first sentence and times are missing, use 0 as start time
                        result.append(
                            {
                                "text": sentence,
                                "start": 0,
                                "end": 1,  # Add 1 second as a placeholder duration
                            }
                        )
            current_word_index += sentence_word_count
    return result


def merge_short_cues(cues, min_duration=3):
    merged_cues = []
    current_cue = None

    for cue in cues:
        if current_cue is None:
            current_cue = cue
        else:
            duration = cue["end"] - current_cue["start"]
            if duration < min_duration:
                # pyrefly: ignore
                current_cue["text"] += " " + cue["text"]
                # pyrefly: ignore
                current_cue["end"] = cue["end"]
            else:
                merged_cues.append(current_cue)
                current_cue = cue

    if current_cue:
        merged_cues.append(current_cue)

    return merged_cues


def get_srt_content(result: AlignedTranscriptionResult) -> io.BytesIO:
    srt_file = io.BytesIO()

    srt_index = 1
    all_cues = []
    for segment in result["segments"]:
        text = punct_model.restore_punctuation(segment["text"])
        word_data = segment.get("words", [])

        sentences = split_at_sentence_end(text, word_data)
        all_cues.extend(sentences)

    merged_cues = merge_short_cues(all_cues)

    for cue in merged_cues:
        formatted_text = split_subtitle(cue["text"])

        srt_file.write(f"{srt_index}\n".encode())
        srt_file.write(f"{format_timestamp(cue['start'])} --> {format_timestamp(cue['end'])}\n".encode())
        srt_file.write(f"{formatted_text}\n\n".encode())

        srt_index += 1

    srt_file.seek(0)
    return srt_file


if __name__ == "__main__":
    # After transcribing, create subtitles with:
    result = {}
    subtitle_path = Path("output_file.srt")
    # pyrefly: ignore
    data = get_srt_content(result)
    subtitle_path.write_text(data.getvalue().decode())
