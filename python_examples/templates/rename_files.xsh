from pathlib import Path

index = 1
# for file in sorted(pg`./*`, key=lambda f: (len(f.name), f.name)):
for file in pg`./*`:
    file: Path
    if file.suffix not in {".pdf"}:
        continue
    target_name = f"{index:02} {file.name}"
    print(f"Renaming {file.name=} to {target_name=}")
    file.rename(target_name)
    index += 1
