# Manual
After setting up pihole on the server, set up the clients

# Arch
```sh
sudo nano /etc/resolv.conf
```

Add entry
```
nameserver pihole.mydomain.com
```
at the top

# Android phone
Check network settings for currently connected wifi, set ip to static to be able to change dns settings and point them to the pihole website.
