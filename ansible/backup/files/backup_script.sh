#!/usr/bin/env bash
# Exit the script if any command fails
set -euo pipefail

backup_function() {
    if [ "$#" -eq 4 ] || [ "$#" -eq 5 ]; then
        set -- "$1" "$2" "$3" "$3" "$3" "$4" "${5:-}"
    fi
    if [ "$#" -lt 6 ] || [ "$#" -gt 7 ]; then
        echo "Usage: backup_function <source> <target> <keep_daily> <keep_weekly> <keep_monthly> <password> [excludes_csv]"
        exit 1
    fi

    SOURCE_DIRECTORY="$1"
    TARGET_DIRECTORY="$2"
    KEEP_DAILY="$3"
    KEEP_WEEKLY="$4"
    KEEP_MONTHLY="$5"
    PASSWORD="$6"
    EXCLUDES_CSV="${7:-}"

    mkdir -p "$TARGET_DIRECTORY"

    LOCK_FILE="/tmp/backup-$(basename "$TARGET_DIRECTORY").lock"
    exec {LOCK_FD}>"$LOCK_FILE"
    flock -n "$LOCK_FD" || { echo "Another backup is running: $LOCK_FILE"; exit 1; }

    if [[ ! -d "$SOURCE_DIRECTORY" ]]; then
        echo "Directory does not exist: $SOURCE_DIRECTORY"
        return 1  # Exit the function with a non-zero status
    fi

    create_backup() {
        local tier="$1"
        local keep="$2"
        ARCHIVE_NAME="backup_${tier}_$(date +%Y%m%d_%H%M%S).7z"
        local tmp_archive="$TARGET_DIRECTORY/$ARCHIVE_NAME.tmp"
        trap "rm -f -- \"$tmp_archive\"" EXIT INT TERM
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
        )
        local -a EXCL=()
        if [[ -n "$EXCLUDES_CSV" ]]; then
            IFS=',' read -ra EXCL <<< "$EXCLUDES_CSV"
        fi
        local pat
        for pat in ${EXCL[@]+"${EXCL[@]}"}; do
            if [[ -n "$pat" ]]; then
                zipargs+=("-x!$pat")
            fi
        done
        zipargs+=(
            # Target 7z path (tmp until verified)
            "$tmp_archive"
            # Files to include
            ./*
        )
        # Execute zip command
        7z "${zipargs[@]}"
        7z t "-p$PASSWORD" "$tmp_archive"
        mv -f -- "$tmp_archive" "$TARGET_DIRECTORY/$ARCHIVE_NAME"
        trap - EXIT INT TERM

        # Remove surplus backups, oldest first per tier
        local -a victims=()
        mapfile -t victims < <(find "$TARGET_DIRECTORY" -maxdepth 1 -type f -name "backup_${tier}_*.7z" -printf '%T@ %p\n' | sort -n | cut -d' ' -f2-)
        if (( ${#victims[@]} > keep )); then
            rm -f -- "${victims[@]:0:${#victims[@]}-keep}"
        fi
    }

    if [ "$(date +%d)" -eq 01 ]; then
        # Monthly backup on the first day of the month
        create_backup "MONTHLY" "$KEEP_MONTHLY"
    elif [ "$(date +%u)" -eq 7 ]; then
        # Create weekly backup on Sundays
        create_backup "WEEKLY" "$KEEP_WEEKLY"
    else
        create_backup "DAILY" "$KEEP_DAILY"
    fi

    # Change ownership to syncthing:syncthing
    chown -R syncthing:syncthing "$TARGET_DIRECTORY"
    # Only allow user syncthing to access directory
    chmod -R 700 "$TARGET_DIRECTORY"
}

# Call the function
backup_function "$@"
# Usage: sh backup_script.sh "/path/to/source" "/path/to/target" "amount of backups" "my_secure_password"
