"""A module of helper functions"""

from datetime import datetime
from typing import NewType

from bot.config import model
from disnake import Color, Embed, Guild, TextChannel
from tabulate import tabulate

Table = NewType("Table[tabulate]", str)


def split_days(days: str) -> list[str]:
    """Split the days into a list of days"""

    if "-" in days:
        days = days.split("-")
        sep = "-"

    if "," in days:
        days = days.split(",")
        sep = ","

    check = [int(d) for d in days]
    if all([c < 7 and c > -1 for c in check]):
        # all can be converted to int and within the 0-6 range
        return f"{sep}".join(days)

    raise ValueError


def format_channels(guild: Guild, channels: model.Channel) -> Table:
    """Formats the channels into a table ready for a Discord embed"""
    if channels == []:
        return

    table = []
    for c in channels:
        channel: TextChannel = guild.get_channel(c.channel_id)
        name = f"#{channel.name}"
        time_lock: str = (
            "None" if c.time_lock is None else c.time_lock.strftime("%H:%M")
        )
        time_unlock: str = (
            "None" if c.time_unlock is None else c.time_unlock.strftime("%H:%M")
        )
        days = "None" if c.days is None else c.days

        table.append([name, time_lock, time_unlock, days])

    return tabulate(
        table,
        headers=["\u200b", "Lock Time", "Unlock Time", "Days"],
        tablefmt="simple",
        stralign="center",
    )


def guild_config_info(slash_guild: Guild, guild: model.Guild) -> Embed:
    """Create and return the embed for guild config view"""

    channels = format_channels(slash_guild, guild.channels)

    embed = Embed(title=f"Current Config for {slash_guild.name}", color=Color.random())
    if slash_guild.icon:
        embed.set_thumbnail(url=slash_guild.icon.url)
    embed.add_field(
        name="Timezone",
        value=str(guild.timezone)
        if guild.timezone
        else "No timezone configured (default: UTC)",
        inline=False,
    )
    if channels is None:
        embed.add_field(name="Channels:", value="No channels configured", inline=False)
    else:
        embed.add_field(name="Channels:", value=f"```py\n{channels}```", inline=False)

    return embed


def combine_date_time(date: datetime.date, time: datetime.time, timezone) -> datetime:
    """combine datetime and stored time objects as tz aware datetime object"""
    return datetime.combine(date, time).astimezone(timezone)


def should_run(days: str, weekday: int) -> bool:
    """Returns true if weekday is in the range of days"""
    if "," in days:
        days = days.split(",")
        days = [int(d) for d in days]
        return weekday in days

    if "-" in days:
        days = days.split("-")
        start, end = [int(d) for d in days]
        return weekday in range(start, end)
