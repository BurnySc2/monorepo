# https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Modules/
# pactl list short sinks
# pactl list short sources

# Create audio loopbacks for twitch recording
# Create sink, description is the name it shows in pulseaudio
if ! pactl list sources short | grep -q "Twitch_Sink.monitor"; then
    pactl load-module module-null-sink sink_name=Twitch_Sink sink_properties=device.description=Twitch_Sink
    # Create loopback from source=devicename, find devicename from: 'pactrl list sources'
    pactl load-module module-loopback source=Twitch_Sink.monitor
fi

if ! pactl list sources short | grep -q "TwitchNoVod_Sink.monitor"; then
    pactl load-module module-null-sink sink_name=TwitchNoVod_Sink sink_properties=device.description=TwitchNoVod_Sink
    # Create loopback from source=devicename, find devicename from: 'pactrl list sources'
    pactl load-module module-loopback source=TwitchNoVod_Sink.monitor
fi
