# Package

version       = "0.1.0"
author        = "burnysc2"
description   = "Twitch stream announcer"
license       = "MIT"
srcDir        = "src"
bin           = @["twitch_stream_announcer"]


# Dependencies

requires "nim >= 2.2.0"
requires "db_connector"
requires "dotenv >= 2.0.2"
