import decide
import gleam/list
import gleam/string
import gleeunit
import gleeunit/should
import twitch

pub fn main() {
  gleeunit.main()
}

fn live_info(name: String) -> decide.StreamInfo {
  decide.StreamInfo(
    username: name,
    displayname: "Alice",
    live: True,
    stream_title: "Hello",
    live_since: "2025-01-06T03:16:52Z",
    stream_category: "Games",
  )
}

fn offline_info(name: String) -> decide.StreamInfo {
  decide.StreamInfo(
    username: name,
    displayname: "",
    live: False,
    stream_title: "",
    live_since: "",
    stream_category: "",
  )
}

fn db_row(name: String, status: String, last_seen: String) -> decide.DbRow {
  decide.DbRow(
    twitch_name: name,
    discord_webhook: "https://hooks.example/1",
    announce_message: "is live!",
    status: status,
    last_seen_online: last_seen,
  )
}

pub fn offline_to_online_announces_test() {
  let result =
    decide.decide(
      [db_row("alice", "offline", "2000-01-01 01:01:01.000000")],
      [live_info("alice")],
      1_736_133_412,
      1800,
    )
  should.equal(result.0, ["alice"])
  should.equal(result.1, ["alice"])
  should.equal(result.2, [])
  should.equal(result.3, [
    decide.AnnounceInfo(
      username: "alice",
      displayname: "Alice",
      live: True,
      stream_title: "Hello",
      live_since: "2025-01-06T03:16:52Z",
      stream_category: "Games",
      webhook_url: "https://hooks.example/1",
      announce_message: "is live!",
    ),
  ])
}

pub fn recent_seen_suppresses_announce_but_marks_online_test() {
  let result =
    decide.decide(
      [db_row("alice", "offline", "2025-01-06 03:16:00")],
      [live_info("alice")],
      1_736_133_412,
      1800,
    )
  should.equal(result.0, [])
  should.equal(result.1, ["alice"])
  should.equal(result.2, [])
  should.equal(result.3, [])
}

pub fn online_to_offline_test() {
  let result =
    decide.decide(
      [db_row("bob", "online", "2025-01-06 03:16:00")],
      [offline_info("bob")],
      1_736_133_412,
      1800,
    )
  should.equal(result.0, [])
  should.equal(result.1, [])
  should.equal(result.2, ["bob"])
  should.equal(result.3, [])
}

pub fn stays_offline_no_action_test() {
  let result =
    decide.decide(
      [db_row("bob", "offline", "2000-01-01 01:01:01.000000")],
      [offline_info("bob")],
      1_736_133_412,
      1800,
    )
  should.equal(result, #([], [], [], []))
}

pub fn unknown_name_skipped_test() {
  let result =
    decide.decide(
      [db_row("carol", "offline", "2000-01-01 01:01:01.000000")],
      [live_info("alice")],
      1_736_133_412,
      1800,
    )
  should.equal(result, #([], [], [], []))
}

pub fn empty_last_seen_falls_back_to_announce_test() {
  let result =
    decide.decide(
      [db_row("alice", "offline", "")],
      [live_info("alice")],
      1_736_133_412,
      1800,
    )
  should.equal(result.0, ["alice"])
  should.equal(result.1, ["alice"])
}

pub fn already_online_live_stays_quiet_test() {
  let result =
    decide.decide(
      [db_row("alice", "online", "2025-01-06 03:16:00")],
      [live_info("alice")],
      1_736_133_412,
      1800,
    )
  should.equal(result.0, [])
  should.equal(result.1, ["alice"])
  should.equal(result.2, [])
  should.equal(result.3, [])
}

pub fn parse_twitch_time_test() {
  decide.parse_twitch_time("2025-01-06T03:16:52Z")
  |> should.equal(Ok(1_736_133_412))
  decide.parse_twitch_time("not-a-time") |> should.equal(Error(Nil))
  decide.parse_twitch_time("2025-01-06 03:16:52") |> should.equal(Error(Nil))
}

pub fn parse_postgres_time_test() {
  decide.parse_postgres_time("2025-01-06 01:44:43.123456789")
  |> should.equal(Ok(1_736_127_883))
  decide.parse_postgres_time("2025-01-06 01:44:43")
  |> should.equal(Ok(1_736_127_883))
  decide.parse_postgres_time("junk") |> should.equal(Error(Nil))
}

pub fn webhook_age_string_test() {
  decide.webhook_age_string(1_736_127_883, 1_736_127_883 + 3661)
  |> should.equal(
    "since 2025-01-06 01:44:43 (which was 1 hour, 1 minute, and 1 second ago)",
  )
  should.equal(
    string.contains(
      decide.webhook_age_string(1_736_127_883, 1_736_127_883),
      "0 seconds ago",
    ),
    True,
  )
}

pub fn chunks_nonpositive_size_returns_empty_test() {
  twitch.chunks(["alice", "bob"], 0) |> should.equal([])
  twitch.chunks(["alice", "bob"], -1) |> should.equal([])
}

pub fn grace_boundary_equal_announces_test() {
  let result =
    decide.decide(
      [db_row("alice", "offline", "2025-01-06 02:46:52")],
      [live_info("alice")],
      1_736_133_412,
      1800,
    )
  should.equal(result.0, ["alice"])
  should.equal(result.1, ["alice"])
  should.equal(list.length(result.3), 1)
}

pub fn invalid_last_seen_and_duplicate_rows_announce_test() {
  let result =
    decide.decide(
      [db_row("alice", "offline", "junk"), db_row("alice", "offline", "junk")],
      [live_info("alice")],
      1_736_133_412,
      1800,
    )
  should.equal(result.0, ["alice"])
  should.equal(result.1, ["alice", "alice"])
  should.equal(list.length(result.3), 2)
}
