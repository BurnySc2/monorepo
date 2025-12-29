# TTS

## TTS via UI
In the endpoint `http://0.0.0.0:8000/tts` people can generate audio with different (Tiktok-)voices.

## TTS via twitch chat
Streamers can add the endpoint `http://0.0.0.0:8000/tts/twitch/STREAMER_NAME` as a browser source. Then the webserver connects to the twitch channel and reads chat input. If it matches the pattern
```
{VOICE_NAME}: {TEXT}
```
then the audio will be generated and sent to the browser source via websocket connection.



