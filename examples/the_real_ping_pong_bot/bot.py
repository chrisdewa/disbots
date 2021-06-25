import asyncio
from datetime import datetime

import discord
from discord.ext import commands
from dpytools import Emoji

bot = commands.Bot(command_prefix='p:')


@bot.event
async def on_ready():
    print(f"{bot.user.name} ready!")


@bot.command()
async def ping(ctx):
    """Plays ping pong with you"""
    reactions = ['🏓', Emoji.X]

    def check(payload: discord.RawReactionActionEvent):
        return all([
            ctx.author.id == payload.user_id,
            ctx.channel.id == payload.channel_id,
            payload.emoji.name in reactions
        ])

    def lat(first: datetime, last: datetime):
        return f" latency: {round((last - first).total_seconds() * 1000, 1)}ms"

    msg = await ctx.send('Wait a bit...')
    await msg.edit(
        content='Ping!' + lat(ctx.message.created_at, msg.created_at)
    )

    async def close():
        await msg.clear_reactions()
        await ctx.message.edit(delete_after=10)

    for r in reactions:
        await msg.add_reaction(r)
    while True:
        try:
            payload = await bot.wait_for('raw_reaction_add', check=check, timeout=60)
        except asyncio.TimeoutError:
            await msg.edit(content="Timeout. It was fun playing with you", delete_after=10)
            return await close()
        else:
            if payload.emoji.name == '🏓':
                now = datetime.utcnow()
                await msg.edit(
                    content=('Ping!' if msg.content.startswith('Pong!') else 'Pong!')
                )
                await msg.edit(
                    content=msg.content + lat(now, msg.edited_at)
                )
                await msg.remove_reaction('🏓', discord.Object(id=payload.user_id))
            elif payload.emoji.name == Emoji.X:
                await msg.edit(content="It was fun playing with you!")
                return await close()


bot.run('token')
