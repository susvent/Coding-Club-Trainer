import signal
import asyncio
import logging
import sys
import traceback
import fs
import main
import cf
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

def attach(bot: commands.Bot):
    logging.info("Starting bot...")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        logging.error(f"Cmd error: {ctx.command} — {error}")
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await ctx.send("Command failed.")

    def shutdown_handler():
        asyncio.create_task(cf.shutdown())
        asyncio.create_task(bot.close())
        logging.info("Shutting down... (no JSON overwrite).")

    @bot.event
    async def on_connect():
        logging.info("Starting bot...")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CommandOnCooldown):
            # Send the cooldown message that was raised by your Cog
            return await ctx.send(str(error), delete_after=5)
        # any other errors...
        logging.error(f"Cmd error: {ctx.command} — {error}")
        await ctx.send("❌ Something went wrong.")

    @bot.event
    async def on_app_command_error(interaction, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await interaction.response.send_message(str(error), ephemeral=True)
        # you can also handle AppCommandError here...
        raise error

    signal.signal(signal.SIGINT, lambda s, f: shutdown_handler())
    signal.signal(signal.SIGTERM, lambda s, f: shutdown_handler())
