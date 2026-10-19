# Wrapper around pre-built openchamber-upstream image adding uv/uvx and Nim, base pinned via BASE_IMAGE build arg.
ARG BASE_IMAGE=openchamber-upstream:main
FROM ghcr.io/astral-sh/uv:latest AS uv
# Official nim image (hub.docker.com/r/nimlang/nim); nim-lang.org provides choosenim install as alternative.
FROM nimlang/nim:2.2.4 AS nim
FROM ${BASE_IMAGE}
USER root
# trixie removed libpcre3 (now libpcre2); C backend needs only gcc/g++.
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libc6-dev && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /uvx /bin/
COPY --from=nim /opt/nim /opt/nim
ENV NIM_VERSION=2.2.4
ENV PATH="/opt/nim/bin:/home/openchamber/.nimble/bin:/bin:$PATH"
USER openchamber
