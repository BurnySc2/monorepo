uv run python -m cProfile -o main.prof src/main.py
uv run snakeviz main.prof
