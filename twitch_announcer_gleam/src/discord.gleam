import birl
import decide.{type AnnounceInfo}
import gleam/http
import gleam/http/request
import gleam/httpc
import gleam/int
import gleam/io
import gleam/json
import gleam/list
import gleam/result
import gleam/string
import kitazith/embed
import kitazith/validation
import kitazith/webhook/execute

fn build_embed(announce: AnnounceInfo, age_string: String) -> embed.Embed {
  embed.new()
  |> embed.with_title(announce.displayname <> " is now live on Twitch!")
  |> embed.with_url("https://www.twitch.tv/" <> announce.username)
  |> embed.with_fields([
    embed.new_field(name: "Stream title", value: announce.stream_title),
    embed.new_field(
      name: "Playing '" <> announce.stream_category <> "'",
      value: age_string,
    ),
  ])
}

fn execute_payload(
  announce: AnnounceInfo,
  age_string: String,
) -> execute.ExecutePayload {
  execute.new()
  |> execute.with_username("Stream Announcer Webhook")
  |> execute.with_content(announce.announce_message)
  |> execute.with_embeds([build_embed(announce, age_string)])
}

pub fn build_payload(announce: AnnounceInfo, age_string: String) -> json.Json {
  execute_payload(announce, age_string)
  |> execute.to_json
}

fn validate_payload(payload: execute.ExecutePayload) -> Result(Nil, String) {
  case execute.validate(payload) {
    Ok(_) -> Ok(Nil)
    Error(errors) ->
      Error(
        errors
        |> list.map(fn(e) { e.path <> ": " <> validation.message(e) })
        |> string.join(", "),
      )
  }
}

pub fn age_string_for(announce: AnnounceInfo, now_epoch: Int) -> String {
  case decide.parse_twitch_time(announce.live_since) {
    Ok(live_epoch) -> decide.webhook_age_string(live_epoch, now_epoch)
    Error(_) -> "since " <> announce.live_since
  }
}

fn log_one(announce: AnnounceInfo, now_epoch: Int) -> Nil {
  let body =
    build_payload(announce, age_string_for(announce, now_epoch))
    |> json.to_string
  io.println(
    "Announcing stream "
    <> announce.username
    <> " in webhook "
    <> announce.webhook_url
    <> "\n"
    <> body,
  )
}

fn post_one(announce: AnnounceInfo) -> Result(Nil, String) {
  let now_epoch = birl.now() |> birl.to_unix
  let payload = execute_payload(announce, age_string_for(announce, now_epoch))
  use _ <- result.try(validate_payload(payload))
  let body = execute.to_string(payload)
  use req <- result.try(
    request.to(announce.webhook_url)
    |> result.replace_error("invalid webhook url: " <> announce.webhook_url),
  )
  let req =
    req
    |> request.set_method(http.Post)
    |> request.set_header("content-type", "application/json")
    |> request.set_body(body)
  use resp <- result.try(httpc.send(req) |> result.map_error(string.inspect))
  case resp.status {
    status if status >= 200 && status < 300 -> Ok(Nil)
    status ->
      Error(
        "Status: "
        <> int.to_string(status)
        <> ", url: "
        <> announce.webhook_url
        <> ", announce_message: "
        <> announce.announce_message,
      )
  }
}

pub fn post_announcements(
  announces: List(AnnounceInfo),
  stage: String,
) -> Result(Nil, String) {
  case stage {
    "PROD" -> list.try_each(over: announces, with: post_one)
    _ -> {
      let now_epoch = birl.now() |> birl.to_unix
      list.each(announces, fn(announce) { log_one(announce, now_epoch) })
      Ok(Nil)
    }
  }
}
