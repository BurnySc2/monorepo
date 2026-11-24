#!/bin/sh
set -eu
if [ "${DEBUG_BOOT:-0}" = "1" ]; then
  echo "DEBUG_BOOT=1: boot diagnostics"
  echo "ERL_LIBS=${ERL_LIBS:-<unset>}"
  ls -R /app | head -n 100
  erl -noshell -eval "io:format(\"otp_release: ~s~n\", [erlang:system_info(otp_release)]), io:format(\"main: ~p~n\", [code:which(main)]), io:format(\"twitch_announcer_gleam@@main: ~p~n\", [code:which('twitch_announcer_gleam@@main')]), halt()."
fi
exec /app/entrypoint.sh "$@"
