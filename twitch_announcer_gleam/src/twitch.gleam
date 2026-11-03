//// Twitch Helix API client: OAuth client-credentials token fetch
//// plus batched live-stream lookups (20 user_logins per request).
//// Missing streams map to offline defaults; names lowercased.
////

import decide.{type StreamInfo, StreamInfo}
import flwr_oauth2/authentication as auth
import flwr_oauth2/common
import flwr_oauth2/response as oauth_resp
import flwr_oauth2/token_request
import gleam/bool
import gleam/dict.{type Dict}
import gleam/dynamic/decode
import gleam/http/request
import gleam/int
import gleam/json
import gleam/list
import gleam/result
import gleam/string
import gleam/uri
import http_helpers

// WHY helix-logins-lowercase: Twitch user_login values are lowercase-only, Nim asserts/toLowers at fetch site — see main.nim get_twitch_info_for_20/get_twitch_infos.

pub fn get_access_token(
  client_id: String,
  client_secret: String,
) -> Result(String, String) {
  use endpoint <- result.try(
    uri.parse("https://id.twitch.tv/oauth2/token")
    |> result.map_error(string.inspect),
  )
  let token_req =
    token_request.ClientCredentialsGrantTokenRequest(
      endpoint,
      auth.ClientSecretPost(
        common.ClientId(client_id),
        common.Secret(client_secret),
      ),
      [],
    )
  use req <- result.try(
    token_request.to_http_request(token_req)
    |> result.map_error(string.inspect),
  )
  use resp <- result.try(http_helpers.send(req))
  oauth_resp.parse_token_response(resp)
  |> result.map(fn(token) { token.access_token })
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
    dict.from_list(list.map(batch, fn(name) { #(name, offline_info(name)) }))
  let live =
    dict.from_list(list.map(live_infos, fn(info) { #(info.username, info) }))
  dict.merge(base, live)
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
  use <- bool.guard(when: size <= 0, return: [])
  case names {
    [] -> []
    _ -> list.sized_chunk(names, size)
  }
}

pub fn get_stream_infos(
  names: List(String),
  token: String,
  client_id: String,
) -> Result(Dict(String, StreamInfo), String) {
  let lowered = normalize_names(names)
  let batches = chunks(lowered, 20)
  list.try_fold(batches, dict.new(), fn(acc, batch) {
    use got <- result.try(fetch_batch(batch, token, client_id))
    Ok(dict.merge(acc, got))
  })
}
