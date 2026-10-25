# SSL renewal (cron: 0 3 * * 0 bash /home/db/ssl_cron_script.sh >> /home/db/ssl_renewal.log 2>&1)
DATA_DIR="${1:-${PGDATA_DIR:-/home/db/postgres_data}}"
CERT_FILE="${DATA_DIR}/server.crt"
KEY_FILE="${DATA_DIR}/server.key"
CONTAINER_NAME="${CONTAINER_NAME:-postgres_postgres}"

certbot certonly \
     --dns-cloudflare \
     --dns-cloudflare-credentials .cloudflare.ini \
     -d postgres.burnysc2.xyz \
     -n

cp /etc/letsencrypt/live/postgres.burnysc2.xyz/fullchain.pem "$CERT_FILE" && cp /etc/letsencrypt/live/postgres.burnysc2.xyz/privkey.pem "$KEY_FILE" && chown 70:70 "$CERT_FILE" "$KEY_FILE" && chmod 644 "$CERT_FILE" && chmod 600 "$KEY_FILE"

docker exec "$CONTAINER_NAME" psql -U postgres -d postgres -c "ALTER SYSTEM SET ssl = 'on';"
docker exec "$CONTAINER_NAME" psql -U postgres -d postgres -c "ALTER SYSTEM SET ssl_cert_file = 'server.crt';"
docker exec "$CONTAINER_NAME" psql -U postgres -d postgres -c "ALTER SYSTEM SET ssl_key_file = 'server.key';"
docker exec "$CONTAINER_NAME" psql -U postgres -d postgres -c "SELECT pg_reload_conf();"
