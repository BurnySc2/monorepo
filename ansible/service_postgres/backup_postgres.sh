# Exit the script if any command fails
set -e

BACKUP_FOLDER="{{ secrets.POSTGRES.BACKUP_MOUNT_PATH }}"
BACKUP_PATH="${BACKUP_FOLDER}/$(date +'%Y-%m-%d_%H:%M:%S').tar"

# Create folder if it doesn't exist, and make syncthing owner
mkdir -p $BACKUP_FOLDER
chown syncthing:syncthing $BACKUP_FOLDER
# Only owner can read/write, group can read
chmod 640 $BACKUP_FOLDER

# https://medium.com/@burakkocakeu/get-pg-dump-from-a-docker-container-and-pg-restore-into-another-in-5-steps-74ca5bf0589c
CONTAINER_NAME="postgres_postgres"
docker exec $CONTAINER_NAME pg_dump -U postgres -F t postgres > $BACKUP_PATH
# Make owner syncthing so that it can sync properly
chown syncthing:syncthing $BACKUP_PATH
# Only owner can read/write, group can read
chmod 640 $BACKUP_PATH

# Remove backups with file size < 1kb (= failed backups)
cd $BACKUP_FOLDER
find . -maxdepth 1 -type f -name '*.tar' -size -1024c -delete

# Keep up to 3 backups newest, remove other
MAX_BACKUPS_TO_KEEP=3
FILES_TO_REMOVE=$(ls -t *.tar | tail -n +$(expr $MAX_BACKUPS_TO_KEEP + 1))
if [ -n "$FILES_TO_REMOVE" ]; then
    for file in $FILES_TO_REMOVE; do 
        echo "Removing older .tar file: $file"
        rm $file
    done 
fi
