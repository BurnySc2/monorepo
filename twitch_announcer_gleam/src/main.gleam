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

fn utc_now() {
  birl.now()
}

pub fn db_timestamp(now: birl.Time) -> String {
  let birl.Day(year, month, day) = birl.get_day(now)
  let birl.TimeOfDay(hour, minute, second, nanosecond) =
    birl.get_time_of_day(now)
  int.to_string(year)
  <> "-"
  <> string.pad_start(int.to_string(month), to: 2, with: "0")
  <> "-"
  <> string.pad_start(int.to_string(day), to: 2, with: "0")
  <> " "
  <> string.pad_start(int.to_string(hour), to: 2, with: "0")
  <> ":"
  <> string.pad_start(int.to_string(minute), to: 2, with: "0")
  <> ":"
  <> string.pad_start(int.to_string(second), to: 2, with: "0")
  <> "."
  <> string.pad_start(int.to_string(nanosecond / 1_000_000), to: 3, with: "0")
}

fn now_ms() -> Int {
  birl.now() |> birl.to_unix_milli
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
  let timestamp = utc_now() |> db_timestamp
  use _ <- result.try(
    write_if_present(
      "Updating announced streams in db: ",
      announced,
      config.stage,
      fn() { db.mark_announced(conn, announced, timestamp) },
    ),
  )
  use _ <- result.try(
    write_if_present(
      "Updating online streams in db: ",
      online,
      config.stage,
      fn() { db.mark_online(conn, online, timestamp) },
    ),
  )
  use _ <- result.try(
    write_if_present(
      "Updating offline streams in db: ",
      now_offline,
      config.stage,
      fn() { db.mark_offline(conn, now_offline, timestamp) },
    ),
  )
  Ok(Nil)
}

fn log_timings(
  fetch_db: Int,
  fetch_twitch: Int,
  deciding: Int,
  update: Int,
  webhooks: Int,
  total: Int,
) -> Nil {
  io.println("Fetching database entries: " <> int.to_string(fetch_db) <> "ms")
  io.println(
    "Fetching twitch api data: " <> int.to_string(fetch_twitch) <> "ms",
  )
  io.println(
    "Calculating which streams to announce: " <> int.to_string(deciding) <> "ms",
  )
  io.println("Updating database entries: " <> int.to_string(update) <> "ms")
  io.println("Sending webhooks: " <> int.to_string(webhooks) <> "ms")
  io.println("Total time taken: " <> int.to_string(total) <> "ms")
}

fn run_once(conn: db.Conn, config: Config) -> Nil {
  let t1 = now_ms()
  let outcome = {
    use rows <- result.try(db.fetch_enabled(conn))
    let t2 = now_ms()
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
    let t3 = now_ms()
    let now_epoch = birl.now() |> birl.to_unix
    let #(announced, online, now_offline, to_announce) =
      decide.decide(rows, dict.values(infos), now_epoch, config.grace_seconds)
    let t4 = now_ms()
    use _ <- result.try(update_entries(
      conn,
      config,
      announced,
      online,
      now_offline,
    ))
    let t5 = now_ms()
    use _ <- result.try(discord.post_announcements(
      to_announce,
      stage_string(config.stage),
    ))
    let t6 = now_ms()
    Ok(#(t2 - t1, t3 - t2, t4 - t3, t5 - t4, t6 - t5, t6 - t1))
  }
  case outcome {
    Ok(#(fetch_db, fetch_twitch, decided, updated, webhooks, total)) ->
      case config.stage {
        Dev ->
          log_timings(fetch_db, fetch_twitch, decided, updated, webhooks, total)
        _ -> Nil
      }
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
