# Wrapper around pre-built openchamber-upstream image adding uv/uvx only, base pinned via BASE_IMAGE build arg.
ARG BASE_IMAGE=openchamber-upstream:main
FROM ghcr.io/astral-sh/uv:latest AS uv
FROM ${BASE_IMAGE}
USER root
COPY --from=uv /uv /uvx /bin/
ENV PATH="/bin:$PATH"
USER openchamber
