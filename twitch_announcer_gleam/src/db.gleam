////
//// Postgres access via pog plus the squirrel-generated queries in sql.
//// Converts sql rows to decide DbRow (String fields, "" = unknown time).
//// Writes take a Timestamp from main straight into the sql queries.
////

import birl
import decide.{type DbRow, DbRow}
import gleam/erlang/process
import gleam/list
import gleam/otp/actor
import gleam/result
import gleam/string
import gleam/time/timestamp.{type Timestamp}
import pog
import sql

pub opaque type Conn {
  Conn(pool: pog.Connection)
}

pub fn connect(url: String) -> Result(Conn, String) {
  let name = process.new_name("twitch_announcer_pool")
  use config <- result.try(
    pog.url_config(name, url)
    |> result.replace_error("invalid POSTGRES_CONNECTION_STRING"),
  )
  case pog.start(config) {
    Ok(actor.Started(_, conn)) -> Ok(Conn(conn))
    Error(err) -> Error("could not start db pool: " <> string.inspect(err))
  }
}

pub fn fetch_enabled(conn: Conn) -> Result(List(DbRow), String) {
  use returned <- result.try(
    sql.fetch_enabled(conn.pool) |> result.map_error(query_error),
  )
  Ok(list.map(returned.rows, to_db_row))
}

pub type MarkKind {
  Announced
  Online
  Offline
}

pub fn mark_status(
  conn: Conn,
  names: List(String),
  at: Timestamp,
  kind: MarkKind,
) -> Result(Nil, String) {
  case names {
    [] -> Ok(Nil)
    _ -> {
      case kind {
        Announced -> sql.mark_announced(conn.pool, at, names)
        Online -> sql.mark_online(conn.pool, at, names)
        Offline -> sql.mark_offline(conn.pool, names)
      }
      |> result.map(fn(_) { Nil })
      |> result.map_error(query_error)
    }
  }
}

fn to_db_row(row: sql.FetchEnabledRow) -> DbRow {
  DbRow(
    twitch_name: row.twitch_name,
    discord_webhook: row.discord_webhook,
    announce_message: row.announce_message,
    status: row.status,
    last_seen_online: timestamp_to_string(row.last_seen_online),
  )
}

// WHY epoch-to-empty: decide treats "" as unknown (fallback_last_seen) while a
// raw 1970 stamp would parse as a real date; both are ancient, this keeps "" semantics.
fn timestamp_to_string(ts: Timestamp) -> String {
  let #(secs, nanos) = timestamp.to_unix_seconds_and_nanoseconds(ts)
  let t = birl.from_unix_milli(secs * 1000 + nanos / 1_000_000)
  let formatted =
    birl.to_naive_date_string(t) <> " " <> birl.to_naive_time_string(t)
  case string.starts_with(formatted, "1970-01-01") {
    True -> ""
    False -> formatted
  }
}

fn query_error(err: pog.QueryError) -> String {
  "db query failed: " <> string.inspect(err)
}
