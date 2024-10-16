# Exit the script if any command fails
set -e

backup_function() {
    # Check if the correct number of parameters is provided
    if [ "$#" -ne 4 ]; then
        echo "Usage: backup_function <source> <target> <max_backups_to_keep> <password>" 
        exit 1
    fi

    SOURCE_DIRECTORY="$1"
    TARGET_DIRECTORY="$2"
    MAX_BACKUPS="$3"
    PASSWORD="$4"

    create_backup() {
        ARCHIVE_NAME="backup_$1_$(date +%Y%m%d_%H%M%S).zip"
        cd "$SOURCE_DIRECTORY"
        # TODO Find a way to use zstd instead of 7z
        zipargs=(
            a
            # Set archive type
            -t7z
            # Require password before seeing files: hide file structure
            -mhe=on
            # Compression level 0-9 where 5 is default and 0 is no compression
            -mx4
            # mx0: 5sec 1gb
            # mx1: 45sec 196mb
            # mx2: 83sec 187mb
            # mx3: 140sec 177mb
            # mx4: 160sec 175mb
            # mx5: 576sec 135mb
            # mx6: 544sec 135mb
            # mx7: 638sec 127mb
            # mx8: 549sec 126mb
            # mx9: 551sec 126mb
            # Set password
            "-p$PASSWORD"
            # Exclude files
            "-x!**data/transcodes" # jelllyfin
            "-x!**data/metadata" # jelllyfin
            "-x!**data/files" # owncloud
            # Exclude internal backups
            "-x!**backup"
            # Exclude temp and log files
            "-x!**cache"
            "-x!**log"

            # Target zip path
            "$TARGET_DIRECTORY/$ARCHIVE_NAME"
            # Files to include
            ./*
        )
        # Execute zip command
        7z "${zipargs[@]}"

        # Remove surplus backups
        cd $TARGET_DIRECTORY
        ls $TARGET_DIRECTORY | grep "_$1_" | head -n "-$MAX_BACKUPS" | xargs rm -f --
    }

    mkdir -p "$TARGET_DIRECTORY"

    if [ "$(date +%d)" -eq 01 ]; then
        # Monthly backup on the first day of the month
        create_backup "MONTHLY"
    elif [ "$(date +%u)" -eq 7 ]; then
        # Create weekly backup on Sundays
        create_backup "WEEKLY"
    else
        create_backup "DAILY"
    fi

    # Change ownership to syncthing:syncthing
    chown -R syncthing:syncthing "$TARGET_DIRECTORY"
    # Only allow user syncthing to access directory
    chmod -R 700 "$TARGET_DIRECTORY"
}

# Call the function
backup_function $1 $2 $3 $4
# Usage: sh backup_script.sh "/path/to/source" "/path/to/target" "amount of backups" "my_secure_password"
