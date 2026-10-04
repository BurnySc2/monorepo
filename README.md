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
- [Docker](https://www.docker.com)

## VScode
Run VScode task called `Install requirements` or alternatively run `uv sync` in the python projects.

Open the Command Palette and `Workspaces: Add Folder to Workspace...` and select the folders you want to edit.

Now set up the correct interpreter path.

## VS code
TODO

# Check dependencies
To avoid packages with large amount of dependencies, we can use `pipdeptree`
```sh
uv run pipdeptree > deps.txt
```

# Lint one project
```sh
bash fastapi_server/lint.sh
```

# Lint all projects + workflows
```sh
bash lint.sh
```

This runs ruff lint, ruff format check, pyrefly type check, sqlfluff lint, plus yamllint, yaml parse, checkout-pin grep, whitespace, and docker checks

# Autoformat all files
```sh
uv run ruff check . --fix && uv run ruff format .
```

# Recommended websites and tools:
[Convert JSON API response to types](https://app.quicktype.io/#l=Python)
[Convert curl to python requests](https://curlconverter.com)
