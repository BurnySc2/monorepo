# Wrapper around pre-built openchamber-upstream image adding uv/uvx and Nim, base pinned via BASE_IMAGE build arg.
# Upstream tags: https://github.com/openchamber/openchamber/tags
ARG BASE_IMAGE=openchamber-upstream:v2.5.0
FROM ghcr.io/astral-sh/uv:latest AS uv
# Official nim image (hub.docker.com/r/nimlang/nim); nim-lang.org provides choosenim install as alternative.
FROM nimlang/nim:2.2.4 AS nim
FROM ${BASE_IMAGE}
USER root
# trixie removed libpcre3 (now libpcre2); C backend needs only gcc/g++.
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libc6-dev && rm -rf /var/lib/apt/lists/*
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
# WHY fontconfig + fonts-liberation: Chromium crashes in SkFontMgr without font config.
RUN mkdir -p /opt/ms-playwright && chown openchamber:openchamber /opt/ms-playwright && apt-get update && apt-get install -y --no-install-recommends fontconfig fonts-liberation && npx -y playwright@1.61.0 install --with-deps chromium && rm -rf /var/lib/apt/lists/* /root/.npm /root/.cache && chown -R openchamber:openchamber /opt/ms-playwright
COPY --from=uv /uv /uvx /bin/
COPY --from=nim /opt/nim /opt/nim
ENV NIM_VERSION=2.2.4
ENV PATH="/opt/nim/bin:/home/openchamber/.nimble/bin:/bin:$PATH"
USER openchamber
