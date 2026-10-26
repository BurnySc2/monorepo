# Wrapper around pre-built openchamber-upstream image adding uv/uvx and Nim, base pinned via BASE_IMAGE build arg.
# Rendered by openchamber_setup.yml from OPENCHAMBER_UPSTREAM_REF; raw docker build requires --build-arg override.
# Upstream tags: https://github.com/openchamber/openchamber/tags
ARG BASE_IMAGE=openchamber-upstream:{{ OPENCHAMBER_UPSTREAM_REF }}
FROM ghcr.io/astral-sh/uv:latest AS uv
# Official nim image (hub.docker.com/r/nimlang/nim); nim-lang.org provides choosenim install as alternative.
FROM nimlang/nim:2.2.4 AS nim
FROM ${BASE_IMAGE}
USER root
# trixie removed libpcre3 (now libpcre2); C backend needs only gcc/g++.
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libc6-dev && rm -rf /var/lib/apt/lists/*
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
# WHY fontconfig + fonts-liberation: Chromium/Firefox crash without font config (SkFontMgr).
RUN mkdir -p /opt/ms-playwright && chown openchamber:openchamber /opt/ms-playwright && apt-get update && apt-get install -y --no-install-recommends fontconfig fonts-liberation && npx -y playwright@1.61.0 install --with-deps chromium firefox && npx -y playwright@1.61.0 install --only-shell chromium && rm -rf /var/lib/apt/lists/* /root/.npm /root/.cache && chown -R openchamber:openchamber /opt/ms-playwright
COPY --from=uv /uv /uvx /bin/
COPY --from=nim /opt/nim /opt/nim
COPY --from=mwader/static-ffmpeg:8.1.1@sha256:735f84b905e00d5c618b667f0b053f83b1096f5fc404c607e6134bf2275a0e0a /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:8.1.1@sha256:735f84b905e00d5c618b667f0b053f83b1096f5fc404c607e6134bf2275a0e0a /ffprobe /usr/local/bin/
RUN chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe && ffmpeg -version && ffprobe -version
ENV NIM_VERSION=2.2.4
ENV PATH="/opt/nim/bin:/home/openchamber/.nimble/bin:/bin:$PATH"
USER openchamber