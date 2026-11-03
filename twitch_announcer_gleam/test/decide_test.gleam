import decide
import gleam/list
import gleam/string
import gleeunit/should
import twitch

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
  // Strict Z-only: offsets and lowercase z rejected (birl is lenient here).
  decide.parse_twitch_time("2025-01-06T03:16:52+00:00")
  |> should.equal(Error(Nil))
  decide.parse_twitch_time("2025-01-06T03:16:52z") |> should.equal(Error(Nil))
}

pub fn parse_postgres_time_test() {
  decide.parse_postgres_time("2025-01-06 01:44:43.123456789")
  |> should.equal(Ok(1_736_127_883))
  decide.parse_postgres_time("2025-01-06 01:44:43")
  |> should.equal(Ok(1_736_127_883))
  decide.parse_postgres_time("junk") |> should.equal(Error(Nil))
  decide.parse_postgres_time("2024-02-29 12:00:00")
  |> should.equal(Ok(1_709_208_000))
  decide.parse_postgres_time("2025-02-30 12:00:00")
  |> should.equal(Error(Nil))
  decide.parse_postgres_time("2025-01-06 25:00:00") |> should.equal(Error(Nil))
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
  // Singular 1 second.
  decide.webhook_age_string(0, 1)
  |> should.equal("since 1970-01-01 00:00:00 (which was 1 second ago)")
  // Plural 2 seconds.
  decide.webhook_age_string(0, 2)
  |> should.equal("since 1970-01-01 00:00:00 (which was 2 seconds ago)")
  // Negative diff clamps to zero.
  decide.webhook_age_string(100, 50)
  |> should.equal("since 1970-01-01 00:01:40 (which was 0 seconds ago)")
  // Midnight zero-pad.
  decide.webhook_age_string(1_736_121_907, 1_736_121_907)
  |> should.equal("since 2025-01-06 00:05:07 (which was 0 seconds ago)")
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

// Z-strictness vectors: strict Z-only vs birl leniency.

pub fn parse_twitch_time_valid_z_ok_test() {
  decide.parse_twitch_time("2025-01-06T03:16:52Z")
  |> should.equal(Ok(1_736_133_412))
}

pub fn parse_twitch_time_offset_plus_rejected_test() {
  decide.parse_twitch_time("2025-01-06T03:16:52+00:00")
  |> should.equal(Error(Nil))
}

pub fn parse_twitch_time_lowercase_z_rejected_test() {
  decide.parse_twitch_time("2025-01-06T03:16:52z") |> should.equal(Error(Nil))
}

pub fn parse_twitch_time_missing_z_rejected_test() {
  decide.parse_twitch_time("2025-01-06T03:16:52") |> should.equal(Error(Nil))
}

pub fn parse_twitch_time_space_separator_rejected_test() {
  decide.parse_twitch_time("2025-01-06 03:16:52") |> should.equal(Error(Nil))
}

pub fn parse_twitch_time_not_a_time_rejected_test() {
  decide.parse_twitch_time("not-a-time") |> should.equal(Error(Nil))
}

pub fn parse_twitch_time_empty_rejected_test() {
  decide.parse_twitch_time("") |> should.equal(Error(Nil))
}

pub fn parse_twitch_time_invalid_feb30_rejected_test() {
  decide.parse_twitch_time("2025-02-30T12:00:00Z") |> should.equal(Error(Nil))
}

pub fn parse_twitch_time_invalid_hour_rejected_test() {
  decide.parse_twitch_time("2025-01-06T25:00:00Z") |> should.equal(Error(Nil))
}

pub fn parse_twitch_time_leap_day_ok_test() {
  decide.parse_twitch_time("2024-02-29T12:00:00Z")
  |> should.equal(Ok(1_709_208_000))
}

pub fn parse_twitch_time_non_leap_feb29_rejected_test() {
  decide.parse_twitch_time("2025-02-29T12:00:00Z") |> should.equal(Error(Nil))
}

// Postgres vectors.

pub fn parse_postgres_time_fractional_equals_bare_test() {
  decide.parse_postgres_time("2025-01-06 01:44:43.123456789")
  |> should.equal(decide.parse_postgres_time("2025-01-06 01:44:43"))
}

pub fn parse_postgres_time_leap_day_ok_test() {
  decide.parse_postgres_time("2024-02-29 12:00:00")
  |> should.equal(Ok(1_709_208_000))
}

pub fn parse_postgres_time_feb30_rejected_test() {
  decide.parse_postgres_time("2025-02-30 12:00:00") |> should.equal(Error(Nil))
}

pub fn parse_postgres_time_hour25_rejected_test() {
  decide.parse_postgres_time("2025-01-06 25:00:00") |> should.equal(Error(Nil))
}

pub fn parse_postgres_time_junk_rejected_test() {
  decide.parse_postgres_time("junk") |> should.equal(Error(Nil))
}

pub fn parse_postgres_time_empty_rejected_test() {
  decide.parse_postgres_time("") |> should.equal(Error(Nil))
}

pub fn parse_postgres_time_midnight_ok_test() {
  decide.parse_postgres_time("2025-01-06 00:00:00")
  |> should.equal(Ok(1_736_121_600))
}

pub fn parse_postgres_time_invalid_minute_rejected_test() {
  decide.parse_postgres_time("2025-01-06 12:60:00") |> should.equal(Error(Nil))
}

pub fn parse_postgres_time_trailing_fraction_zero_test() {
  decide.parse_postgres_time("2025-01-06 01:44:43.000000")
  |> should.equal(Ok(1_736_127_883))
}

// Webhook age vectors: singular/plural, Oxford comma, clamp, zero-pad.

pub fn webhook_age_zero_seconds_exact_test() {
  decide.webhook_age_string(0, 0)
  |> should.equal("since 1970-01-01 00:00:00 (which was 0 seconds ago)")
}

pub fn webhook_age_one_second_singular_test() {
  decide.webhook_age_string(0, 1)
  |> should.equal("since 1970-01-01 00:00:00 (which was 1 second ago)")
}

pub fn webhook_age_two_seconds_plural_test() {
  decide.webhook_age_string(0, 2)
  |> should.equal("since 1970-01-01 00:00:00 (which was 2 seconds ago)")
}

pub fn webhook_age_one_minute_singular_test() {
  decide.webhook_age_string(0, 60)
  |> should.equal("since 1970-01-01 00:00:00 (which was 1 minute ago)")
}

pub fn webhook_age_two_minutes_plural_test() {
  decide.webhook_age_string(0, 120)
  |> should.equal("since 1970-01-01 00:00:00 (which was 2 minutes ago)")
}

pub fn webhook_age_one_hour_singular_test() {
  decide.webhook_age_string(0, 3600)
  |> should.equal("since 1970-01-01 00:00:00 (which was 1 hour ago)")
}

pub fn webhook_age_two_hours_plural_test() {
  decide.webhook_age_string(0, 7200)
  |> should.equal("since 1970-01-01 00:00:00 (which was 2 hours ago)")
}

pub fn webhook_age_one_day_singular_test() {
  decide.webhook_age_string(0, 86_400)
  |> should.equal("since 1970-01-01 00:00:00 (which was 1 day ago)")
}

pub fn webhook_age_two_days_plural_test() {
  decide.webhook_age_string(0, 172_800)
  |> should.equal("since 1970-01-01 00:00:00 (which was 2 days ago)")
}

pub fn webhook_age_two_parts_and_test() {
  decide.webhook_age_string(0, 61)
  |> should.equal(
    "since 1970-01-01 00:00:00 (which was 1 minute and 1 second ago)",
  )
}

pub fn webhook_age_three_parts_oxford_test() {
  decide.webhook_age_string(0, 3661)
  |> should.equal(
    "since 1970-01-01 00:00:00 (which was 1 hour, 1 minute, and 1 second ago)",
  )
}

pub fn webhook_age_four_parts_oxford_test() {
  decide.webhook_age_string(0, 90_061)
  |> should.equal(
    "since 1970-01-01 00:00:00 (which was 1 day, 1 hour, 1 minute, and 1 second ago)",
  )
}

pub fn webhook_age_negative_clamp_exact_test() {
  decide.webhook_age_string(100, 50)
  |> should.equal("since 1970-01-01 00:01:40 (which was 0 seconds ago)")
}

pub fn webhook_age_midnight_zero_pad_exact_test() {
  decide.webhook_age_string(1_736_121_907, 1_736_121_907)
  |> should.equal("since 2025-01-06 00:05:07 (which was 0 seconds ago)")
}

pub fn webhook_age_filters_zero_components_test() {
  decide.webhook_age_string(0, 3660)
  |> should.equal(
    "since 1970-01-01 00:00:00 (which was 1 hour and 1 minute ago)",
  )
}

pub fn webhook_age_known_timestamp_exact_test() {
  decide.webhook_age_string(1_736_127_883, 1_736_127_883 + 3661)
  |> should.equal(
    "since 2025-01-06 01:44:43 (which was 1 hour, 1 minute, and 1 second ago)",
  )
}
