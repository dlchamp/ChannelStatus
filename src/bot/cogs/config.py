from datetime import time
from typing import Optional

import pytz
from bot.cogs.helper import helper
from bot.config import query
from disnake import ApplicationCommandInteraction, Color, Embed, TextChannel, utils
from disnake.ext.commands import Cog, default_member_permissions, slash_command
from disnake.ui import Button, View


class Config(Cog):
    """Class that represents the configure commands"""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.days = ("mon", "tues", "wed", "thurs", "fri", "sat", "sun")

    @Cog.listener(name="on_ready")
    async def loaded_cog(self) -> None:
        """Invoked when this cog is loaded"""
        print(f"Cog loaded: {self.qualified_name}")

    @slash_command(name="config")
    # @default_member_permissions(manage_channels=True)
    async def config(self, interaction: ApplicationCommandInteraction) -> None:
        """Slash group parent command - always invoked when a sub-command is used"""
        pass

    @config.sub_command(name="view")
    async def config_view(self, interaction: ApplicationCommandInteraction) -> None:
        """
        View the current configuration for this server
        """

        guild = await query.get_guild_config(interaction.guild.id)
        slash_guild = interaction.guild

        # create and format the embed showing command guild's current config
        embed = helper.guild_config_info(slash_guild, guild)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @config.sub_command_group(name="set")
    async def config_set_sub_command_group(
        self, interaction: ApplicationCommandInteraction
    ) -> None:
        """Sub command group parent, always invoked when a group sub-command is used"""
        pass

    @config_set_sub_command_group.sub_command(name="timezone")
    async def config_set_timezone(
        self, interaction: ApplicationCommandInteraction, timezone: str
    ) -> None:
        """Set the timezone for this guild

        Parameters
        ----------
        timezone: Supported timezone (https://bit.ly/2JtQfVI)
        """
        if not timezone in pytz.all_timezones:

            view = View()
            view.add_item(
                Button(
                    label="View Supported Timezones",
                    url="https://gist.github.com/dlchamp/4d0a45f58ec222faed406ee221a6c771",
                )
            )

            return await interaction.response.send_message(
                "You must use a supported timezone.",
                view=view,
                ephemeral=True,
            )

        guild = interaction.guild
        await query.update_guild_timezone(guild.id, timezone)

        await interaction.response.send_message(
            f"Timezone has been updated", ephemeral=True
        )

    @config_set_sub_command_group.sub_command(name="channel")
    async def config_add_update_channel(
        self,
        interaction: ApplicationCommandInteraction,
        channel: TextChannel,
        time_lock: Optional[str] = None,
        time_unlock: Optional[str] = None,
        days: Optional[str] = None,
    ) -> None:
        """Add or update a channel to be locked/unlocked automatically

        Parameters
        ----------
        channel: The text channel you wish to automatically lock/unlock
        time_lock: The time when a channel should lock (24-hour time- 01:30)
        time_unlock: The time when a channel should unlock (24-hour time- 01:30)
        """
        guild = interaction.guild

        # convert time strings to time objects
        if time_lock:
            try:
                lock_hours, lock_minutes = time_lock.split(":")
            except ValueError:
                return await interaction.response.send_message(
                    "Please make sure time_lock is in the correct format:\n"
                    "Must be in 24-hour format and should  appear as hour:minutes. [examples: 03:30, 00:20, 20:15]",
                    ephemeral=True,
                )
            else:
                try:
                    time_lock: time = time(int(lock_hours), int(lock_minutes))
                except ValueError:
                    return await interaction.response.send_message(
                        f"Hours must be **0-23** and minutes **0-59**", ephemeral=True
                    )

        if time_unlock:
            try:
                unlock_hours, unlock_minutes = time_unlock.split(":")
            except ValueError:
                return await interaction.response.send_message(
                    "Please make sure time_unlock is in the correct format:\n"
                    "Must be in 24-hour format and should  appear as hour:minutes. [examples: 03:30, 00:20, 20:15]",
                    ephemeral=True,
                )
            else:
                try:
                    time_unlock: time = time(int(unlock_hours), int(unlock_minutes))
                except ValueError:
                    return await interaction.response.send_message(
                        f"Hours must be **0-23** and minutes **0-59**", ephemeral=True
                    )

        if days:
            try:
                days = helper.split_days(days)
            except ValueError:
                return await interaction.response.send_message(
                    "Invalid days format\nMust a range or list of weekday numbers\n`1-3` (Tuesday-Thursday) or `0, 2, 4, 6` (Monday, Wednesday, Friday, Sunday)",
                    ephemeral=True,
                )

        add, lock, unlock, days = await query.update_guild_channel(
            guild.id,
            channel_id=channel.id,
            time_lock=time_lock,
            time_unlock=time_unlock,
            days=days,
        )

        if add:
            msg = "**New Channel Added!**\n"
        else:
            msg = "**Channel Updated!**\n"

        time_unlock = str(unlock.strftime("%H:%M"))
        time_lock = str(lock.strftime("%H:%M"))

        await interaction.response.send_message(
            f"{msg}\n"
            f"**Channel**: {channel.name}\n"
            f"**Unlock Time**: {time_unlock}\n"
            f"**Lock Time**: {time_lock}\n"
            f"**Days**: {days}",
            ephemeral=True,
        )

    @config.sub_command(name="remove")
    async def config_remove_channel(
        self, interaction: ApplicationCommandInteraction, channel: str
    ) -> None:
        """Remove a channel from configured channels

        Parameters
        ----------
        channel: A discord text channel
        """

        guild = interaction.guild
        channel = utils.get(guild.text_channels, name=channel)
        await query.remove_channel(channel.id)

        await interaction.response.send_message(
            f"#{channel.name} has been removed", ephemeral=True
        )

    @config_remove_channel.autocomplete("channel")
    async def channel_auto_complete(
        self, interaction: ApplicationCommandInteraction, string: str
    ) -> list:
        """Auto complete channels to select from with the remove channel command"""

        string = string.lower()
        guild = interaction.guild
        channel_ids = await query.get_channel_ids(guild.id)
        channels = [guild.get_channel(i) for i in channel_ids]

        return [c.name for c in channels if string in c.name.lower()]
