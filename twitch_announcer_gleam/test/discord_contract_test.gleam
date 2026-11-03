import decide
import discord
import gleam/json
import gleam/string
import gleeunit/should

// Fixed fixture: no birl.now(), fully deterministic snapshot input.
fn fixed_announce() -> decide.AnnounceInfo {
  decide.AnnounceInfo(
    username: "alice",
    displayname: "Alice",
    live: True,
    stream_title: "Hello",
    live_since: "2025-01-06T03:16:52Z",
    stream_category: "Games",
    webhook_url: "https://example.invalid",
    announce_message: "@here Alice live",
  )
}

fn fixed_age() -> String {
  "since 2025-01-06 03:16:52 (which was 1 hour ago)"
}

pub fn discord_payload_golden_test() {
  let payload =
    discord.build_payload(fixed_announce(), fixed_age())
    |> json.to_string
  let golden =
    "{\"username\":\"Stream Announcer Webhook\",\"content\":\"@here Alice live\",\"embeds\":[{\"title\":\"Alice is now live on Twitch!\",\"url\":\"https://www.twitch.tv/alice\",\"fields\":[{\"name\":\"Stream title\",\"value\":\"Hello\"},{\"name\":\"Playing 'Games'\",\"value\":\"since 2025-01-06 03:16:52 (which was 1 hour ago)\"}]}]}"
  should.equal(payload, golden)
}

pub fn discord_age_valid_time_test() {
  // 2025-01-06T03:16:52Z parses to 1_736_133_412 (see decide_test).
  let now = 1_736_133_412 + 3661
  discord.age_string_for(fixed_announce(), now)
  |> should.equal(decide.webhook_age_string(1_736_133_412, now))
}

pub fn discord_age_invalid_time_fallback_test() {
  let broken = decide.AnnounceInfo(..fixed_announce(), live_since: "")
  let age = discord.age_string_for(broken, 1_736_133_412)
  should.equal(age, "since ")
  should.equal(string.starts_with(age, "since "), True)
}
