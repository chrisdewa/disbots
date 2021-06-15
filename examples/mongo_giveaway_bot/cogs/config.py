import discord
from discord.ext import commands
from dpytools import Color
from dpytools.embeds import Embed
from dpytools.menus import confirm

from utils import get_guild_config, save_guild_config


class ConfigCog(commands.Cog, name='configuration'):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    async def config(self, ctx):
        """
        This is the access point for configuring the giveaways
        If called alone, the command shows current guild configuration
        Subcommands:
            prefix: Sets up the bot's prefix
        """
        config = await get_guild_config(ctx)
        embed = Embed(
            title=f"{ctx.guild.name} configuration",
            thumbnail=self.bot.user.avatar_url,
        ).add_fields(
            prefix=config.prefix,  # and any other configuration you come up with
        )
        await ctx.send(embed=embed)

    @config.command()
    @commands.has_guild_permissions(administrator=True)
    async def prefix(self, ctx, new_prefix):
        """
        This command set's the server's prefix
        """
        config = await get_guild_config(ctx)
        config.prefix = new_prefix
        await save_guild_config(self.bot, config)
        await ctx.send(f'Done!, prefix set to `{new_prefix}`')



def setup(bot):
    bot.add_cog(ConfigCog(bot))
