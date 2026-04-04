# ===================================================================
# SSL Certificate Renewal Script
#
# crontab -e
#
# Cron job to run every 7 days:
# 0 3 * * 0 bash /home/db/ssl_cron_script.sh >> /home/db/ssl_renewal.log 2>&1
#
# ===================================================================

# Create certs, -n for non interactive
certbot certonly \
     --dns-cloudflare \
     --dns-cloudflare-credentials .cloudflare.ini \
     -d postgres.burnysc2.xyz \
     -n

# Copy certs
cp /etc/letsencrypt/live/postgres.burnysc2.xyz/fullchain.pem /home/db/postgres_data/server.crt
cp /etc/letsencrypt/live/postgres.burnysc2.xyz/privkey.pem /home/db/postgres_data/server.key

# Adjust permissions
chmod 600 /home/db/postgres_data/server.key

# TODO: Adjust config file
# nano /home/db/postgres_data/postgresql.conf
# ssl = on
# ssl_cert_file = 'server.crt'
# ssl_key_file = 'server.key'
