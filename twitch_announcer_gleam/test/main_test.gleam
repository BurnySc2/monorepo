import birl
import decide
import gleam/int
import gleam/list
import gleam/string
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
    [date, clock] ->
      case string.split(date, "-"), string.split(clock, ":") {
        [y, mo, d], [h, mi, s] ->
          string.length(y) == 4
          && string.length(mo) == 2
          && string.length(d) == 2
          && string.length(h) == 2
          && string.length(mi) == 2
          && string.length(s) == 2
          && all_digits(y)
          && all_digits(mo)
          && all_digits(d)
          && all_digits(h)
          && all_digits(mi)
          && all_digits(s)
        _, _ -> False
      }
    _ -> False
  }
}

pub fn db_timestamp_format_test() {
  let ts = decide.format_naive(birl.now())
  should.equal(is_db_timestamp(ts), True)
  should.equal(string.contains(ts, "T"), False)
  should.equal(string.contains(ts, "Z"), False)
  should.equal(string.length(ts), 19)
}

pub fn grace_parse_valid_test() {
  main.parse_grace_seconds("30") |> should.equal(30)
}

pub fn grace_parse_garbage_defaults_test() {
  main.parse_grace_seconds("abc") |> should.equal(1800)
  main.parse_grace_seconds("-1") |> should.equal(1800)
  main.parse_grace_seconds("") |> should.equal(1800)
  main.parse_grace_seconds(" 30 ") |> should.equal(1800)
}
