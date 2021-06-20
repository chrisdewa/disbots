from datetime import datetime

import discord

from dateparser import parse
from discord.ext import commands
from dpytools.errors import InvalidTimeString
from dpytools.parsers import to_timedelta


def parse_n_delta(string):
    arg = None
    try:
        arg = datetime.utcnow() + to_timedelta(string)
    except InvalidTimeString:
        arg = parse(string)
    finally:
        return arg




class ReminderContext:
    def __init__(self, message: discord.Message):
        self.author = message.author
        self.channel = message.channel
        self.send = message.channel.send



