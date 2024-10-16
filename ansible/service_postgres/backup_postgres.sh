# Exit the script if any command fails
set -e

DATABASE_NAME="$1"
PASSWORD="$2"

BACKUP_FOLDER="{{ secrets.POSTGRES.BACKUP_MOUNT_PATH }}"

if [ "$(date +%d)" -eq 01 ]; then
    # Monthly backup on the first day of the month
    BACKUP_PATH="${BACKUP_FOLDER}/${DATABASE_NAME}_MONTHLY_$(date +'%Y-%m-%d_%H:%M:%S').zip"
elif [ "$(date +%u)" -eq 7 ]; then
    # Create weekly backup on Sundays
    BACKUP_PATH="${BACKUP_FOLDER}/${DATABASE_NAME}_WEEKLY_$(date +'%Y-%m-%d_%H:%M:%S').zip"
else
    BACKUP_PATH="${BACKUP_FOLDER}/${DATABASE_NAME}_DAILY_$(date +'%Y-%m-%d_%H:%M:%S').zip"
fi

# Create folder if it doesn't exist, and make syncthing owner
mkdir -p $BACKUP_FOLDER
chown syncthing:syncthing $BACKUP_FOLDER
# Only owner can enter the folder
chmod 700 $BACKUP_FOLDER

# https://medium.com/@burakkocakeu/get-pg-dump-from-a-docker-container-and-pg-restore-into-another-in-5-steps-74ca5bf0589c
# Backup
CONTAINER_NAME="postgres_postgres"
backupargs=(
    exec $CONTAINER_NAME 
    pg_dump 
    # User
    -U postgres
    # Database
    -d $DATABASE_NAME
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
    # Compression level
    -mx0
    # Set password
    "-p$PASSWORD"
    # Input from stdin comes from pipe
    -si
    $BACKUP_PATH
)
# Compress raw sql with 7z
docker "${backupargs[@]}" | 7z "${zipargs[@]}"

# Make owner syncthing so that it can sync properly
chown syncthing:syncthing $BACKUP_PATH
# Only owner can read/write, group can read
chmod 640 $BACKUP_PATH

# Keep up to 3 backups newest, remove other
MAX_BACKUPS=3
cd $BACKUP_FOLDER
ls $BACKUP_FOLDER | grep "${DATABASE_NAME}_DAILY_" | head -n "-$MAX_BACKUPS" | xargs rm -f --
ls $BACKUP_FOLDER | grep "${DATABASE_NAME}_WEEKLY_" | head -n "-$MAX_BACKUPS" | xargs rm -f --
ls $BACKUP_FOLDER | grep "${DATABASE_NAME}_MONTHLY_" | head -n "-$MAX_BACKUPS" | xargs rm -f --
