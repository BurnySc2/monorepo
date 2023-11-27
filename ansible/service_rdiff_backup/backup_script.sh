# Exit the script if any command fails
set -e

backup_function() {
    # Check if the correct number of parameters is provided
    if [ "$#" -ne 3 ]; then
        echo "Usage: backup_function <source> <target> <max_backups_to_keep>"
        exit 1
    fi

    SOURCE_DIRECTORY="$1"
    TARGET_DIRECTORY="$2"
    MAX_BACKUPS="$3"

    mkdir -p "$TARGET_DIRECTORY"

    # Perform rdiff-backup
    rdiff-backup backup "$SOURCE_DIRECTORY" "$TARGET_DIRECTORY"

    # Change ownership to syncthing:syncthing
    chown -R syncthing:syncthing "$TARGET_DIRECTORY"
    # Only allow user syncthing to access directory
    chmod 700 "$TARGET_DIRECTORY"

    # Keep at most N backups (replace N with the provided amount)
    rdiff-backup --force remove increments --older-than "${MAX_BACKUPS}"B "$TARGET_DIRECTORY"
}

# Call the function
backup_function $1 $2 $3
# Usage: sh backup_script.sh "/path/to/source" "/path/to/target" "amount of backups"
