[![publish_example_package](https://github.com/BurnySc2/python-template/actions/workflows/publish_example_package.yml/badge.svg?branch=master)](https://github.com/BurnySc2/python-template/actions/workflows/publish_example_package.yml)
[![python_examples](https://github.com/BurnySc2/python-template/actions/workflows/python_examples.yml/badge.svg)](https://github.com/BurnySc2/python-template/actions/workflows/python_examples.yml)
[![test_fastapi_server](https://github.com/BurnySc2/python-template/actions/workflows/test_fastapi_server.yml/badge.svg)](https://github.com/BurnySc2/python-template/actions/workflows/test_fastapi_server.yml)
[![test_react_frontend](https://github.com/BurnySc2/python-template/actions/workflows/test_react_frontend.yml/badge.svg)](https://github.com/BurnySc2/python-template/actions/workflows/test_react_frontend.yml)
[![test_svelte_frontend](https://github.com/BurnySc2/python-template/actions/workflows/test_svelte_frontend.yml/badge.svg)](https://github.com/BurnySc2/python-template/actions/workflows/test_svelte_frontend.yml)

# python-template
Template for any of my upcoming Python projects


# Useful Poetry commands
https://python-poetry.org/docs/cli/
### Create new project
`poetry init`

or

`poetry new <project-name>`
### Install dependencies
`poetry install`

`poetry install --no-dev`
### Add dependencies
`poetry add <package-name>`

Add dev dependency:

`poetry add <package-name> --dev`
### Remove dependencies
`poetry remove <package-name>`
### Update dependencies
`poetry update`
### List current and latest available version
`poetry show -l`
### Same as above, but only show outdated
`poetry show -o`
### List of packages
`poetry show`
### Validate pyproject.toml
`poetry check`
### Build for distribution
`poetry build`
### Publish on pypy
`poetry publish`
### Run a file in virtual environment
`poetry run python main.py`

`poetry run pytest`

### Write requirements.txt from Poetry lock file
`poetry export -f requirements.txt > requirements.txt`


# Run python files
- install `poetry` using command `pip install poetry`
- run the python file `main.py` using `poetry run python main.py`
- or `poetry shell` and then run `python main.py`


# Run Tests
Single file:
`poetry run pytest test/test_functions.py`

Test all files in folder:
`poetry run pytest`

# Install and run all pre-commit hook scripts
```py
poetry run pre-commit install
poetry run pre-commit run --all-files
```

This runs pylint, mypy, pytest tests, apply autoformatter yapf

# Autoformat all files
`poetry run yapf ./**/*.py -i`
