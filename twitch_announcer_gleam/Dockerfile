FROM ghcr.io/gleam-lang/gleam:v1.19.2-erlang-alpine AS build

WORKDIR /app

COPY gleam.toml ./
RUN gleam deps download

COPY src ./src
RUN gleam build
# RUN gleam test
RUN gleam export erlang-shipment

FROM erlang:27-alpine

# WHY libpq: runtime parity with twitch_stream_announcer image per deploy spec
RUN apk add --no-cache libpq

COPY --from=build /app/build/erlang-shipment /

ENV ERL_LIBS=/
# WHY ERL_LIBS=/: shipment root on path so run(pkg) resolves without -pa — see gleam export erlang-shipment
ENTRYPOINT ["erl", "-noshell", "-noinput", "-eval", "twitch_announcer_gleam@@main:run(twitch_announcer_gleam), init:stop()."]
