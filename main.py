import discord
import os
import threading
import time
from pathlib import Path
from discord.ext import commands
import json
from datetime import datetime, timedelta
import asyncio

base_dir = Path(__file__).resolve().parent
config_path = base_dir / "config.json"
GENERATED_PATH = base_dir / "fansign" / "generated"

if not config_path.exists():
    raise FileNotFoundError(f"config.json not found at {config_path}")

with open(config_path) as f:
    config = json.load(f)

def delete_generated_images():
    pass

threading.Timer(21600, delete_generated_images).start()

def count_recent_fansigns():
    now = datetime.now()
    cutoff = now - timedelta(days=1)
    count = 942
    if GENERATED_PATH.exists():
        for file in os.listdir(GENERATED_PATH):
            filepath = GENERATED_PATH / file
            if filepath.is_file():
                created = datetime.fromtimestamp(filepath.stat().st_mtime)
                if created > cutoff:
                    count += 1
    return count

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def presence_updater():
    await bot.wait_until_ready()
    while not bot.is_closed():
        count = count_recent_fansigns()
        status_text = f".gg/esigns | {count} generated in last 24h"
        try:
            await bot.change_presence(activity=discord.Game(name=status_text))
        except Exception as e:
            print(f"Error setting presence: {e}")
        await asyncio.sleep(10)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    bot.loop.create_task(presence_updater())

    for ext in ["commands.fansign", "commands.gen", "commands.premgen", "commands.bulkgen", "commands.secret", "commands.receiptgen", "commands.privateroom", "commands.link"]:
        try:
            await bot.load_extension(ext)
            print(f"Extension '{ext}' loaded.")
        except Exception as e:
            print(f"Failed to load extension '{ext}': {e}")

    try:
        await bot.tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

bot.run(config["token"])
