from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId
from discord import NotFound
from discord.ext import commands, tasks
from dpytools.menus import multichoice
from dpytools.parsers import to_timedelta, Trimmer

from examples.reminder_bot.database import db


def bad_time(delta: timedelta) -> Optional[str]:
    """Returns a string if the timedelta is shorter than the minimum"""
    if delta.total_seconds() <= 0:
        return 'I cannot work backwards... maybe one day.'
    elif delta.total_seconds() < (60 * 5):
        return 'Minimum reminder time is 5 minutes, please try again.'


class ReminderCog(commands.Cog):
    """This cog holds the logic for working with reminders"""

    def __init__(self, bot):
        self.bot = bot
        self.remind.start()
        print(f"cog: {self.qualified_name} loaded")

    @commands.command(name='in')
    async def in_(self, ctx, time: to_timedelta, *, what):
        """Sets a reminder in this channel in the specified time
        Example:
            remindme! in 5m Drink Water!!
        """
        if bad_time_string := bad_time(time):
            return await ctx.send(bad_time_string)

        now = ctx.message.created_at
        when = now + time

        await db.all_reminders.insert_one({
            'user_id': ctx.author.id,
            'channel_id': ctx.channel.id,
            'next_time': when,
            'content': what,
            'recurrent_time': False,
            'done': False,
        })

        await ctx.send(f"I'll remind you then on {when.strftime('%x %X')} (utc)")

    @commands.command()
    async def every(self, ctx, time: str, *, what):
        """Repeats a reminder every X time
        Example:
            remindme! every 5m WORK!
        """
        delta = to_timedelta(time)

        if bad_time_string := bad_time(delta):
            return await ctx.send(bad_time_string)

        now = ctx.message.created_at
        when = now + delta

        await db.all_reminders.insert_one({
            'user_id': ctx.author.id,
            'channel_id': ctx.channel.id,
            'next_time': when,
            'content': what,
            'recurrent_time': time,
            'done': False,
        })

        await ctx.send(f"I'll remind you every {delta}.\n"
                       f"Next reminder on {when.strftime('%x %X')} (utc)")

    @commands.command()
    async def delete(self, ctx):
        """Deletes a recurrent reminder"""
        trimmer = Trimmer(max_length=140)
        reminders = await db.all_reminders.find({'user_id': ctx.author.id, 'done': False}).to_list(length=None)
        options = {}
        for i, reminder in enumerate(reminders, start=1):
            channel = self.bot.get_channel(reminder['channel_id'])
            options[

                (f"**{i})** Every: __{reminder['recurrent_time']}__ "
                 if reminder['recurrent_time']
                 else f"On: __{reminder['next_time'].strftime('%x %X')}__ ") +
                (f"In: {channel.mention}" if channel else "") +
                f"| {trimmer(reminder['content'])}\n\n"
                ] = reminder
        if options:
            choice = await multichoice(ctx, list(options))
            if choice:
                reminder = options[choice]
                reminder['done'] = True
                await db.all_reminders.replace_one({'_id': ObjectId(reminder['_id'])}, reminder)
                await ctx.send('Done!')
            else:
                await ctx.send('Cancelled!')
        else:
            await ctx.send("You don't have any active reminders")

    @tasks.loop(seconds=5)
    async def remind(self):
        await self.bot.wait_until_ready()
        now = datetime.utcnow()
        reminders = db.all_reminders.find({'done': False, 'next_time': {'$lte': now}})
        async for reminder in reminders:
            channel = self.bot.get_channel(reminder['channel_id'])
            guild = getattr(channel, 'guild', None)
            try:
                if guild:
                    author = await guild.fetch_member(reminder['user_id'])
                else:
                    author = await self.bot.fetch_user(reminder['user_id'])
            except NotFound:
                if reminder['next_time'] <= (now - timedelta(days=2)):
                    reminder['done'] = True
                    await db.all_reminders.replace_one({'_id': reminder['_id']}, reminder)
                continue
            else:
                if author and channel:
                    await channel.send(f"{author.mention}! Here's your reminder:\n"
                                       f">>> {reminder['content']}")

                    if (time := reminder['recurrent_time']) is not False:
                        reminder['next_time'] = now + to_timedelta(time)
                    else:
                        reminder['done'] = True

                    await db.all_reminders.replace_one({'_id': reminder['_id']}, reminder)


def setup(bot):
    bot.add_cog(ReminderCog(bot))
