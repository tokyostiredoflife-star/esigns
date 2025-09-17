import discord
from discord import app_commands
from discord.ext import commands
import random
import string
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
keys_path = base_dir / "keys.txt"
premium_role_id = 1403991225559678997

def generate_key(length=20):
    allowed_chars = string.ascii_letters + string.digits + "!$?"
    return ''.join(random.choices(allowed_chars, k=length))

def load_keys():
    keys = {}
    if not keys_path.exists():
        return keys

    with open(keys_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                key, user_id = line.split(':', 1)
                keys[key] = user_id
            else:
                keys[line] = None
    return keys

def save_keys(keys):
    with open(keys_path, 'w') as f:
        for key, user_id in keys.items():
            if user_id:
                f.write(f"{key}:{user_id}\n")
            else:
                f.write(f"{key}\n")

class KeyGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="1keygen", description="Generate a redeemable premium key")
    async def gen(self, interaction: discord.Interaction):
        if interaction.user.id != 110332657337913344:
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return

        key = generate_key()
        keys = load_keys()
        keys[key] = None
        save_keys(keys)

        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(
            name="Premium Lifetime Key",
            value=(
                f"`{key}`\n\n"
                "This key grants **lifetime access** to `/premgen` and premium-style fan signs.\n"
                "Share carefully. Can only be redeemed once."
            ),
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="redeem", description="Redeem a key")
    @app_commands.describe(key="The key to redeem")
    async def redeem(self, interaction: discord.Interaction, key: str):
        keys = load_keys()

        if key not in keys:
            await interaction.response.send_message("Invalid key.", ephemeral=True)
            return

        if keys[key] is not None:
            await interaction.response.send_message("Key already redeemed.", ephemeral=True)
            return

        keys[key] = str(interaction.user.id)
        save_keys(keys)

        guild = interaction.guild
        member = interaction.user
        role = guild.get_role(premium_role_id)

        if role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                await interaction.response.send_message("Failed to assign premium role. Bot may be missing permissions.", ephemeral=True)
                return
        else:
            await interaction.response.send_message("Premium role not found in this server.", ephemeral=True)
            return

        await interaction.response.send_message("Key redeemed successfully. You now have premium access.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(KeyGen(bot))
