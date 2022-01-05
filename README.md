[![publish_example_package](https://github.com/BurnySc2/monorepo/actions/workflows/publish_example_package.yml/badge.svg?branch=master)](https://github.com/BurnySc2/monorepo/actions/workflows/publish_example_package.yml)
[![python_examples](https://github.com/BurnySc2/monorepo/actions/workflows/python_examples.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/python_examples.yml)
[![test_fastapi_server](https://github.com/BurnySc2/monorepo/actions/workflows/test_fastapi_server.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/test_fastapi_server.yml)
[![test_react_frontend](https://github.com/BurnySc2/monorepo/actions/workflows/test_react_frontend.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/test_react_frontend.yml)
[![test_svelte_frontend](https://github.com/BurnySc2/monorepo/actions/workflows/test_svelte_frontend.yml/badge.svg)](https://github.com/BurnySc2/monorepo/actions/workflows/test_svelte_frontend.yml)

# Monorepo
My monorepo for various tools and showcases

[Preview](https://burnysc2.github.io/monorepo/)

[Dev branch Preview](https://burnysc2.github.io/monorepodev/)

# Useful Poetry commands
https://python-poetry.org/docs/cli/
### Create new project
`poetry init`
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
### Run a file in virtual environment
`poetry run python python_examples/main.py`

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
Single function:
`poetry run pytest test/test_functions.py::test_fuction_name`
Single function in class:
`poetry run pytest test/test_functions.py::class_name::test_fuction_name`

Test all files in project:
`poetry run pytest`

# Run and display code coverage 
In pycharm: right click folder and `More Run/Debug` -> `Run pytest in '...' with coverage'`

```
poetry run pytest --cov=. --cov-report xml --cov-report html && poetry run coverage html
```

then use `coverage gutters` extension in VScode

or open the generated html file in folder `htmlcov`

# Install and run all pre-commit hook scripts
```py
poetry run pre-commit install
poetry run pre-commit run --all-files
```

This runs pylint, mypy, pytest tests, apply autoformatter yapf

# Autoformat all files
`poetry run yapf ./**/*.py -i`
