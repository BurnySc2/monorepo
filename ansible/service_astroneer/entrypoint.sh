#!/bin/bash
set -x 

# Install or update the game to '/astroneer'
/usr/games/steamcmd +@sSteamCmdForcePlatformType windows +force_install_dir /astroneer +login anonymous +app_update 728470 validate +quit

# Works without, but then we get more error messages in logs
pulseaudio --system=true --daemonize=true

# Run server if path doesn't exist to initialize config files
if [ ! -e "/astroneer/Astro/Saved/Config/WindowsServer/AstroServerSettings.ini" ]; then
    wine "/astroneer/AstroServer.exe"
fi

# Files should exist now, update them
if [ -e "/astroneer/Astro/Saved/Config/WindowsServer/AstroServerSettings.ini" ]; then
    # Update config files
    crudini --set /astroneer/Astro/Saved/Config/WindowsServer/AstroServerSettings.ini "/Script/Astro.AstroServerSettings" "PublicIP" $(curl ifconfig.co)
    crudini --set /astroneer/Astro/Saved/Config/WindowsServer/AstroServerSettings.ini "/Script/Astro.AstroServerSettings" "ServerName" astroneerserver
    crudini --set /astroneer/Astro/Saved/Config/WindowsServer/AstroServerSettings.ini "/Script/Astro.AstroServerSettings" "OwnerName" $OWNER_NAME
    crudini --set /astroneer/Astro/Saved/Config/WindowsServer/AstroServerSettings.ini "/Script/Astro.AstroServerSettings" "OwnerGuid" $OWNER_GUID
    crudini --set /astroneer/Astro/Saved/Config/WindowsServer/AstroServerSettings.ini "/Script/Astro.AstroServerSettings" "ServerPassword" $SERVER_PASSWORD
    crudini --set /astroneer/Astro/Saved/Config/WindowsServer/AstroServerSettings.ini "/Script/Astro.AstroServerSettings" "ActiveSaveFileDescriptiveName" $SAVE_NAME

    crudini --set /astroneer/Astro/Saved/Config/WindowsServer/Engine.ini "url" "Port" {{ APPLICATION_PORT }}
    crudini --set /astroneer/Astro/Saved/Config/WindowsServer/Engine.ini "SystemSettings" "net.AllowEncryption" False
fi

# Start server
wine "/astroneer/AstroServer.exe"
