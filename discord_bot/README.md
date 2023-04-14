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
!reminder 2m this will remind me in 2 minutes
!reminder 2h this will remind me in 2 hours
!reminder 2h 2m this will remind me in 2 hours and 2 minutes

# Remind the user at a certain time in the same channel of a text message
!remindat <date> <time> <message>
!remindat <date> <message>
!remindat <time> <message>
!remindat 16:20 this will remind me at 16:20 utc
!remindat 4-20 this will remind me on 20th of april at midnight utc
!remindat 4-20 16:20 this will remind me on 20th of april at 16:20 utc

# List all your pending reminders
!reminders

# Remove a reminder from !reminders
!delreminder <reminder-id>

# Count all the emotes of the user on that server
!count

# Display leaderboard of users in this server
!leaderboard
!leaderboard -m
!leaderboard -w
!leaderboard 5-15
!leaderboard -m 5-15
!leaderboard 5-15 -m

# Display a random TWSS quote
!twss

# Find specific aoe4 player profiles with a given name
!aoe4find burny
!aoe4search burny

# Analyse build order of a specific game from a specific player perspective
!aoe4analyse https://aoe4world.com/players/585764/games/66434421
!aoe4analyse <https://aoe4world.com/players/585764/games/66434421>
        
# Find games that match the specific criteria
!aoe4bo --race english --condition 2towncenter<400s,wheelbarrow<900s,feudal<360s,castle<660s
```
