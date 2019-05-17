[![Build Status](https://travis-ci.com/BurnySc2/python-template.svg?token=uZSbyQZSCPfwrTxZ8beQ&branch=master)](https://travis-ci.com/BurnySc2/python-template)

# python-template
Template for any of my upcoming Python projects


# To get to the current stage of the repo
install `pipenv` using command `pip install pipenv`

install packages using the `pip install` command here:

`pipenv install aiohttp dpcontracts`

`pipenv install --dev pytest pytest-asyncio hypothesis`



# Useful Pipenv commands
### Update dependencies
`pipenv update`
### List requirements graph
`pipenv graph`
### Check security
`pipenv check`
### Remove the virtual environment
`pipenv --rm`
### Uninstall all packages in the venv without editing pipfile
`pipenv uninstall --all`
### Install dev packages to be able to run tests
`pipenv install --dev`

`pipenv run pytest tests`


# Run python files
- install `pipenv` using command `pip install pipenv`
- run the python file `main.py` using `pipenv run main.py`
or `pipenv shell` and then run using `main.py`


# Run Tests
Single file:
`pipenv run pytest tests/test_functions.py`

Test all files in folder:
`pipenv run pytest tests/`




