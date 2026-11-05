import decide.{StreamInfo}
import gleam/dict
import gleam/int
import gleam/list
import gleeunit/should
import twitch

fn names(n: Int) -> List(String) {
  range_loop(0, n, [])
}

fn range_loop(i: Int, n: Int, acc: List(String)) -> List(String) {
  case i >= n {
    True -> list.reverse(acc)
    False -> range_loop(i + 1, n, [int.to_string(i), ..acc])
  }
}

pub fn chunks_21_splits_20_plus_1_test() {
  let result = twitch.chunks(names(21), 20)
  should.equal(list.length(result), 2)
  should.equal(list.map(result, list.length), [20, 1])
}

pub fn normalize_names_lowercases_test() {
  twitch.normalize_names(["Alice", "BOB", "cHaRlIe"])
  |> should.equal(["alice", "bob", "charlie"])
}

pub fn merge_infos_offline_default_test() {
  let live =
    StreamInfo(
      username: "alice",
      displayname: "Alice",
      live: True,
      stream_title: "Hello",
      live_since: "2025-01-06T03:16:52Z",
      stream_category: "Games",
    )
  let merged = twitch.merge_infos(["alice", "bob"], [live])
  should.equal(dict.size(merged), 2)
  should.equal(dict.get(merged, "alice"), Ok(live))
  should.equal(
    dict.get(merged, "bob"),
    Ok(StreamInfo(
      username: "bob",
      displayname: "",
      live: False,
      stream_title: "",
      live_since: "",
      stream_category: "",
    )),
  )
}

pub fn strict_decoder_rejects_missing_user_login_test() {
  twitch.parse_streams_json(
    "{\"data\": [{\"user_name\": \"Alice\", \"type\": \"live\"}]}",
  )
  |> should.be_error
}

pub fn empty_type_means_offline_test() {
  let body =
    "{\"data\": [{\"user_login\": \"alice\", \"user_name\": \"Alice\", \"type\": \"\"}]}"
  case twitch.parse_streams_json(body) {
    Ok([info]) -> should.equal(info.live, False)
    _ -> should.fail()
  }
}
