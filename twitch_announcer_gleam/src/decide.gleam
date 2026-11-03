import birl
import birl/duration
import gleam/int
import gleam/list
import gleam/string

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

fn plural(n: Int, word: String) -> String {
  case n {
    1 -> "1 " <> word
    _ -> int.to_string(n) <> " " <> word <> "s"
  }
}

fn join_human(parts: List(String)) -> String {
  case list.reverse(parts) {
    [] -> ""
    [single] -> single
    [last, ..rest_reversed] -> {
      let head = string.join(list.reverse(rest_reversed), ", ")
      case rest_reversed {
        [_] -> head <> " and " <> last
        _ -> head <> ", and " <> last
      }
    }
  }
}

fn duration_string(total: Int) -> String {
  let parts =
    birl.difference(birl.from_unix(0), birl.from_unix(total))
    |> duration.decompose
    |> list.filter_map(fn(p) {
      case p {
        #(n, duration.Day) -> Ok(plural(n, "day"))
        #(n, duration.Hour) -> Ok(plural(n, "hour"))
        #(n, duration.Minute) -> Ok(plural(n, "minute"))
        #(n, duration.Second) -> Ok(plural(n, "second"))
        _ -> Error(Nil)
      }
    })
  case parts {
    [] -> "0 seconds"
    _ -> join_human(parts)
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

fn maybe_announce(
  acc: #(List(String), List(String), List(String), List(AnnounceInfo)),
  row: DbRow,
  info: StreamInfo,
  now_epoch: Int,
  grace_s: Int,
) -> #(List(String), List(String), List(String), List(AnnounceInfo)) {
  let #(announced, online, offline, to_announce) = acc
  let raw = case row.last_seen_online {
    "" -> fallback_last_seen
    s -> s
  }
  let last_seen = case parse_postgres_time(raw) {
    Ok(t) -> t
    Error(_) -> 0
  }
  case now_epoch - last_seen < grace_s {
    True -> acc
    False -> {
      let announced = case list.contains(announced, row.twitch_name) {
        True -> announced
        False -> [row.twitch_name, ..announced]
      }
      let entry =
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
      #(announced, online, offline, [entry, ..to_announce])
    }
  }
}

fn decide_row(
  acc: #(List(String), List(String), List(String), List(AnnounceInfo)),
  row: DbRow,
  infos: List(StreamInfo),
  now_epoch: Int,
  grace_s: Int,
) -> #(List(String), List(String), List(String), List(AnnounceInfo)) {
  let #(announced, online, offline, to_announce) = acc
  case list.find(infos, fn(info) { info.username == row.twitch_name }) {
    Error(_) -> acc
    Ok(info) -> {
      let offline = case row.status != "offline" && info.live == False {
        True -> [row.twitch_name, ..offline]
        False -> offline
      }
      case info.live {
        False -> #(announced, online, offline, to_announce)
        True -> {
          let online = [row.twitch_name, ..online]
          case row.status == "online" {
            True -> #(announced, online, offline, to_announce)
            False ->
              maybe_announce(
                #(announced, online, offline, to_announce),
                row,
                info,
                now_epoch,
                grace_s,
              )
          }
        }
      }
    }
  }
}

pub fn decide(
  rows: List(DbRow),
  infos: List(StreamInfo),
  now_epoch: Int,
  grace_s: Int,
) -> #(List(String), List(String), List(String), List(AnnounceInfo)) {
  let result =
    list.fold(rows, #([], [], [], []), fn(acc, row) {
      decide_row(acc, row, infos, now_epoch, grace_s)
    })
  #(
    list.reverse(result.0),
    list.reverse(result.1),
    list.reverse(result.2),
    list.reverse(result.3),
  )
}
