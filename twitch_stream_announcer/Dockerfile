FROM nimlang/nim:2.2.4-alpine-regular as base

# Install dependencies
COPY twitch_stream_announcer.nimble /root/tsa/
WORKDIR /root/tsa
RUN nimble install --depsOnly

# Build binary
COPY src /root/tsa/src
RUN nimble c -d:ssl -d:release --opt:size -o:main src/main.nim 

# https://pkgs.alpinelinux.org/package/edge/main/x86/libpq
RUN apk add --no-cache libpq

CMD ["./main"]
