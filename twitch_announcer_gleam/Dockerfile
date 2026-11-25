FROM ghcr.io/gleam-lang/gleam:v1.19.2-erlang-alpine AS build

WORKDIR /app

COPY gleam.toml manifest.toml ./
RUN gleam deps download

COPY src ./src
# RUN gleam test
RUN gleam export erlang-shipment

# WHY slim runtime: libpq removed (pgo/pog pure-Erlang no libpq linkage), ca-certificates kept (HTTPS Twitch/Discord); digest pin skipped: docker unavailable
FROM erlang:28-alpine

RUN apk add --no-cache ca-certificates && mkdir -p /var/crash

COPY --from=build /app/build/erlang-shipment /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["run"]
