import subprocess
from pathlib import Path

# poetry run python -m pytest


def get_total_length_of_file(file_path: Path) -> float:
    """No longer needed, as info.duration by the model already tells the duration of the mp3."""
    # Sanity checks
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
    assert result.returncode == 0
    return float(result.stdout)


def test_get_duration_of_file():
    file_path = Path("test") / "Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3"
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
