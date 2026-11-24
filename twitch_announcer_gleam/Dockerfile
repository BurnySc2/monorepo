FROM ghcr.io/gleam-lang/gleam:v1.19.2-erlang-alpine AS build

WORKDIR /app

COPY gleam.toml manifest.toml ./
RUN gleam deps download

COPY src ./src
RUN gleam build
# RUN gleam test
RUN gleam export erlang-shipment

# NOTE digest pin skipped: docker unavailable, keeping erlang:28-alpine (min supported Gleam 1.19.2)
FROM erlang:28-alpine

# WHY libpq: runtime parity with twitch_stream_announcer image per deploy spec
RUN apk add --no-cache libpq ca-certificates && mkdir -p /var/crash

COPY --from=build /app/build/erlang-shipment /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["run"]
