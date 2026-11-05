import db
import decide
import envoy
import gleam/list
import gleeunit/should

fn live_url() -> Result(String, Nil) {
  case
    envoy.get("PGHOST"),
    envoy.get("PGPORT"),
    envoy.get("PGUSER"),
    envoy.get("PGPASSWORD"),
    envoy.get("PGDATABASE")
  {
    Ok(host), Ok(port), Ok(user), Ok(password), Ok(database) ->
      Ok(
        "postgres://"
        <> user
        <> ":"
        <> password
        <> "@"
        <> host
        <> ":"
        <> port
        <> "/"
        <> database,
      )
    _, _, _, _, _ -> Error(Nil)
  }
}

fn with_live_rows(f: fn(List(decide.DbRow)) -> Nil) -> Nil {
  case live_url() {
    Error(_) -> Nil
    Ok(url) ->
      case db.connect(url) {
        Error(_) -> should.fail()
        Ok(conn) ->
          case db.fetch_enabled(conn) {
            Error(_) -> should.fail()
            Ok(rows) -> f(rows)
          }
      }
  }
}

pub fn db_shape_smoke_test() {
  with_live_rows(fn(rows) {
    case list.find(rows, fn(r) { r.twitch_name == "c3_smoke_alice" }) {
      Error(_) -> should.fail()
      Ok(row) -> {
        should.equal(row.discord_webhook, "https://example.invalid/c3")
        should.equal(row.announce_message, "@here alice live")
        should.equal(row.status, "offline")
      }
    }
  })
}

pub fn db_null_last_seen_empty_test() {
  with_live_rows(fn(rows) {
    case list.find(rows, fn(r) { r.twitch_name == "c3_smoke_alice" }) {
      Error(_) -> should.fail()
      Ok(row) -> should.equal(row.last_seen_online, "")
    }
  })
}

pub fn db_disabled_excluded_test() {
  with_live_rows(fn(rows) {
    list.any(rows, fn(r) { r.twitch_name == "c3_smoke_disabled" })
    |> should.equal(False)
  })
}
