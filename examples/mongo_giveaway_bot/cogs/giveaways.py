import asyncio
import random
from datetime import datetime
from typing import List

import discord
from database import Giveaway, GuildConfig, engine
from discord import NotFound, Forbidden
from discord.ext import commands, tasks
from dpytools import Color
from dpytools.embeds import Embed
from dpytools.emojis import Emoji
from dpytools.menus import TextMenu
from dpytools.parsers import Trimmer, to_timedelta
from dpytools.checks import any_of_permissions
from utils import get_guild_config, OrTextChannelConverter, save_guild_config, delete_guild_config


async def process_giveaway(gw, guild):
    """
    This coro processes a single giveaway
    1) checks if its date is due but has not been finished
    2) gets its channel and message
    3) selects winners
    4) edits messages
    5) if step 2 fails then cancels the giveaway
    """
    now = datetime.utcnow()
    if now >= gw.finishes_at:
        cancelled = 0
        author, msg = None, None
        channel: discord.TextChannel = guild.get_channel(gw.channel_id)
        if channel:
            try:
                msg = await channel.fetch_message(gw.message_id)
            except (NotFound, Forbidden,):  # we're unable to get the giveaway message
                cancelled = 1
            else:
                gw.finished_on = now
                reaction = discord.utils.get(msg.reactions, emoji='🎉')
                participants = [
                    m for m in
                    (await reaction.users().flatten() if reaction else [])  # to consider cleared reactions
                    if isinstance(m, discord.Member)  # so we don't pick users that left the server
                       and not m.bot  # and neither the bot itself or other bots
                ]

                old_embed = msg.embeds[0]
                author = old_embed.author

                if not participants:
                    cancelled = 2
                else:
                    max_winners = lambda p, w: w if len(p) >= w else len(p)  # get correct amount of winners
                    winners = random.sample(participants, k=max_winners(participants, w=gw.max_winners))

                    description = f'**{gw.prize}**\n\n' + (
                        f"Winner: {winners[0].mention}"
                        if len(winners) == 0
                        else "Winners:\n" + ','.join(w.mention for w in winners)
                    )
                    embed = Embed(description=description, color=Color.FUCHSIA) \
                        .set_author(name=author.name, icon_url=author.icon_url) \
                        .set_footer(text="Ended") \
                        .add_field(inline=False,
                                   name=f"Info",
                                   value=f"__Total participants__: {len(participants)}\n"
                                         f"__Maximum Possible winners__: {gw.max_winners}\n"
                                         f"__Actual number of winners__: {len(winners)}")
                    await msg.edit(embed=embed)
                    await msg.reply(content=(f",".join(m.mention for m in winners) + 'You just won!'))
                    gw.winners = [m.id for m in winners]
                    gw.participants = [m.id for m in participants]

        if cancelled:
            gw.cancelled = cancelled
            gw.finished_on = now
            if cancelled == 2 and msg and author:  # we have a message to inform the cancellation
                await msg.edit(embed=(Embed(description=f"**{gw.prize}**\n\n"
                                                        f"Cancelled for lack of participants.",
                                            color=Color.RED)
                                      .set_footer(text=f"Cancelled")
                                      .set_author(name=author.name, icon_url=author.icon_url)))


async def process_guild_giveaways(bot, config: GuildConfig):
    """
    This coro runs all the giveaways in a server concurrently
    """
    guild: discord.Guild = bot.get_guild(config.guild_id)
    if guild:
        gws = [gw for gw in config.giveaways if not gw.finished_on]
        await asyncio.gather(
            *[process_giveaway(gw, guild) for gw in gws]
        )
        if gws:
            await save_guild_config(bot, config)  # finally save all changes we've made
    else:  # we're no longer part of the guild so we delete its configs
        await delete_guild_config(bot, config)


class GiveawayCog(commands.Cog, name='giveaways'):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()
        print(f'{self.qualified_name} loaded')

    @commands.guild_only()
    @any_of_permissions(administrator=True, manage_guild=True)
    @commands.command()
    async def new(self, ctx):
        """
        Set's up a new giveaway
        Only admins and server managers can call this command
        """
        author: discord.Member = ctx.author
        config = await get_guild_config(ctx)
        role = ctx.guild.get_role(config.role)
        trimmer = Trimmer(max_length=200)
        if (role and role in author.roles) or author.guild_permissions.administrator:
            menu = TextMenu(timeout=120, cleanup=True, retry_parse_fail=True)

            menu.add_question(question='What channel should be use to host the giveaway? (you can also say "here")',
                              parser=OrTextChannelConverter())
            menu.add_question(question='How long should it last? <number>[s|m|h|d|w].\n'
                                       'Example: `2h30m` is two hours and 30 minutes.',
                              parser=to_timedelta)
            menu.add_question(question='How many winners can this giveaway have?',
                              parser=lambda string: int(string) if string.isdigit() and int(string) >= 1 else None)
            menu.add_question(question="Finally, what is going to be the prize?",
                              parser=trimmer)

            answers = await menu.call(ctx)
            if not answers:
                return await ctx.send(f"Cancelled {Emoji.X}", delete_after=4)

            channel, duration, winners, prize = answers
            now = datetime.utcnow()
            ends = now + duration
            embed = Embed(description=f"**{prize.capitalize()}**\n\n"
                                      f"`react with 🎉 to enter`",
                          timestamp=ends,
                          color=Color.FUCHSIA)
            embed.set_author(name=f"from {ctx.author.display_name}",
                             icon_url=ctx.author.avatar_url)
            embed.set_footer(text=f"Ends:")
            embed.add_fields(**{'Maximum winners': f'{winners}',
                                'End date': f'{ends.strftime(f"%x %X (utc)")}'},
                             inline=False)

            msg = await channel.send(content=f"🎉**Giveaway!**🎉", embed=embed)
            await msg.add_reaction('🎉')

            giveaway = Giveaway(
                created_at=now,
                finishes_at=ends,
                prize=prize,
                creator_id=ctx.author.id,
                channel_id=msg.channel.id,
                message_id=msg.id,
                max_winners=winners
            )
            config: GuildConfig = await get_guild_config(ctx)
            config.giveaways.append(giveaway)
            config.giveaway_count += 1
            await save_guild_config(self.bot, config)
            await ctx.send(f'Done! {Emoji.GREEN_CHECK}', delete_after=4)
        # else, we silently ignore

    @tasks.loop(seconds=5)
    async def check_giveaways(self):
        await self.bot.wait_until_ready()
        configs: List[GuildConfig] = await engine.find(GuildConfig)  # Get all guild configurations

        await asyncio.gather(
            *[process_guild_giveaways(self.bot, config) for config in configs]
        )


def setup(bot):
    bot.add_cog(GiveawayCog(bot))
