from audioop import add
from datetime import datetime, timedelta
from sys import version as sys_version

import pytz
from disnake import Activity, ActivityType, Guild, Intents, TextChannel
from disnake import __version__ as disnake_version
from disnake.ext import commands, tasks

from bot import __version__ as bot_version
from bot.cogs import Config
from bot.cogs.helper import helper
from bot.config import query

bot = commands.InteractionBot(
    intents=Intents.default(),
    test_guilds=[947543739671412878],
    activity=Activity(type=ActivityType.watching, name="/help"),
)


@bot.listen(name="on_ready")
async def bot_ready() -> None:
    """Invoked when bot has connected to Discord api and completed internal caching"""
    print(
        "--------------------------\n"
        f'Bot started: {datetime.now().strftime("%m/%d/%Y - %H:%M:%S")}\n'
        f"System version: {sys_version}\n"
        f"Disnake version: {disnake_version}\n"
        f"Bot Version: {bot_version}\n"
        f""
        "--------------------------\n"
        f"Successfully connected to Discord as: {bot.user} ({bot.user.id})\n"
        "--------------------------"
    )

    await bot.wait_until_ready()
    lock_unlock_channel.start()
    add_guilds.start()


# load cogs
bot.add_cog(Config(bot))


"""
Asyncio tasks 
"""


@tasks.loop(seconds=30)
async def lock_unlock_channel() -> None:
    """Asyncio loop that runs every 5 minutes and checks if the
    current time is greater than the configured time to lock or unlock
    the configured channels"""

    # fetch all guilds and their config channels from the database
    guilds = await query.get_guild_configs()

    for _guild_ in guilds:
        # get discord guild object for getting channel
        # objects later
        guild: Guild = bot.get_guild(_guild_.id)
        # set timezone objects from guild config
        timezone: str = "UTC" if _guild_.timezone is None else _guild_.timezone
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        for _channel_ in _guild_.channels:
            # get time data from db and convert to localized tz datetime objects
            unlocked = _channel_.unlocked
            local_lock_time = helper.combine_date_time(
                now.date(), _channel_.time_lock, tz
            )
            local_lock_time_30_seconds = local_lock_time + timedelta(seconds=30)
            local_unlock_time = helper.combine_date_time(
                now.date(), _channel_.time_unlock, tz
            )
            local_unlock_time_30_seconds = local_unlock_time + timedelta(seconds=30)

            weekday = now.weekday()

            # split channels days or date range  into comparable weekdays
            c_days = _channel_.days

            if not helper.should_run(c_days, weekday):
                continue

            # check if channel is ready to be locked
            if local_lock_time <= now <= local_lock_time_30_seconds and unlocked:

                # lock channel
                channel: TextChannel = guild.get_channel(_channel_.channel_id)
                await channel.set_permissions(guild.default_role, send_messages=False)

                # update channel name
                name = channel.name.replace("🔴", "").replace("🟢", "")
                await channel.edit(name=f"🔴{name}🔴")

                # update channel locked status
                await query.update_channel_status(channel.id, is_unlocked=False)

            # check if channel is ready to be unlocked
            if (
                local_unlock_time <= now <= local_unlock_time_30_seconds
                and not unlocked
            ):
                # unlock channel
                channel: TextChannel = guild.get_channel(_channel_.channel_id)
                await channel.set_permissions(guild.default_role, send_messages=None)

                # update channel name
                name = channel.name.replace("🟢", "").replace("🔴", "")
                await channel.edit(name=f"🟢{name}🟢")

                # update channel locked status
                await query.update_channel_status(channel.id, is_unlocked=True)


@tasks.loop(count=1)
async def add_guilds():
    """Adds any new guilds that were added to the bot while offline"""

    for guild in bot.guilds:
        await query.add_guild(guild.id)
