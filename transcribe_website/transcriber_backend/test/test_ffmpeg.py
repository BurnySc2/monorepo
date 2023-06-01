import subprocess
from pathlib import Path

from src.argparser import get_total_length_of_file


def test_get_duration_of_file():
    file_path = Path("test") / "Eclypxe - Black Roses (ft. Annamarie Rosanio) Copyright Free Music.mp3"
    assert file_path.is_file()

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path.absolute()),
        ],
        capture_output=True
    )
    assert result.stdout == b"193.632000\n", result.stdout
    result2 = get_total_length_of_file(file_path)
    assert float(result.stdout) == result2, result2
