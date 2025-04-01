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

# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))