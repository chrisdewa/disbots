# The Reminder Bot!
<hr>

This bot features:

- Async mongo database with Motor Engine
- Ultra easy interface with three commands
    - `remindme! in time what`
        - `remindme! in 5m to drink water`
            - The bot will send a reminder to ctx.channel in 5 minutos with the "drink water" text
        - `remindme! every 5m work`
            - The bot will remind the user every 5 minutes to work
        - `remindme! delete`
            - Reaction menu to select and delete a specific reminder

# To start up
- Copy the bot's directory
- Install dependencies with `pip install -r requirements.txt`
- Put your bot's token in `.env` (token=hjfhjkdfs128132981329)
- Start the bot up using `python bot.py`
