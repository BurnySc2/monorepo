import birl
import gleam/list
import gleam/string
import humanize

// WHY caller-lowercases: Twitch logins are lowercase-only; Nim asserts/toLowers at fetch site, so decide matches usernames exactly — see main.nim get_twitch_info_for_20/get_twitch_infos.

pub type StreamInfo {
  StreamInfo(
    username: String,
    displayname: String,
    live: Bool,
    stream_title: String,
    live_since: String,
    stream_category: String,
  )
}

pub type AnnounceInfo {
  AnnounceInfo(
    username: String,
    displayname: String,
    live: Bool,
    stream_title: String,
    live_since: String,
    stream_category: String,
    webhook_url: String,
    announce_message: String,
  )
}

pub type DbRow {
  DbRow(
    twitch_name: String,
    discord_webhook: String,
    announce_message: String,
    status: String,
    last_seen_online: String,
  )
}

const fallback_last_seen = "2000-01-01 01:01:01.000000"

// Strict Z-only: birl.parse also accepts offsets and lowercase z.
pub fn parse_twitch_time(s: String) -> Result(Int, Nil) {
  case string.ends_with(s, "Z") {
    False -> Error(Nil)
    True ->
      case birl.parse(s) {
        Error(_) -> Error(Nil)
        Ok(t) -> {
          let back =
            birl.to_naive_date_string(t)
            <> "T"
            <> string.slice(birl.to_naive_time_string(t), 0, 8)
            <> "Z"
          case back == s {
            True -> Ok(birl.to_unix(t))
            False -> Error(Nil)
          }
        }
      }
  }
}

pub fn parse_postgres_time(s: String) -> Result(Int, Nil) {
  let base = case string.split(s, ".") {
    [b, ..] -> b
    [] -> s
  }
  case birl.from_naive(base) {
    Error(_) -> Error(Nil)
    Ok(t) -> {
      let back =
        birl.to_naive_date_string(t)
        <> " "
        <> string.slice(birl.to_naive_time_string(t), 0, 8)
      case back == base {
        True -> Ok(birl.to_unix(t))
        False -> Error(Nil)
      }
    }
  }
}

fn duration_string(total: Int) -> String {
  case total <= 0 {
    True -> "0 seconds"
    False ->
      humanize.duration_precise(total)
      |> string.split(", ")
      |> humanize.list_with_oxford
  }
}

pub fn webhook_age_string(live_since_epoch: Int, now_epoch: Int) -> String {
  let t = birl.from_unix(live_since_epoch)
  let formatted =
    birl.to_naive_date_string(t)
    <> " "
    <> string.slice(birl.to_naive_time_string(t), 0, 8)
  let diff = case now_epoch - live_since_epoch < 0 {
    True -> 0
    False -> now_epoch - live_since_epoch
  }
  "since " <> formatted <> " (which was " <> duration_string(diff) <> " ago)"
}

fn last_seen_epoch(row: DbRow) -> Int {
  let raw = case row.last_seen_online {
    "" -> fallback_last_seen
    s -> s
  }
  case parse_postgres_time(raw) {
    Ok(t) -> t
    Error(_) -> 0
  }
}

fn should_announce(last_seen: Int, now_epoch: Int, grace_s: Int) -> Bool {
  now_epoch - last_seen >= grace_s
}

fn to_announce_entry(row: DbRow, info: StreamInfo) -> AnnounceInfo {
  AnnounceInfo(
    username: row.twitch_name,
    displayname: info.displayname,
    live: info.live,
    stream_title: info.stream_title,
    live_since: info.live_since,
    stream_category: info.stream_category,
    webhook_url: row.discord_webhook,
    announce_message: row.announce_message,
  )
}

pub fn decide(
  rows: List(DbRow),
  infos: List(StreamInfo),
  now_epoch: Int,
  grace_s: Int,
) -> #(List(String), List(String), List(String), List(AnnounceInfo)) {
  let result =
    list.fold(rows, #([], [], [], []), fn(acc, row) {
      case list.find(infos, fn(info) { info.username == row.twitch_name }) {
        Error(_) -> acc
        Ok(info) -> {
          let #(announced, online, offline, to_announce) = acc
          let offline = case row.status != "offline" && !info.live {
            True -> [row.twitch_name, ..offline]
            False -> offline
          }
          case info.live {
            False -> #(announced, online, offline, to_announce)
            True -> {
              let online = [row.twitch_name, ..online]
              let announce =
                row.status != "online"
                && should_announce(last_seen_epoch(row), now_epoch, grace_s)
              case announce {
                False -> #(announced, online, offline, to_announce)
                True -> {
                  let announced = case
                    list.contains(announced, row.twitch_name)
                  {
                    True -> announced
                    False -> [row.twitch_name, ..announced]
                  }
                  #(announced, online, offline, [
                    to_announce_entry(row, info),
                    ..to_announce
                  ])
                }
              }
            }
          }
        }
      }
    })
  #(
    list.reverse(result.0),
    list.reverse(result.1),
    list.reverse(result.2),
    list.reverse(result.3),
  )
}
