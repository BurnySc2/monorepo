////
//// Postgres pool and typed queries via pgo.
//// Maps rows to DbRow for the announce cycle.
//// Squirrel codegen pending; runtime stays on pgo.
////

import decide.{type DbRow, DbRow}
import gleam/dict
import gleam/dynamic.{type Dynamic}
import gleam/dynamic/decode
import gleam/int
import gleam/list
import gleam/option
import gleam/result
import gleam/string
import gleam/uri

// WHY binary_to_atom: pgo is an Erlang driver keyed on atoms and this stdlib
// has no atom module, so atoms come from a BIF applied to literals only.

pub opaque type Conn {
  Conn(pool: Dynamic)
}

@external(erlang, "erlang", "binary_to_atom")
fn atom(name: String) -> Dynamic

@external(erlang, "application", "ensure_all_started")
fn ensure_started(app: Dynamic) -> Dynamic

@external(erlang, "pgo", "start_pool")
fn pgo_start_pool(name: Dynamic, config: List(#(Dynamic, Dynamic))) -> Dynamic

@external(erlang, "pgo", "query")
fn pgo_query(
  sql: String,
  params: List(Dynamic),
  opts: dict.Dict(Dynamic, Dynamic),
) -> Dynamic

@external(erlang, "erlang", "element")
fn tuple_element(index: Int, tuple: Dynamic) -> Dynamic

@external(erlang, "erlang", "is_tuple")
fn is_tuple(value: Dynamic) -> Bool

const select_sql =
  "SELECT id, twitch_name, discord_webhook, announce_message, announced_at::text, status, coalesce(last_seen_online::text, '') FROM stream_announcer_streams WHERE enabled IS TRUE ORDER BY id"

pub fn connect(url: String) -> Result(Conn, String) {
  use config <- result.try(pool_config(url))
  let _ = ensure_started(atom("pgo"))
  let pool = atom("twitch_announcer_pool")
  result.map(start_outcome(pgo_start_pool(pool, config)), fn(_) { Conn(pool) })
}

fn start_outcome(outcome: Dynamic) -> Result(Nil, String) {
  let started = is_tuple(outcome) && tuple_element(1, outcome) == atom("ok")
  let resumed =
    is_tuple(outcome)
    && is_tuple(tuple_element(2, outcome))
    && tuple_element(1, tuple_element(2, outcome)) == atom("already_started")
  case started || resumed {
    True -> Ok(Nil)
    False -> Error("could not start db pool: " <> string.inspect(outcome))
  }
}

fn pool_config(url: String) -> Result(List(#(Dynamic, Dynamic)), String) {
  use parsed <- result.try(
    uri.parse(url) |> result.replace_error("invalid POSTGRES_CONNECTION_STRING"),
  )
  use host <- result.try(option.to_result(
    parsed.host,
    "missing host in POSTGRES_CONNECTION_STRING",
  ))
  use userinfo <- result.try(option.to_result(
    parsed.userinfo,
    "missing user in POSTGRES_CONNECTION_STRING",
  ))
  let #(user, password) = case string.split_once(userinfo, ":") {
    Ok(#(u, p)) -> #(decode_component(u), decode_component(p))
    Error(_) -> #(decode_component(userinfo), "")
  }
  use database <- result.try(case list.last(string.split(parsed.path, "/")) {
    Ok(db) if db != "" -> Ok(decode_component(db))
    _ -> Error("missing database in POSTGRES_CONNECTION_STRING")
  })
  Ok([
    #(atom("host"), dynamic.string(decode_component(host))),
    #(atom("port"), dynamic.int(option.unwrap(parsed.port, 5432))),
    #(atom("user"), dynamic.string(user)),
    #(atom("password"), dynamic.string(password)),
    #(atom("database"), dynamic.string(database)),
  ])
}

fn decode_component(s: String) -> String {
  uri.percent_decode(s) |> result.unwrap(s)
}

pub fn fetch_enabled(conn: Conn) -> Result(List(DbRow), String) {
  use rows <- result.try(exec(conn, select_sql, []))
  Ok(list.map(rows, to_db_row))
}

pub type MarkKind {
  Announced
  Online
  Offline
}

pub fn mark_status(
  conn: Conn,
  names: List(String),
  timestamp: String,
  kind: MarkKind,
) -> Result(Nil, String) {
  case kind {
    Announced ->
      mark(
        conn,
        "announced_at = $1, status = 'online', last_seen_online = $2",
        names,
        [dynamic.string(timestamp), dynamic.string(timestamp)],
      )
    Online ->
      mark(conn, "status = 'online', last_seen_online = $1", names, [
        dynamic.string(timestamp),
      ])
    Offline -> mark(conn, "status = 'offline'", names, [])
  }
}

fn mark(
  conn: Conn,
  set_clause: String,
  names: List(String),
  extra: List(Dynamic),
) -> Result(Nil, String) {
  case names {
    [] -> Ok(Nil)
    _ -> {
      let sql =
        "UPDATE stream_announcer_streams SET "
        <> set_clause
        <> " WHERE twitch_name IN ("
        <> placeholders(list.length(extra) + 1, list.length(names))
        <> ")"
      let params = list.append(extra, list.map(names, dynamic.string))
      use _rows <- result.try(exec(conn, sql, params))
      Ok(Nil)
    }
  }
}

fn placeholders(start: Int, count: Int) -> String {
  list.repeat(Nil, count)
  |> list.index_map(fn(_, i) { "$" <> int.to_string(start + i) })
  |> string.join(",")
}

fn exec(
  conn: Conn,
  sql: String,
  params: List(Dynamic),
) -> Result(List(List(String)), String) {
  let raw = pgo_query(sql, params, dict.from_list([#(atom("pool"), conn.pool)]))
  case decode.run(raw, rows_decoder()) {
    Ok(rows) -> Ok(rows)
    Error(_) -> Error("db query failed: " <> string.inspect(raw))
  }
}

fn rows_decoder() -> decode.Decoder(List(List(String))) {
  decode.subfield(
    [atom("rows")],
    decode.list(decode.list(cell_decoder())),
    fn(rows) { decode.success(rows) },
  )
}

fn cell_decoder() -> decode.Decoder(String) {
  let texty =
    decode.one_of(decode.string, [decode.map(decode.int, int.to_string)])
  decode.map(decode.optional(texty), fn(cell) { option.unwrap(cell, "") })
}

fn to_db_row(cells: List(String)) -> DbRow {
  let at = fn(i) { list.drop(cells, i) |> list.first |> result.unwrap("") }
  DbRow(
    twitch_name: at(1),
    discord_webhook: at(2),
    announce_message: at(3),
    status: at(5),
    last_seen_online: at(6),
  )
}
