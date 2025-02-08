# Create audio loopbacks for twitch recording
# Create sink, description is the name it shows in pulseaudio
pactl load-module module-null-sink sink_name=Twitch sink_properties=device.description=Twitch
pactl load-module module-null-sink sink_name=TwitchNoVod sink_properties=device.description=TwitchNoVod

# Create loopback from source=devicename, find devicename from: 'pactrl list sources'
pactl load-module module-loopback source=Twitch.monitor
pactl load-module module-loopback source=TwitchNoVod.monitor
