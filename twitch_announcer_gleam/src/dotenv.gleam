import dot_env as dot

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
  load_path(".env")
  load_path("twitch_announcer_gleam/.env")
}
