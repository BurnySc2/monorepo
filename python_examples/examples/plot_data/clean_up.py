from pathlib import Path

DIRECTORY = Path(__file__).parent


def main():
    for file in DIRECTORY.iterdir():
        if not file.is_file():
            continue
        if file.suffix in {".html", ".png"}:
            file.unlink()


if __name__ == "__main__":
    main()
