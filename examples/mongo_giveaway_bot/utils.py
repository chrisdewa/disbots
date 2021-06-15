from discord.ext import commands
from odmantic.exceptions import DocumentNotFoundError

from configuration import DEFAULT_PREFIX
from database import GuildConfig, engine


async def save_guild_config(bot, config: GuildConfig):
    """
    This function saves a config object to the database and the cache
    """
    bot.db_cache[config.guild_id] = config
    await engine.save(config)


async def delete_guild_config(bot, config: GuildConfig):
    bot.db_cache.pop(config.guild_id, None)
    try:
        await engine.delete(config)
    except DocumentNotFoundError:
        pass


async def get_guild_config(ctx):
    """
    This function tries to fetch the guild configuration, first from the bot's cache and then from the database,
    if it's not found a new object is created and appended to the cache.
 
    Parameters
    ----------
        ctx: :class:`discord.ext.commands.Context`
    
    Returns
    -------
        :class:`GuildConfig`
    """

    guild_id = ctx.guild.id
    guild_config = ctx.bot.db_cache.get(guild_id)

    if not guild_config:  # fetch from the db or make a new object and save to cache.
        guild_config = await engine.find_one(GuildConfig, GuildConfig.query(guild_id)) or GuildConfig(guild_id=guild_id)
        ctx.bot.db_cache[guild_id] = guild_config

    return guild_config


class OrTextChannelConverter(commands.TextChannelConverter):
    """This class overrides the convert method so that user's can pass "here" and the channel will be ctx.channel"""

    async def convert(self, ctx, argument):
        if argument.lower().strip() == 'here':
            return ctx.channel
        else:
            return await super().convert(ctx, argument)


async def get_command_prefix(bot, message):
    if message.guild:
        prefix = bot.db_cache.get(message.guild.id, GuildConfig(guild_id=message.guild.id)).prefix
    else:
        prefix = DEFAULT_PREFIX
    return commands.when_mentioned_or(f"{prefix} ", prefix)(bot, message)  # the double prefix helps typing mistakes
