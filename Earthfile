VERSION 0.6
ARG NODEVERSION=18 # 14, 16, 18, 19
ARG PYTHONVERSION=3.8 # 3.8 to 3.11
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

check-backend:
    BUILD ./burny_common+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./discord_bot+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./fastapi_server+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./python_examples+all --PYTHONVERSION=${PYTHONVERSION}

check-frontend:
    BUILD ./bored_gems+all --NODEVERSION=${NODEVERSION}
    BUILD ./svelte_frontend+all --NODEVERSION=${NODEVERSION}

# Export cache for github actions runner
export-cache-backend:
    BUILD ./burny_common+export-cache --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./discord_bot+export-cache --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./fastapi_server+export-cache --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./python_examples+export-cache --PYTHONVERSION=${PYTHONVERSION}

# Install all requirements to be able to run format-checks, linter and tests
install-all:
    BUILD +install-backend
    BUILD +install-frontend

# Run format-checks, linter and tests
all:
    BUILD +check-backend
    BUILD +check-frontend