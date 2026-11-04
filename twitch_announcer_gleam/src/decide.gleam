//// Pure decision and time logic for this Gleam port.
//// Exposes decide plus Twitch/Postgres time parsing and age
//// formatting; performs no I/O or env reads by design.
//// All database and webhook side effects live in main.

import birl
import gleam/dict
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

fn check_roundtrip(
  parsed: birl.Time,
  formatted: String,
  original: String,
) -> Result(Int, Nil) {
  case formatted == original {
    True -> Ok(birl.to_unix(parsed))
    False -> Error(Nil)
  }
}

pub fn format_naive(t: birl.Time) -> String {
  birl.to_naive_date_string(t)
  <> " "
  <> string.slice(birl.to_naive_time_string(t), 0, 8)
}

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
          check_roundtrip(t, back, s)
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
      let back = format_naive(t)
      check_roundtrip(t, back, base)
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
  let formatted = format_naive(t)
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

fn distinct_rows(rows: List(DbRow)) -> List(DbRow) {
  let #(deduped_rev, _) =
    list.fold(rows, #([], dict.new()), fn(acc, row) {
      let #(deduped, seen) = acc
      case dict.has_key(seen, row.twitch_name) {
        True -> acc
        False -> #([row, ..deduped], dict.insert(seen, row.twitch_name, Nil))
      }
    })
  list.reverse(deduped_rev)
}

pub fn decide(
  rows: List(DbRow),
  infos: List(StreamInfo),
  now_epoch: Int,
  grace_s: Int,
) -> #(List(String), List(String), List(String), List(AnnounceInfo)) {
  let by_name =
    dict.from_list(list.map(infos, fn(info) { #(info.username, info) }))
  let joined =
    list.filter_map(distinct_rows(rows), fn(row) {
      case dict.get(by_name, row.twitch_name) {
        Ok(info) -> Ok(#(row, info))
        Error(_) -> Error(Nil)
      }
    })
  let #(online_rev, offline_rev, to_announce_rev) =
    list.fold(joined, #([], [], []), fn(acc, pair) {
      let #(row, info) = pair
      let #(online, offline, to_announce) = acc
      let online = case info.live {
        True -> [row.twitch_name, ..online]
        False -> online
      }
      let offline = case row.status != "offline" && !info.live {
        True -> [row.twitch_name, ..offline]
        False -> offline
      }
      let to_announce = case
        info.live
        && row.status != "online"
        && should_announce(last_seen_epoch(row), now_epoch, grace_s)
      {
        True -> [to_announce_entry(row, info), ..to_announce]
        False -> to_announce
      }
      #(online, offline, to_announce)
    })
  let online = list.reverse(online_rev)
  let offline = list.reverse(offline_rev)
  let to_announce = list.reverse(to_announce_rev)
  let announced = list.unique(list.map(to_announce, fn(a) { a.username }))
  #(announced, online, offline, to_announce)
}
