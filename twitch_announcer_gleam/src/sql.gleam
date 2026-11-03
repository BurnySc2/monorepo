//// This module contains the code to run the sql queries defined in
//// `.././src/sql`.
//// > 🐿️ This module was generated automatically using v4.7.0 of
//// > the [squirrel package](https://github.com/giacomocavalieri/squirrel).
////

import gleam/dynamic/decode
import gleam/time/timestamp.{type Timestamp}
import pog

/// A row you get from running the `fetch_enabled` query
/// defined in `.././src/sql/fetch_enabled.sql`.
///
/// > 🐿️ This type definition was generated automatically using v4.7.0 of the
/// > [squirrel package](https://github.com/giacomocavalieri/squirrel).
///
pub type FetchEnabledRow {
  FetchEnabledRow(
    twitch_name: String,
    discord_webhook: String,
    announce_message: String,
    status: String,
    last_seen_online: Timestamp,
    announced_at: Timestamp,
  )
}

/// Runs the `fetch_enabled` query
/// defined in `.././src/sql/fetch_enabled.sql`.
///
/// > 🐿️ This function was generated automatically using v4.7.0 of
/// > the [squirrel package](https://github.com/giacomocavalieri/squirrel).
///
pub fn fetch_enabled(
  db: pog.Connection,
) -> Result(pog.Returned(FetchEnabledRow), pog.QueryError) {
  let decoder = {
    use twitch_name <- decode.field(0, decode.string)
    use discord_webhook <- decode.field(1, decode.string)
    use announce_message <- decode.field(2, decode.string)
    use status <- decode.field(3, decode.string)
    use last_seen_online <- decode.field(4, pog.timestamp_decoder())
    use announced_at <- decode.field(5, pog.timestamp_decoder())
    decode.success(FetchEnabledRow(
      twitch_name:,
      discord_webhook:,
      announce_message:,
      status:,
      last_seen_online:,
      announced_at:,
    ))
  }

  "SELECT COALESCE(twitch_name, '') AS twitch_name, COALESCE(discord_webhook, '') AS discord_webhook, COALESCE(announce_message, '') AS announce_message, COALESCE(status, 'offline') AS status, last_seen_online, announced_at FROM stream_announcer_streams WHERE enabled IS TRUE ORDER BY id;
"
  |> pog.query
  |> pog.returning(decoder)
  |> pog.execute(db)
}

/// Runs the `mark_announced` query
/// defined in `.././src/sql/mark_announced.sql`.
///
/// > 🐿️ This function was generated automatically using v4.7.0 of
/// > the [squirrel package](https://github.com/giacomocavalieri/squirrel).
///
pub fn mark_announced(
  db: pog.Connection,
  last_seen_online: Timestamp,
  arg_2: List(String),
) -> Result(pog.Returned(Nil), pog.QueryError) {
  let decoder = decode.map(decode.dynamic, fn(_) { Nil })

  "UPDATE stream_announcer_streams SET announced_at = $1, status = 'online', last_seen_online = $1 WHERE twitch_name = ANY($2);
"
  |> pog.query
  |> pog.parameter(pog.timestamp(last_seen_online))
  |> pog.parameter(pog.array(fn(value) { pog.text(value) }, arg_2))
  |> pog.returning(decoder)
  |> pog.execute(db)
}

/// Runs the `mark_offline` query
/// defined in `.././src/sql/mark_offline.sql`.
///
/// > 🐿️ This function was generated automatically using v4.7.0 of
/// > the [squirrel package](https://github.com/giacomocavalieri/squirrel).
///
pub fn mark_offline(
  db: pog.Connection,
  arg_1: List(String),
) -> Result(pog.Returned(Nil), pog.QueryError) {
  let decoder = decode.map(decode.dynamic, fn(_) { Nil })

  "UPDATE stream_announcer_streams SET status = 'offline' WHERE twitch_name = ANY($1);
"
  |> pog.query
  |> pog.parameter(pog.array(fn(value) { pog.text(value) }, arg_1))
  |> pog.returning(decoder)
  |> pog.execute(db)
}

/// Runs the `mark_online` query
/// defined in `.././src/sql/mark_online.sql`.
///
/// > 🐿️ This function was generated automatically using v4.7.0 of
/// > the [squirrel package](https://github.com/giacomocavalieri/squirrel).
///
pub fn mark_online(
  db: pog.Connection,
  last_seen_online: Timestamp,
  arg_2: List(String),
) -> Result(pog.Returned(Nil), pog.QueryError) {
  let decoder = decode.map(decode.dynamic, fn(_) { Nil })

  "UPDATE stream_announcer_streams SET status = 'online', last_seen_online = $1 WHERE twitch_name = ANY($2);
"
  |> pog.query
  |> pog.parameter(pog.timestamp(last_seen_online))
  |> pog.parameter(pog.array(fn(value) { pog.text(value) }, arg_2))
  |> pog.returning(decoder)
  |> pog.execute(db)
}
