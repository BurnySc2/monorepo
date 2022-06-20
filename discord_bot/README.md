# Python Discord Sc2 Bot

### Installation
- Install python 3.8 or newer (32 or 64 bit)
- Run commands 
    ```
    pip install poetry --user
    poetry install
    ```
- Required private file: DISCORDKEY, SUPABASEKEY, SUPABASEURL (the error messages should display if certain keys are missing)

### Running

Run the bot with command

`poetry run python main.py`

or inside docker via

`sh run.sh`

### Commands
**Public commands:**
```markdown
# Uses nephest.com to grab mmr of the player
!mmr <sc2-name>

# Remind the user in a certain time in the same channel of a text message
!reminder <time-offset> <message>

# Remind the user at a certain time in the same channel of a text message
!remindat <date> <time> <message>

# List all pending reminders of the user
!reminders

# Remove a reminder from !reminders
!delreminder <reminder-id>

# Count all the emotes of the user on that server
!count
```
