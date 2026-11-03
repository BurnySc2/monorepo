import gleam/http/request
import gleam/http/response
import gleam/httpc
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
