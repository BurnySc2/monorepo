//// CLI entry for this Gleam port of the Twitch announcer.
//// Dispatches on STAGE: DEV runs the announce cycle once,
//// PROD repeats it forever with a 20s sleep; owns all I/O.
//// Pure announce choice lives in decide; DB writes fire in PROD only.

import birl
import db
import decide
import discord
import dotenv
import envoy
import gleam/dict
import gleam/erlang/process
import gleam/int
import gleam/io
import gleam/list
import gleam/result
import gleam/string
import gleam/time/timestamp.{type Timestamp}
import twitch

type Stage {
  Build
  Dev
  Prod
}

type Config {
  Config(
    stage: Stage,
    client_id: String,
    client_secret: String,
    grace_seconds: Int,
  )
}

fn stage_string(stage: Stage) -> String {
  case stage {
    Build -> "BUILD"
    Dev -> "DEV"
    Prod -> "PROD"
  }
}

fn read_stage() -> Stage {
  case envoy.get("STAGE") {
    Ok("BUILD") -> Build
    Ok("DEV") -> Dev
    Ok("PROD") -> Prod
    _ -> panic as "STAGE must be one of BUILD, DEV, PROD"
  }
}

pub fn parse_grace_seconds(value: String) -> Int {
  case int.parse(value) {
    Ok(seconds) if seconds >= 0 -> seconds
    _ -> 1800
  }
}

fn read_config(stage: Stage) -> Config {
  let client_id = case envoy.get("TWITCH_APP_ID") {
    Ok(id) -> id
    Error(_) -> panic as "missing TWITCH_APP_ID"
  }
  let client_secret = case envoy.get("TWITCH_APP_SECRET") {
    Ok(secret) -> secret
    Error(_) -> panic as "missing TWITCH_APP_SECRET"
  }
  let grace_seconds = case envoy.get("OFFLINE_GRACE_TIME") {
    Ok(value) -> parse_grace_seconds(value)
    Error(_) -> 1800
  }
  Config(stage:, client_id:, client_secret:, grace_seconds:)
}

fn utc_now() -> Timestamp {
  let now = birl.now()
  timestamp.from_unix_seconds_and_nanoseconds(
    birl.to_unix(now),
    { birl.to_unix_micro(now) % 1_000_000 } * 1000,
  )
}

fn write_if_present(
  label: String,
  names: List(String),
  stage: Stage,
  write: fn() -> Result(Nil, String),
) -> Result(Nil, String) {
  case names {
    [] -> Ok(Nil)
    _ -> {
      io.println(label <> string.inspect(names))
      case stage {
        Prod -> write()
        _ -> Ok(Nil)
      }
    }
  }
}

fn update_entries(
  conn: db.Conn,
  config: Config,
  announced: List(String),
  online: List(String),
  now_offline: List(String),
) -> Result(Nil, String) {
  let at = utc_now()
  let updates = [
    #("Updating announced streams in db: ", announced, db.Announced),
    #("Updating online streams in db: ", online, db.Online),
    #("Updating offline streams in db: ", now_offline, db.Offline),
  ]
  list.try_each(updates, fn(update) {
    let #(label, names, kind) = update
    write_if_present(label, names, config.stage, fn() {
      db.mark_status(conn, names, at, kind)
    })
  })
}

fn run_once(conn: db.Conn, config: Config) -> Nil {
  let outcome = {
    use rows <- result.try(db.fetch_enabled(conn))
    use token <- result.try(twitch.get_access_token(
      config.client_id,
      config.client_secret,
    ))
    let names = list.map(rows, fn(row) { row.twitch_name }) |> list.unique
    use infos <- result.try(twitch.get_stream_infos(
      names,
      token,
      config.client_id,
    ))
    let now_epoch = birl.now() |> birl.to_unix
    let #(announced, online, now_offline, to_announce) =
      decide.decide(rows, dict.values(infos), now_epoch, config.grace_seconds)
    use _ <- result.try(update_entries(
      conn,
      config,
      announced,
      online,
      now_offline,
    ))
    use _ <- result.try(discord.post_announcements(
      to_announce,
      stage_string(config.stage),
    ))
    Ok(Nil)
  }
  case outcome {
    Ok(Nil) -> Nil
    Error(reason) -> io.println("run_once failed: " <> reason)
  }
}

fn loop_forever(conn: db.Conn, config: Config) -> Nil {
  io.println("Running once")
  run_once(conn, config)
  process.sleep(20_000)
  loop_forever(conn, config)
}

fn run_stage(stage: Stage) -> Nil {
  let config = read_config(stage)
  let url = case envoy.get("POSTGRES_CONNECTION_STRING") {
    Ok(url) -> url
    Error(_) -> panic as "missing POSTGRES_CONNECTION_STRING"
  }
  case db.connect(url) {
    Ok(conn) ->
      case stage {
        Prod -> loop_forever(conn, config)
        _ -> run_once(conn, config)
      }
    Error(reason) -> panic as reason
  }
}

pub fn main() {
  io.println("Started twitch_announcer_gleam.main")
  dotenv.load_dotenv()
  case read_stage() {
    Build -> io.println("BUILD stage: skipping announcer run")
    Dev -> run_stage(Dev)
    Prod -> run_stage(Prod)
  }
}
