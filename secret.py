import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
from discord import File
from io import StringIO
import string
import random

BASE_DIR = Path(__file__).resolve().parent.parent
KEYS_FILE = BASE_DIR / "keys.txt"

def generate_key(length=20):
    allowed_chars = string.ascii_letters + string.digits + "!$?"
    return ''.join(random.choices(allowed_chars, k=length))

def load_keys():
    keys = {}
    if not KEYS_FILE.exists():
        return keys

    with open(KEYS_FILE, 'r') as f:
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

def save_keys(keys: dict):
    with open(KEYS_FILE, 'w') as f:
        for key, user_id in keys.items():
            if user_id:
                f.write(f"{key}:{user_id}\n")
            else:
                f.write(f"{key}\n")

class BulkGenKeys(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="genkeys", description="Generate premium keys and get them in DMs. (Owner only)")
    @app_commands.describe(amount="Number of keys to generate")
    async def genkeys(self, interaction: discord.Interaction, amount: int):
        owner_id = 110332657337913344
        if interaction.user.id != owner_id:
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return

        if amount < 1 or amount > 100000:
            await interaction.response.send_message("You can generate between 1 and 100,000 keys at a time.", ephemeral=True)
            return

        existing_keys = load_keys()
        new_keys = []

        while len(new_keys) < amount:
            key = generate_key()
            if key not in existing_keys:
                new_keys.append(key)
                existing_keys[key] = None

        save_keys(existing_keys)

        key_list = "\n".join(new_keys)
        file = File(fp=StringIO(key_list), filename="premium_keys.txt")

        try:
            await interaction.user.send(
                content=f"Here are your {amount} premium key(s):",
                file=file
            )
            await interaction.response.send_message("Keys generated and sent to your DMs.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Failed to send DM. Please enable DMs from server members.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BulkGenKeys(bot))
