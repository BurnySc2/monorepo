VERSION 0.6
ARG NODEVERSION=19 # 14, 16, 18, 19
ARG PYTHONVERSION=3.11 # 3.8 to 3.11
FROM alpine:3.15 # Is only used for formatting, so image can be as small as possible

# Run autoformatter on all projects
format:
    BUILD ./burny_common+format
    BUILD ./discord_bot+format
    BUILD ./fastapi_server+format
    BUILD ./python_examples+format
    BUILD ./bored_gems+format
    BUILD ./svelte_frontend+format

install-backend:
    BUILD ./burny_common+install-dev --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./discord_bot+install-dev --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./fastapi_server+install-dev --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./python_examples+install-dev --PYTHONVERSION=${PYTHONVERSION}

install-frontend:
    BUILD ./bored_gems+install-all --NODEVERSION=${NODEVERSION}
    BUILD ./svelte_frontend+install-all --NODEVERSION=${NODEVERSION}

pre-commit-backend:
    BUILD ./burny_common+pre-commit --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./discord_bot+pre-commit --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./fastapi_server+pre-commit --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./python_examples+pre-commit --PYTHONVERSION=${PYTHONVERSION}

# TODO pre-commit-frontend

check-backend:
    BUILD ./burny_common+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./discord_bot+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./fastapi_server+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./python_examples+all --PYTHONVERSION=${PYTHONVERSION}

check-frontend:
    BUILD ./bored_gems+all --NODEVERSION=${NODEVERSION}
    BUILD ./svelte_frontend+all --NODEVERSION=${NODEVERSION}

# Install all requirements to be able to run format-checks, linter and tests
install-all:
    BUILD +install-backend
    BUILD +install-frontend

# Run format-checks and linter
pre-commit:
    BUILD +pre-commit-backend
    # BUILD +pre-commit-frontend

# Run format-checks, linter and tests
all:
    BUILD +check-backend
    BUILD +check-frontend
