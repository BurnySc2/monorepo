import decide.{type StreamInfo, StreamInfo}
import gleam/dict.{type Dict}
import gleam/dynamic/decode
import gleam/http
import gleam/http/request
import gleam/int
import gleam/json
import gleam/list
import gleam/result
import gleam/string
import gleam/uri
import http_helpers

// WHY helix-logins-lowercase: Twitch user_login values are lowercase-only, Nim asserts/toLowers at fetch site — see main.nim get_twitch_info_for_20/get_twitch_infos.

fn token_decoder() -> decode.Decoder(String) {
  use token <- decode.field("access_token", decode.string)
  decode.success(token)
}

pub fn get_access_token(
  client_id: String,
  client_secret: String,
) -> Result(String, String) {
  let body =
    "client_id="
    <> uri.percent_encode(client_id)
    <> "&client_secret="
    <> uri.percent_encode(client_secret)
    <> "&grant_type=client_credentials"
  use req <- result.try(
    request.to("https://id.twitch.tv/oauth2/token")
    |> result.replace_error("invalid token url"),
  )
  let req =
    req
    |> request.set_method(http.Post)
    |> request.set_header("content-type", "application/x-www-form-urlencoded")
    |> request.set_body(body)
  use resp <- result.try(http_helpers.send(req))
  use resp <- result.try(
    http_helpers.require_status(resp, fn(status) { status == 200 }, fn(status) {
      "token request status: " <> int.to_string(status)
    }),
  )
  json.parse(resp.body, token_decoder())
  |> result.map_error(string.inspect)
}

fn stream_entry_decoder() -> decode.Decoder(StreamInfo) {
  use user_login <- decode.field("user_login", decode.string)
  use user_name <- decode.field("user_name", decode.string)
  use stream_type <- decode.field("type", decode.string)
  use title <- decode.optional_field("title", "", decode.string)
  use started_at <- decode.optional_field("started_at", "", decode.string)
  use game_name <- decode.optional_field("game_name", "", decode.string)
  decode.success(StreamInfo(
    username: user_login,
    displayname: user_name,
    live: stream_type == "live",
    stream_title: title,
    live_since: started_at,
    stream_category: game_name,
  ))
}

fn streams_decoder() -> decode.Decoder(List(StreamInfo)) {
  use data <- decode.field("data", decode.list(stream_entry_decoder()))
  decode.success(data)
}

pub fn offline_info(name: String) -> StreamInfo {
  StreamInfo(
    username: name,
    displayname: "",
    live: False,
    stream_title: "",
    live_since: "",
    stream_category: "",
  )
}

pub fn normalize_names(names: List(String)) -> List(String) {
  list.map(names, string.lowercase)
}

pub fn merge_infos(
  batch: List(String),
  live_infos: List(StreamInfo),
) -> Dict(String, StreamInfo) {
  let base =
    list.fold(batch, dict.new(), fn(acc, name) {
      dict.insert(acc, name, offline_info(name))
    })
  list.fold(live_infos, base, fn(acc, info) {
    dict.insert(acc, info.username, info)
  })
}

pub fn parse_streams_json(body: String) -> Result(List(StreamInfo), String) {
  json.parse(body, streams_decoder())
  |> result.map_error(string.inspect)
}

fn fetch_batch(
  batch: List(String),
  token: String,
  client_id: String,
) -> Result(Dict(String, StreamInfo), String) {
  let query =
    list.map(batch, fn(name) { #("user_login", name) }) |> uri.query_to_string
  use req <- result.try(
    request.to("https://api.twitch.tv/helix/streams?" <> query)
    |> result.replace_error("invalid streams url"),
  )
  let req =
    req
    |> request.set_header("authorization", "Bearer " <> token)
    |> request.set_header("client-id", client_id)
  use resp <- result.try(http_helpers.send(req))
  use resp <- result.try(
    http_helpers.require_status(resp, fn(status) { status == 200 }, fn(status) {
      "streams request status: " <> int.to_string(status)
    }),
  )
  use live_infos <- result.try(
    json.parse(resp.body, streams_decoder())
    |> result.map_error(string.inspect),
  )
  Ok(merge_infos(batch, live_infos))
}

pub fn chunks(names: List(String), size: Int) -> List(List(String)) {
  case size <= 0 {
    True -> []
    False ->
      case names {
        [] -> []
        _ -> {
          let #(head, tail) = list.split(names, size)
          case head {
            [] -> chunks(tail, size)
            _ -> [head, ..chunks(tail, size)]
          }
        }
      }
  }
}

pub fn get_stream_infos(
  names: List(String),
  token: String,
  client_id: String,
) -> Result(Dict(String, StreamInfo), String) {
  let lowered = normalize_names(names)
  use batches <- result.try(Ok(chunks(lowered, 20)))
  list.fold(batches, Ok(dict.new()), fn(acc, batch) {
    use done <- result.try(acc)
    use got <- result.try(fetch_batch(batch, token, client_id))
    Ok(dict.merge(done, got))
  })
}
