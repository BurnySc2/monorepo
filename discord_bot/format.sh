# pip install poetry
# poetry install
# Remove unused imports
poetry run pycln .
# Sort imports
poetry run isort .
# Format code
poetry run yapf -ir .
