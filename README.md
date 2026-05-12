[![Discord Bot](https://github.com/BurnySc2/monorepo/actions/workflows/discord_bot.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/discord_bot.yml)
[![Fastapi Server](https://github.com/BurnySc2/monorepo/actions/workflows/fastapi_server.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/fastapi_server.yml)
[![Svelte Frontends](https://github.com/BurnySc2/monorepo/actions/workflows/svelte_frontends.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/svelte_frontends.yml)
[![Stream Announcer](https://github.com/BurnySc2/monorepo/actions/workflows/stream_announcer.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/stream_announcer.yml)
[![Python Examples](https://github.com/BurnySc2/monorepo/actions/workflows/python_examples.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/python_examples.yml)

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
