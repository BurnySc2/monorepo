VERSION 0.6
FROM python:3.10-slim
WORKDIR /root

format:
    BUILD ./burny_common+format
    BUILD ./discord_bot+format
    BUILD ./fastapi_server+format
    BUILD ./python_examples+format

all:
    BUILD ./burny_common+all
    BUILD ./discord_bot+all
    BUILD ./fastapi_server+all
    BUILD ./python_examples+all