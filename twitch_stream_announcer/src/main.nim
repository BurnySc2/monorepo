# https://nim-lang.org/docs/db_postgres.html
import db_connector/db_postgres # nimble install db_connector
import std/envvars
import std/httpclient
import std/json
import std/os
import std/sequtils
import std/strutils
import std/tables
import std/times
import std/uri
import strformat

let STAGE = getenv("STAGE")
assert STAGE in ["BUILD", "DEV", "PROD"]

type
  # Data retrieved from twitch api
  StreamInfo = object of RootObj
    username: string
    displayname: string = ""
    live: bool
    stream_title: string = ""
    live_since: string = ""
    stream_category: string = ""

  # Required information to send to webhook
  AnnounceInfo = object of StreamInfo
    webhook_url: string
    announce_message: string

func convert_to_table(row: Row, column_names: seq[string]): TableRef[string, string] =
  result = newTable[string, string]()
  for (column_value, column_name) in zip(row, column_names):
    result[column_name] = column_value

proc fetch_postgres_users(db: DbConn): seq[TableRef[string, string]] =
  # Grab all rows
  # Add a table to the sequence with {key: value} pair of {column_name: column_value} for each row
  result = newSeq[TableRef[string, string]]()
  let column_names =
    @[
      "id", "twitch_name", "discord_webhook", "announce_message", "announced_at",
      "status", "last_seen_online",
    ]
  for row in db.fastRows(
    sql"""
    SELECT id, twitch_name, discord_webhook, announce_message, announced_at, status, last_seen_online 
    FROM stream_announcer_streams 
    WHERE enabled IS TRUE
    ORDER BY id
    ;"""
  ):
    result &= row.convert_to_table(column_names)

proc to_postgres_array(my_seq: seq[string]): string =
  result = ""
  let
    pre = "ANY(ARRAY["
    post = "]::text[])"
  for index, value in my_seq:
    if index > 0:
      result &= ", "
    result &= fmt"'{value}'"
  result = pre & result & post

proc update_database_entries(
    db: DbConn, announced_streams, online_streams, now_offline_streams: seq[string]
) =
  let current_time = now().utc.format("yyyy-MM-dd HH:mm:ss.fff")
  let announced_query =
    "UPDATE stream_announcer_streams SET announced_at = ?, status = 'online', last_seen_online = ? WHERE twitch_name = "
  let online_query =
    "UPDATE stream_announcer_streams SET status = 'online', last_seen_online = ? WHERE twitch_name = "
  let now_offline_query =
    "UPDATE stream_announcer_streams SET status = 'offline' WHERE twitch_name = "
  if announced_streams.len > 0:
    echo fmt"Updating announced streams in db: {announced_streams}"
    if STAGE == "PROD":
      db.exec(
        sql(announced_query & announced_streams.to_postgres_array & ";"),
        current_time,
        current_time,
      )
  if online_streams.len > 0:
    echo fmt"Updating online streams in db: {online_streams}"
    if STAGE == "PROD":
      db.exec(sql(online_query & online_streams.to_postgres_array & ";"), current_time)
  if now_offline_streams.len > 0:
    echo fmt"Updating offline streams in db: {now_offline_streams}"
    if STAGE == "PROD":
      db.exec(sql(now_offline_query & now_offline_streams.to_postgres_array & ";"))

proc get_access_token(client: HttpClient): string =
  # https://dev.twitch.tv/docs/api/get-started/#get-an-oauth-token
  # https://nim-lang.org/docs/httpclient.html
  # https://nim-lang.org/docs/streams.html
  # https://nim-lang.org/docs/json.html
  # Login with oauth, get access token
  client.headers = newHttpHeaders({"Content-Type": "application/x-www-form-urlencoded"})
  let data = newMultipartData()
  data["client_id"] = getenv("TWITCH_APP_ID")
  data["client_secret"] = getenv("TWITCH_APP_SECRET")
  data["grant_type"] = "client_credentials"
  let response = client.post("https://id.twitch.tv/oauth2/token", multipart = data)
  assert response.status[0] == '2'
  assert response.status == "200 OK"
  let access_token: JsonNode = response.body.parseJson["access_token"]
  result = access_token.getStr

proc get_twitch_info_for_20(
    client: HttpClient, access_token: string, streamer_names: seq[string]
): TableRef[string, StreamInfo] =
  assert streamer_names.len <= 20
  for name in streamer_names:
    assert name == name.toLower
  var uri = parseUri("https://api.twitch.tv/helix/streams")
  var params = newSeq[string]()
  for name in streamer_names:
    params &= fmt"user_login={name.toLower}"
  let params_string = params.join("&")
  uri = uri / fmt"?{params_string}"
  let response = client.get(uri)
  assert response.status[0] == '2'
  assert response.status == "200 OK"

  result = newTable[string, StreamInfo]()
  # Set default values, override with live=true in second loop
  for name in streamer_names:
    result[name] = StreamInfo(username: name, live: false)
  for entry in response.body.parseJson["data"]:
    # Do not add the streamer a second time
    assert entry["user_login"].getStr in result
    result[entry["user_login"].getStr] = StreamInfo(
      username: entry["user_login"].getStr,
      displayname: entry["user_name"].getStr,
      live: entry["type"].getStr == "live",
      stream_title: entry["title"].getStr,
      live_since: entry["started_at"].getStr,
      stream_category: entry["game_name"].getStr,
    )

proc get_twitch_infos(
    client: HttpClient, access_token: string, streamer_names: seq[string]
): TableRef[string, StreamInfo] =
  # https://dev.twitch.tv/docs/api/reference/#get-streams
  # Split streamer names into sequences of 20
  # Request info and concatenate data
  client.headers = newHttpHeaders(
    {"Authorization": fmt"Bearer {access_token}", "Client-Id": getenv("TWITCH_APP_ID")}
  )
  result = newTable[string, StreamInfo]()
  var streamer_names_seq: seq[string] = @[]
  for index, name in streamer_names:
    streamer_names_seq &= name.toLower
    if streamer_names_seq.len == 20 or index == streamer_names.high:
      let streams = client.get_twitch_info_for_20(access_token, streamer_names_seq)
      for name, stream_info in streams:
        result[name] = stream_info
      streamer_names_seq = @[]

proc fetch_twitch_stream_status(
    streams: seq[TableRef[string, string]]
): TableRef[string, StreamInfo] =
  # Extract stream names
  var stream_names: seq[string] = @[]
  for stream in streams:
    stream_names.addUnique(stream["twitch_name"])

  let client = newHttpClient()
  try:
    let access_token = client.get_access_token()
    result = client.get_twitch_infos(access_token, stream_names)
  finally:
    client.close()

proc parse_postgres_time(my_time: string): DateTime =
  assert $dateTime(2025, mJan, 1, 9, 9, 9, zone = utc()) ==
    $parse("2025-01-01 09:09:09", "yyyy-MM-dd HH:mm:ss", tz = utc())
  var time_copied = my_time
  let expected_format = "2025-01-06 01:44:43.123456"
  while time_copied.len < expected_format.len:
    time_copied &= "0"
  result = parse(time_copied, "yyyy-MM-dd HH:mm:ss.ffffff", tz = utc())

proc parse_twitch_api_time(my_time: string): DateTime =
  # Expected format: "2025-01-06T03:16:52Z"
  assert $dateTime(2025, mJan, 1, 9, 9, 9, zone = utc()) ==
    $parse("2025-01-01T09:09:09Z", "yyyy-MM-dd'T'HH:mm:ss'Z'", tz = utc())
  result = parse(my_time, "yyyy-MM-dd'T'HH:mm:ss'Z'", tz = utc())

proc datetime_to_webhook_string(my_time: DateTime): string =
  # E.g. converts DateTime object "2025-01-04 01:02:03.123456"
  # to "since 2025-01-04 01:02:03 (which was XX seconds ago)"
  runnableExamples:
    let dt: DateTime =
      parse("2025-01-06 01:44:43.1234", "yyyy-MM-dd HH:mm:ss.ffffff", tz = utc())
    echo dt.datetime_to_webhook_string()
  let formatted = my_time.format("yyyy-MM-dd HH:mm:ss")
  var human_time_interval = between(my_time, now().utc)
  human_time_interval.nanoseconds = 0
  human_time_interval.microseconds = 0
  human_time_interval.milliseconds = 0
  result = fmt"since {formatted} (which was {human_time_interval} ago)"

proc send_webhooks(infos: seq[AnnounceInfo]) =
  # https://nim-lang.org/docs/json.html#creating-json
  # https://discord.com/developers/docs/resources/webhook#execute-webhook
  let client = newHttpClient()
  client.headers = newHttpHeaders({"Content-Type": "application/json"})
  try:
    for info in infos:
      let live_since_datetime = info.live_since.parse_twitch_api_time
      let my_request_body: JsonNode =
        %*{
          "username": "Stream Announcer Webhook",
          "content": info.announce_message,
          "embeds": [
            {
              "title": fmt"{info.displayname} is now live on Twitch!",
              "url": fmt"https://www.twitch.tv/{info.username}",
              "fields": [
                {"name": "Stream title", "value": info.stream_title},
                {
                  "name": fmt"Playing '{info.stream_category}'",
                  "value": live_since_datetime.datetime_to_webhook_string,
                },
              ],
            }
          ],
        }
      if STAGE == "PROD":
        let response = client.post(info.webhook_url, body = $my_request_body)
        assert response.status[0] == '2'
        assert response.status == "204 No Content"
      elif STAGE == "DEV":
        echo(
          fmt"Announcing stream {info.username} in webhook {info.webhook_url}\n{$my_request_body}"
        )
  finally:
    client.close()

proc get_which_streams_to_announce_and_update(
    database_rows: seq[TableRef[string, string]],
    stream_infos: TableRef[string, StreamInfo],
): tuple[
  announced_streams, online_streams, now_offline_streams: seq[string],
  announce_in_webhook: seq[AnnounceInfo],
] =
  result = (@[], @[], @[], @[])
  for row in database_rows:
    let name = row["twitch_name"]
    if name notin stream_infos:
      echo fmt"Name not found in stream_info: {name}"
      continue
    let stream_info = stream_infos[name]
    # Find all channels that switched from online to offline
    if row["status"] != "offline" and not stream_info.live:
      result.now_offline_streams &= name
    if stream_info.live:
      # Always update database entries for live channels
      result.online_streams &= name
      # Find all channels that switched from offline to online
      if row["status"] != "online":
        # If the stream has not been seen online for more than 30 minutes, announce in webhook
        # This should prevent spamming if streamer had a disconnect or restarted stream
        var last_seen_online = row["last_seen_online"]
        # Is this required? Are entries empty string for None values?
        if last_seen_online == "":
          last_seen_online = "2000-01-01 01:01:01.000000"
        let parsed_time = last_seen_online.parse_postgres_time
        if now().utc - parsed_time < initDuration(minutes = 30):
          continue
        result.announced_streams.addUnique(name)
        result.announce_in_webhook &=
          AnnounceInfo(
            username: name,
            displayname: stream_info.displayname,
            live: stream_info.live,
            stream_title: stream_info.stream_title,
            live_since: stream_info.live_since,
            stream_category: stream_info.stream_category,
            webhook_url: row["discord_webhook"],
            announce_message: row["announce_message"],
          )

proc run_once(db: DbConn) =
  let t1 = cpuTime()
  let rows = fetch_postgres_users(db)
  # echo fmt"Rows as list of dict: {rows}"
  let t2 = cpuTime()
  let stream_infos = fetch_twitch_stream_status(rows)
  # echo fmt"Current stream infos: {stream_infos}"
  let t3 = cpuTime()
  let info_tuple = get_which_streams_to_announce_and_update(
    database_rows = rows, stream_infos = stream_infos
  )
  # echo fmt"Info tuple: {info_tuple}"
  let t4 = cpuTime()
  update_database_entries(
    db, info_tuple.announced_streams, info_tuple.online_streams,
    info_tuple.now_offline_streams,
  )
  let t5 = cpuTime()
  send_webhooks(info_tuple.announce_in_webhook)
  let t6 = cpuTime()
  if STAGE == "DEV":
    echo fmt"Fetching database entries: {t2 - t1}"
    echo fmt"Fetching twitch api data: {t3 - t2}"
    echo fmt"Calculating which streams to announce: {t4 - t3}"
    echo fmt"Updating database entries: {t5 - t4}"
    echo fmt"Sending webhooks: {t6 - t5}"
    echo fmt"Total time taken: {t6 - t1}"

proc run_for_one_hour(db: DbConn) =
  let t1 = cpuTime()
  let duration: float = 60 * 60
  while true:
    if duration < cpuTime() - t1:
      break
    echo "Running once"
    run_once(db)
    sleep 60 * 1000

proc main(db: DbConn) =
  if STAGE == "DEV":
    run_once(db)
  elif STAGE == "PROD":
    run_for_one_hour(db)

when isMainModule:
  echo "Started nim.main"
  var db: DbConn
  try:
    let POSTGRES_CONNECTION_STRING = getenv("POSTGRES_CONNECTION_STRING")
    db = open("", "", "", POSTGRES_CONNECTION_STRING)
    main(db)
  except DbError as e:
    echo e.msg
    if STAGE != "BUILD":
      # Reraise error if this is not the docker build process
      raise e
  finally:
    db.close()
