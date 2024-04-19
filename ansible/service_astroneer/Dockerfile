FROM debian:12-slim

ENV TIMEZONE=Europe/Rome
ENV DEBIAN_FRONTEND=noninteractive
ENV WINEARCH=win64
ENV WINEDEBUG=-all
ENV WINEPREFIX=/root/server

# crudini to edit ini files
# curl to get the server IP
# wget and gnupg2 to install wine
RUN apt update \
    && apt install -y curl gnupg2 wget crudini

# Install steamcmd to be able to install or update astroneer server
# https://developer.valvesoftware.com/wiki/SteamCMD#Debian
# https://stackoverflow.com/a/77853830
RUN echo "deb http://ftp.us.debian.org/debian bookworm main non-free" > /etc/apt/sources.list.d/non-free.list \
    && apt update \
    && apt install -y software-properties-common \
    && apt-add-repository non-free \
    && dpkg --add-architecture i386 \
    && apt update \
    && echo steam steam/question select "I AGREE" | debconf-set-selections \
    && apt install -y steamcmd

# https://wiki.winehq.org/Debian
# Install wine to launch the game
RUN mkdir -pm755 /etc/apt/keyrings \
    && wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key \
    && wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/bookworm/winehq-bookworm.sources \
    && apt update \
    && apt install -y --install-recommends winehq-stable

RUN wget https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks \
    && chmod +x winetricks \
    && apt install -y pulseaudio \
    && ./winetricks sound=pulse \
    && usermod -aG pulse,pulse-access root

ADD entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
