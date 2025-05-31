import discord
from discord.ext import commands
import logging
import traceback
import sys
import logger, main
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.dm_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

logger.attach(bot)

async def main():
    await bot.load_extension("ratelimit")
    await bot.load_extension("main")
    await bot.start(TOKEN)

import asyncio, os
asyncio.run(main())
