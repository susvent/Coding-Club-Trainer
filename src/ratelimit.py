import time
import discord
from collections import defaultdict, deque
from typing import Deque, Dict
from discord.ext import commands
from discord import app_commands

# ✅ Custom exception for rate limiting
class RateLimitError(app_commands.CheckFailure):
    pass

class RateLimit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.history: Dict[int, Deque[float]] = defaultdict(lambda: deque(maxlen=20))
        self.base_cd = 2.0
        self.bot.tree.interaction_check = self.global_app_check

    async def global_app_check(self, interaction: discord.Interaction) -> bool:
        if interaction.type is not discord.InteractionType.application_command:
            return True

        user_id = interaction.user.id
        now = time.monotonic()
        hist = self.history[user_id]
        hist.append(now)

        recent = [t for t in hist if now - t < self.base_cd]
        count = len(recent)
        if count <= 1:
            return True

        # Exponential backoff
        penalty = self.base_cd * (2 ** (count - 1))
        retry_after = penalty - (now - recent[0])
        if retry_after > 0:
            # Friendly user-facing message
            await interaction.response.send_message(
                f"🚫 You're sending commands too quickly. Try again in {retry_after:.1f}s.",
                ephemeral=True
            )
            # Raise custom exception so we can handle it cleanly
            raise RateLimitError()

        return True


async def setup(bot: commands.Bot):
    await bot.add_cog(RateLimit(bot))
