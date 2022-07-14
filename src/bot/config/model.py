from datetime import time

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, Time
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# constructing the Base class for declarative class definitions
Base = declarative_base()


class Guild(Base):
    """Represents the guild table"""

    __tablename__ = "guild"

    id: int = Column(
        BigInteger,
        primary_key=True,
    )
    timezone: str = Column(String(30), nullable=True, default=None)
    channels = relationship("Channel")

    __mapper_args__ = {"eager_defaults": True}


class Channel(Base):
    """Represents the table channel"""

    __tablename__ = "channel"

    id: int = Column(Integer, primary_key=True)
    guild: int = Column(ForeignKey("guild.id"))
    channel_id: int = Column(BigInteger, nullable=False)
    time_lock: time = Column(Time, nullable=True, default=None)
    time_unlock: time = Column(Time, nullable=True, default=None)
    unlocked: bool = Column(Boolean, nullable=False, default=True)
    days: str = Column(String(20), nullable=True, default=None)


engine = create_async_engine("sqlite+aiosqlite:///bot/config/config.sqlite3")


async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create():
    """create the table and rows if they do not exist"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
