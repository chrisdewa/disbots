import dotenv
from discord.ext import commands

token = dotenv.get_key('.env', 'token')

bot = commands.Bot(command_prefix=('remindme! ', 'remindme!'))


@bot.event
async def on_ready():
    print(f"{bot.user.name} ready!")


bot.load_extension('cogs.reminders')

bot.run(token)
