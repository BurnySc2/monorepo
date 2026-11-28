import gleeunit/should
import twitch

// (a) Full live Helix entry with all decoded optionals present.
fn full_live_body() -> String {
  "{\"data\": [{\"user_login\": \"alice\", \"user_name\": \"Alice\", \"type\": \"live\", \"title\": \"Hello\", \"game_name\": \"Games\", \"started_at\": \"2025-01-06T03:16:52Z\"}]}"
}

// (b) Same entry with title/game_name/started_at keys absent.
fn missing_optionals_body() -> String {
  "{\"data\": [{\"user_login\": \"alice\", \"user_name\": \"Alice\", \"type\": \"live\"}]}"
}

// (c) Same entry with those keys explicit null.
fn null_optionals_body() -> String {
  "{\"data\": [{\"user_login\": \"alice\", \"user_name\": \"Alice\", \"type\": \"live\", \"title\": null, \"game_name\": null, \"started_at\": null}]}"
}

// Minimal offline entry: empty type means not live.
fn empty_type_body() -> String {
  "{\"data\": [{\"user_login\": \"alice\", \"user_name\": \"Alice\", \"type\": \"\"}]}"
}

pub fn helix_missing_optionals_default_empty_test() {
  case twitch.parse_streams_json(missing_optionals_body()) {
    Ok([info]) -> {
      should.equal(info.live, True)
      should.equal(info.stream_title, "")
      should.equal(info.stream_category, "")
      should.equal(info.live_since, "")
    }
    _ -> should.fail()
  }
}

// Contract: explicit null optionals currently fail the strict string
// decoder, so parse_streams_json returns Error. If the decoder ever
// tolerates null, update this test to assert "" defaults instead.
pub fn helix_null_optionals_contract_test() {
  twitch.parse_streams_json(null_optionals_body())
  |> should.be_error
}

pub fn helix_type_live_vs_empty_test() {
  case twitch.parse_streams_json(full_live_body()) {
    Ok([info]) -> should.equal(info.live, True)
    _ -> should.fail()
  }
  case twitch.parse_streams_json(empty_type_body()) {
    Ok([info]) -> should.equal(info.live, False)
    _ -> should.fail()
  }
}
