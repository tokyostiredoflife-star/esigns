import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path

class PremiumPrivateRoom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_redeemed_ids(self):
        ids = set()
        keys_file = Path(__file__).resolve().parent.parent / "keys.txt"
        if not keys_file.exists():
            return ids
        with open(keys_file, 'r') as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) == 2:
                    ids.add(parts[1].strip())
        return ids

    def has_premium(self, user_id: int):
        return str(user_id) in self.load_redeemed_ids()

    @app_commands.command(name="privateroom", description="Create a private room for 30 Minutes (premium only).")
    @app_commands.checks.cooldown(1, 5.0)
    async def privateroom(self, interaction: discord.Interaction):
        if not self.has_premium(interaction.user.id):
            await interaction.response.send_message(
                "You don't have premium access. Use a valid key with `/redeem` first.",
                ephemeral=True
            )
            return

        category = interaction.channel.category
        if category is None:
            await interaction.response.send_message(
                "This command must be used in a channel inside a category.",
                ephemeral=True
            )
            return

        for channel in interaction.guild.text_channels:
            if (channel.name.startswith("private-") and
                channel.category == category and
                channel.overwrites_for(interaction.user).view_channel):
                await interaction.response.send_message(
                    f"You already have a private room: {channel.mention}. Please wait until it is deleted.",
                    ephemeral=True
                )
                return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        private_channel = await category.create_text_channel(
            name=f"private-{interaction.user.name}",
            overwrites=overwrites,
            reason="Premium private room creation"
        )

        await interaction.response.send_message(
            f"{interaction.user.mention}, your private room {private_channel.mention} has been created for 30 Minutes.",
            ephemeral=True
        )

        await asyncio.sleep(1800)
        try:
            await private_channel.delete(reason="Private room expired after 30 minutes")
        except discord.NotFound:
            pass

    @privateroom.error
    async def privateroom_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            embed = discord.Embed(
                title="Slow down...",
                description="You're doing that too fast. Try again in a few seconds.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
            raise error

async def setup(bot):
    await bot.add_cog(PremiumPrivateRoom(bot))
