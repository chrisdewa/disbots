from typing import Dict

import discord
from discord.ext import commands

from configuration import TOKEN
from database import GuildConfig
from utils import get_command_prefix

intents = discord.Intents.default()
intents.members = True  # we need members intent to locate the giveaway participants and winners


class GiveawayBot(commands.Bot):
    db_cache: Dict[int, GuildConfig] = {}


bot = GiveawayBot(command_prefix=get_command_prefix, intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user.name} ready")


bot.load_extension('cogs.giveaways')

bot.run(TOKEN)
