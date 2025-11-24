#!/bin/bash
set -x

sudo pacman -S --needed ansible git

ansible-galaxy install -r requirements.yml

ansible-playbook main.yml -i hosts --ask-become-pass --check

ansible-playbook main.yml -i hosts --ask-become-pass --diff

# Open xfce settings editor and adjust power settings on AC https://docs.xfce.org/xfce/xfce4-settings/editor
# Power manager, turn off display power management when plugged in
# Set up terminal to have solid background
# Set keyboard repeat rate to 40 and delay to 250
# Set up 'keyboard' settings shortcut for terminal to remove '--dropbown' and 'ctrl+g' to open 'thunar'
# Set up thunar to show hidden files, use 'list view' and proper datetime display for modified files
# Set system clock, and sync clock 'time only' and format '%A %d %b %y, %T'
# Never group windows in task bar
# Set task bar to 2 rows and row size 20
# In XFCE, set 'appearence' style to 'Matcha-dark-sea', icons to 'Papirus-Dark-Maia'
# Edit ~/.profile and add lines 'export GTK_THEME=Matcha-dark-sea' and 'export color-scheme=prefer-dark' to set gnome apps to dark mode
