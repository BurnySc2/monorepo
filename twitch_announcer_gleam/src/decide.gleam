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

fn is_leap_year(year: Int) -> Bool {
  year % 4 == 0 && { year % 100 != 0 || year % 400 == 0 }
}

fn days_in_month(year: Int, month: Int) -> Int {
  case month {
    2 ->
      case is_leap_year(year) {
        True -> 29
        False -> 28
      }
    4 | 6 | 9 | 11 -> 30
    _ -> 31
  }
}

fn valid_date(year: Int, month: Int, day: Int) -> Bool {
  month >= 1 && month <= 12 && day >= 1 && day <= days_in_month(year, month)
}

fn parse_date(date: String) -> Result(#(Int, Int, Int), Nil) {
  case string.split(date, "-") {
    [y, mo, d] ->
      case int.parse(y), int.parse(mo), int.parse(d) {
        Ok(year), Ok(month), Ok(day) ->
          case valid_date(year, month, day) {
            True -> Ok(#(year, month, day))
            False -> Error(Nil)
          }
        _, _, _ -> Error(Nil)
      }
    _ -> Error(Nil)
  }
}

fn parse_clock(time: String) -> Result(#(Int, Int, Int), Nil) {
  case string.split(time, ":") {
    [h, mi, s] ->
      case int.parse(h), int.parse(mi), int.parse(s) {
        Ok(hour), Ok(minute), Ok(second) ->
          case
            hour >= 0
            && hour <= 23
            && minute >= 0
            && minute <= 59
            && second >= 0
            && second <= 59
          {
            True -> Ok(#(hour, minute, second))
            False -> Error(Nil)
          }
        _, _, _ -> Error(Nil)
      }
    _ -> Error(Nil)
  }
}

fn days_from_civil(year: Int, month: Int, day: Int) -> Int {
  let y = case month <= 2 {
    True -> year - 1
    False -> year
  }
  let era = y / 400
  let yoe = y - era * 400
  let mp = case month > 2 {
    True -> month - 3
    False -> month + 9
  }
  let doy = { 153 * mp + 2 } / 5 + day - 1
  let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy
  era * 146_097 + doe - 719_468
}

fn to_epoch(
  year: Int,
  month: Int,
  day: Int,
  hour: Int,
  min: Int,
  sec: Int,
) -> Int {
  days_from_civil(year, month, day) * 86_400 + hour * 3600 + min * 60 + sec
}

pub fn parse_twitch_time(s: String) -> Result(Int, Nil) {
  case string.split(s, "T") {
    [date, time_z] ->
      case string.ends_with(time_z, "Z") {
        True -> {
          let time = string.slice(time_z, 0, string.length(time_z) - 1)
          case parse_date(date), parse_clock(time) {
            Ok(#(year, month, day)), Ok(#(hour, min, sec)) ->
              Ok(to_epoch(year, month, day, hour, min, sec))
            _, _ -> Error(Nil)
          }
        }
        False -> Error(Nil)
      }
    _ -> Error(Nil)
  }
}

pub fn parse_postgres_time(s: String) -> Result(Int, Nil) {
  let base = case string.split(s, ".") {
    [b, ..] -> b
    [] -> s
  }
  case string.split(base, " ") {
    [date, time] ->
      case parse_date(date), parse_clock(time) {
        Ok(#(year, month, day)), Ok(#(hour, min, sec)) ->
          Ok(to_epoch(year, month, day, hour, min, sec))
        _, _ -> Error(Nil)
      }
    _ -> Error(Nil)
  }
}

fn civil_from_days(z_in: Int) -> #(Int, Int, Int) {
  let z = z_in + 719_468
  let era = z / 146_097
  let doe = z - era * 146_097
  let yoe = { doe - doe / 1460 + doe / 36_524 - doe / 146_096 } / 365
  let y = yoe + era * 400
  let doy = doe - { 365 * yoe + yoe / 4 - yoe / 100 }
  let mp = { 5 * doy + 2 } / 153
  let d = doy - { 153 * mp + 2 } / 5 + 1
  let m = case mp < 10 {
    True -> mp + 3
    False -> mp - 9
  }
  let year = case m <= 2 {
    True -> y + 1
    False -> y
  }
  #(year, m, d)
}

fn pad2(n: Int) -> String {
  case n < 10 {
    True -> "0" <> int.to_string(n)
    False -> int.to_string(n)
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
  let days = total / 86_400
  let hours = { total - days * 86_400 } / 3600
  let minutes = { total - days * 86_400 - hours * 3600 } / 60
  let seconds = total - days * 86_400 - hours * 3600 - minutes * 60
  let texts =
    list.filter_map(
      [
        #(days, "day"),
        #(hours, "hour"),
        #(minutes, "minute"),
        #(seconds, "second"),
      ],
      fn(p) {
        case p.0 {
          0 -> Error(Nil)
          n -> Ok(plural(n, p.1))
        }
      },
    )
  case texts {
    [] -> "0 seconds"
    _ -> join_human(texts)
  }
}

pub fn webhook_age_string(live_since_epoch: Int, now_epoch: Int) -> String {
  let days = live_since_epoch / 86_400
  let rem = live_since_epoch - days * 86_400
  let #(year, month, day) = civil_from_days(days)
  let formatted =
    int.to_string(year)
    <> "-"
    <> pad2(month)
    <> "-"
    <> pad2(day)
    <> " "
    <> pad2(rem / 3600)
    <> ":"
    <> pad2({ rem - rem / 3600 * 3600 } / 60)
    <> ":"
    <> pad2(rem - rem / 3600 * 3600 - { rem - rem / 3600 * 3600 } / 60 * 60)
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
