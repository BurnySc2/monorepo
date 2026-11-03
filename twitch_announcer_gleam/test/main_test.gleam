import birl
import gleam/int
import gleam/list
import gleam/string
import gleam/time/calendar
import gleam/time/timestamp
import gleeunit/should
import main

fn all_digits(s: String) -> Bool {
  string.to_graphemes(s)
  |> list.all(fn(c) {
    case int.parse(c) {
      Ok(_) -> True
      Error(_) -> False
    }
  })
}

fn is_db_timestamp(ts: String) -> Bool {
  case string.split(ts, " ") {
    [date, time] ->
      case string.split(date, "-"), string.split(time, ".") {
        [y, mo, d], [clock, ms] ->
          case string.split(clock, ":") {
            [h, mi, s] ->
              string.length(y) == 4
              && string.length(mo) == 2
              && string.length(d) == 2
              && string.length(h) == 2
              && string.length(mi) == 2
              && string.length(s) == 2
              && string.length(ms) == 3
              && all_digits(y)
              && all_digits(mo)
              && all_digits(d)
              && all_digits(h)
              && all_digits(mi)
              && all_digits(s)
              && all_digits(ms)
            _ -> False
          }
        _, _ -> False
      }
    _ -> False
  }
}

fn pad2(n: Int) -> String {
  string.pad_start(int.to_string(n), to: 2, with: "0")
}

fn format_timestamp(ts: timestamp.Timestamp) -> String {
  let #(date, time) = timestamp.to_calendar(ts, calendar.utc_offset)
  int.to_string(date.year)
  <> "-"
  <> pad2(calendar.month_to_int(date.month))
  <> "-"
  <> pad2(date.day)
  <> " "
  <> pad2(time.hours)
  <> ":"
  <> pad2(time.minutes)
  <> ":"
  <> pad2(time.seconds)
  <> "."
  <> string.pad_start(
    int.to_string(time.nanoseconds / 1_000_000),
    to: 3,
    with: "0",
  )
}

fn utc_now() -> timestamp.Timestamp {
  let now = birl.now()
  timestamp.from_unix_seconds_and_nanoseconds(
    birl.to_unix(now),
    { birl.to_unix_micro(now) % 1_000_000 } * 1000,
  )
}

pub fn db_timestamp_format_test() {
  let ts = utc_now() |> format_timestamp
  should.equal(is_db_timestamp(ts), True)
  should.equal(string.contains(ts, "T"), False)
  should.equal(string.contains(ts, "Z"), False)
  should.equal(string.length(ts), 23)
}

pub fn grace_parse_valid_test() {
  main.parse_grace_seconds("30") |> should.equal(30)
}

pub fn grace_parse_negative_defaults_test() {
  main.parse_grace_seconds("-5") |> should.equal(1800)
}

pub fn grace_parse_garbage_defaults_test() {
  main.parse_grace_seconds("abc") |> should.equal(1800)
}
