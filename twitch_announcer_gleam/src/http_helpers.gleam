//// Shared HTTP send + status check for twitch/discord clients.
//// Centralizes httpc error mapping so callers stay focused on APIs.
//// Named http_helpers to avoid OTP http_util module collision.
//// Used by twitch token/stream fetches and discord webhook posts.

import gleam/http
import gleam/http/request
import gleam/http/response
import gleam/httpc
import gleam/int
import gleam/result
import gleam/string

pub fn send(
  req: request.Request(String),
) -> Result(response.Response(String), String) {
  httpc.send(req) |> result.map_error(string.inspect)
}

pub fn require_status(
  resp: response.Response(String),
  ok: fn(Int) -> Bool,
  on_error: fn(Int) -> String,
) -> Result(response.Response(String), String) {
  case ok(resp.status) {
    True -> Ok(resp)
    False -> Error(on_error(resp.status))
  }
}

pub fn post_json(url: String, body: String) -> Result(Nil, String) {
  use req <- result.try(
    request.to(url)
    |> result.replace_error("invalid webhook url: " <> url),
  )
  let req =
    req
    |> request.set_method(http.Post)
    |> request.set_header("content-type", "application/json")
    |> request.set_body(body)
  use resp <- result.try(send(req))
  use _ <- result.try(
    require_status(
      resp,
      fn(status) { status >= 200 && status < 300 },
      fn(status) {
        "Status: "
        <> int.to_string(status)
        <> ", url: "
        <> url
        <> ", announce_message: "
        <> body
      },
    ),
  )
  Ok(Nil)
}
