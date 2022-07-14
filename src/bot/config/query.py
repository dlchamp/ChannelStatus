from datetime import time
from optparse import Option
from typing import Optional

from bot.config.model import Channel, Guild, async_session
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


async def get_guild_config(guild_id: int) -> Guild:
    """Returns a Guild database object"""

    async with async_session() as session:
        async with session.begin():

            result = await session.execute(
                select(Guild)
                .where(Guild.id == guild_id)
                .options(selectinload(Guild.channels))
            )

    return result.scalars().first()


async def update_guild_timezone(guild_id: int, timezone: str) -> None:
    """Updates the guild's configured timezone"""

    async with async_session() as session:
        async with session.begin():

            result = await session.execute(select(Guild).where(Guild.id == guild_id))

            guild = result.scalars().first()

            if guild.timezone == timezone:
                return

            guild.timezone = timezone
            await session.commit()


async def update_guild_channel(
    guild_id: int,
    *,
    channel_id: int,
    time_lock: Optional[time] = None,
    time_unlock: Optional[time] = None,
    days: Optional[str] = None
) -> tuple:
    """Updates a channel's lock/unlock times, or adds a new channel
    Returns True if a new channel was added, or false if a channel was updated"""

    async with async_session() as session:
        async with session.begin():

            result = await session.execute(
                select(Channel)
                .where(Channel.guild == guild_id)
                .where(Channel.channel_id == channel_id)
            )

            channel = result.scalars().first()

            if channel is None:
                session.add(
                    Channel(
                        guild=guild_id,
                        channel_id=channel_id,
                        time_lock=time_lock,
                        time_unlock=time_unlock,
                        days=days,
                    )
                )
                add = True

            else:
                if channel.time_lock != time_lock and not time_lock is None:
                    channel.time_lock = time_lock

                if channel.time_unlock != time_unlock and not time_unlock is None:
                    channel.time_unlock = time_unlock

                if channel.days != days and not days is None:
                    channel.days = days

                add = False

        await session.commit()

    return add, channel.time_lock, channel.time_unlock, days


async def add_guild(guild_id: int, timezone: Optional[str] = None) -> None:
    """Add a new guild to the database"""

    async with async_session() as session:
        async with session.begin():

            result = await session.execute(select(Guild).where(Guild.id == guild_id))

            guild = result.scalars().first()

            if guild:
                return

            session.add(Guild(id=guild_id, timezone=timezone))

        await session.commit()


async def get_channel_ids(guild_id: int) -> list[int]:
    """Return a list of configured channel IDs for the guild"""

    async with async_session() as session:
        async with session.begin():

            result = await session.execute(
                select(Channel).where(Channel.guild == guild_id)
            )

            return [c.channel_id for c in result.scalars()]


async def remove_channel(channel_id: int) -> None:
    """Remove a channel from the guild's channels"""

    async with async_session() as session:
        async with session.begin():

            await session.execute(
                delete(Channel).where(Channel.channel_id == channel_id)
            )

            await session.commit()


async def get_guild_configs() -> Guild:
    """Gets and returns all guilds and associated channels from the table"""

    async with async_session() as session:
        async with session.begin():

            result = await session.execute(
                select(Guild).options(selectinload(Guild.channels))
            )

            return result.scalars()


async def update_channel_status(channel_id: int, *, is_unlocked: bool) -> None:
    """Update a channels' lock/unlocked status"""

    async with async_session() as session:
        async with session.begin():

            result = await session.execute(
                select(Channel).where(Channel.channel_id == channel_id)
            )

            channel = result.scalars().first()

            if channel is None:
                return

            channel.unlocked = is_unlocked

            await session.commit()
