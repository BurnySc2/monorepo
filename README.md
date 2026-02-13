[![discord_bot](https://github.com/BurnySc2/monorepo/actions/workflows/test_discord_bot.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/test_discord_bot.yml)
[![fastapi_server](https://github.com/BurnySc2/monorepo/actions/workflows/test_fastapi_server.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/test_fastapi_server.yml)
[![stream_announcer](https://github.com/BurnySc2/monorepo/actions/workflows/test_stream_announcer.yml/badge.svg?branch=develop)](https://github.com/BurnySc2/monorepo/actions/workflows/test_stream_announcer.yml)
[![python_examples](https://github.com/BurnySc2/monorepo/actions/workflows/python_examples.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/python_examples.yml)
[![earthly_checks](https://github.com/BurnySc2/monorepo/actions/workflows/earthly_project_check.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/earthly_project_check.yml)

# Monorepo
My monorepo for various tools and showcases

# Development
### Pre-requisites
- [Python](https://www.python.org/downloads)
    - [uv](https://docs.astral.sh/uv/)
- [Earthly](https://earthly.dev)
    - [Docker](https://www.docker.com)

## VScode
Run VScode task called `Install requirements` or alternatively run `sh .vscode/install_requirements.sh` or alternatively run `uv sync` in the python projects.

Open the Command Palette and `Workspaces: Add Folder to Workspace...` and select the folders you want to edit.

Now set up the correct interpreter path.

## VS code
TODO

# Check dependencies
To avoid packages with large amount of dependencies, we can use `pipdeptree`
```sh
uv run pipdeptree > deps.txt
```

# Install and run pre-commit hook on all staged files
```sh
uv run pre-commit install
uv run pre-commit run --all-files --verbose --hook-stage push
```

This runs pylint, mypy, pytest tests, apply autoformatter yapf

# Autoformat all files
`earthly +format`

# Recommended websites and tools:
[Convert JSON API response to types](https://app.quicktype.io/#l=Python)
[Convert curl to python requests](https://curlconverter.com)
