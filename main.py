
import discord
from discord.ext import commands
import asyncio
import aiosqlite
import random
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable necessary intents
intents = discord.Intents.default()
intents.message_content = True

# Set command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

# Import all the bot code
from bot import *

# Initialize database before running the bot
async def init_db():
    async with aiosqlite.connect("profiles.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER,
            name TEXT,
            role TEXT,
            stats TEXT,
            inventory TEXT,
            PRIMARY KEY (user_id, name, role)
        )
        """)
        await db.commit()

# Run initialization and then start the bot
asyncio.run(init_db())
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
