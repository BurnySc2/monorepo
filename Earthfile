VERSION 0.6
ARG NODEVERSION=18 # 14, 16, 18, 19
ARG PYTHONVERSION=3.8 # 3.8 to 3.11
FROM python:${PYTHONVERSION}-alpine # Is only used for formatting, so image can be as small as possible

format:
    BUILD ./burny_common+format
    BUILD ./discord_bot+format
    BUILD ./fastapi_server+format
    BUILD ./python_examples+format
    BUILD ./bored_gems+format
    BUILD ./svelte_frontend+format

all:
    BUILD ./burny_common+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./discord_bot+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./fastapi_server+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./python_examples+all --PYTHONVERSION=${PYTHONVERSION}
    BUILD ./bored_gems+all --NODEVERSION=${NODEVERSION}
    BUILD ./svelte_frontend+all --NODEVERSION=${NODEVERSION}