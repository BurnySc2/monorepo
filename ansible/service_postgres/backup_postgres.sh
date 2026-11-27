# Exit the script if any command fails
set -euo pipefail

DATABASE_NAME="$1"
PASSWORD="$2"

BACKUP_FOLDER="{{ secrets.POSTGRES.BACKUP_MOUNT_PATH }}"

STAMP="$(date +'%Y-%m-%d_%H%M%S')"
if [ "$(date +%d)" -eq 01 ]; then
    # Monthly backup on the first day of the month
    TIER="MONTHLY"
elif [ "$(date +%u)" -eq 7 ]; then
    # Create weekly backup on Sundays
    TIER="WEEKLY"
else
    TIER="DAILY"
fi
BACKUP_PATH="${BACKUP_FOLDER}/${DATABASE_NAME}_${TIER}_${STAMP}.7z"

# Create folder if it doesn't exist, and make syncthing owner
mkdir -p "$BACKUP_FOLDER"
exec 200>"$BACKUP_FOLDER/.backup.lock"
flock -n 200 || { echo "Another backup is running" >&2; exit 1; }
chown syncthing:syncthing "$BACKUP_FOLDER"
# Only owner can enter the folder
chmod 700 "$BACKUP_FOLDER"

TMPD="$(mktemp -d)"
trap 'rm -rf "$TMPD"' EXIT

CONTAINER_NAME="postgres_postgres"
docker exec "$CONTAINER_NAME" pg_dumpall -U postgres -g > "$TMPD/globals.sql"

# https://medium.com/@burakkocakeu/get-pg-dump-from-a-docker-container-and-pg-restore-into-another-in-5-steps-74ca5bf0589c
# Backup
backupargs=(
    exec $CONTAINER_NAME
    pg_dump
    # User
    -U postgres
    # Database
    -d "$DATABASE_NAME"
    # Format
    -F c
    --compress=zstd:9
)
# Compress and encrypt
zipargs=(
    a
    # Set archive type
    -t7z
    # Require password before seeing files: hide file structure
    -mhe=on
    # Compression level, not needed because already compressed with zstd
    -mx0
    # Set password
    "-p$PASSWORD"
    # Input from stdin comes from pipe
    "-si${DATABASE_NAME}.dump"
    "$BACKUP_PATH"
    "$TMPD/globals.sql"
)
# Compress raw sql with 7z
docker "${backupargs[@]}" | 7z "${zipargs[@]}"
dump_rc="${PIPESTATUS[0]}"
zip_rc="${PIPESTATUS[1]}"
if [ "$dump_rc" -ne 0 ] || [ "$zip_rc" -ne 0 ]; then
    echo "Backup pipe failed: pg_dump rc=$dump_rc 7z rc=$zip_rc" >&2
    exit 1
fi

# Verify archive integrity
7z t "-p$PASSWORD" "$BACKUP_PATH"

# Make owner syncthing so that it can sync properly
chown syncthing:syncthing "$BACKUP_PATH"
# Only owner can read/write, group can read
chmod 640 "$BACKUP_PATH"

# Keep up to 3 backups newest, remove other
MAX_BACKUPS=3
prune_tier() {
    local tier="$1"
    local -a files=()
    while IFS= read -r -d '' f; do
        files+=("$f")
    done < <(find "$BACKUP_FOLDER" -maxdepth 1 -type f -name "${DATABASE_NAME}_${tier}_*.7z" -print0 | sort -z)
    if [ "${#files[@]}" -gt "$MAX_BACKUPS" ]; then
        rm -f -- "${files[@]:0:$((${#files[@]} - MAX_BACKUPS))}"
    fi
}
for tier in DAILY WEEKLY MONTHLY; do
    prune_tier "$tier"
done
