////
//// Loads .env files via dot_env wrapper.
//// Checks repo root then package dir.
//// File values overwrite OS env.
////

import dot_env as dot
import gleam/list

fn load_path(path: String) -> Nil {
  dot.new()
  |> dot.set_path(path)
  |> dot.set_debug(False)
  |> dot.set_capitalize(False)
  |> dot.set_ignore_missing_file(True)
  |> dot.load
}

pub fn load_dotenv() -> Nil {
  // WHY dot_env overwrite: file values replace OS env, unlike prior OS-env-wins
  list.each([".env", "twitch_announcer_gleam/.env"], load_path)
}
