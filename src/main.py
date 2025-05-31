import asyncio
import cf
import fs
import utils
import discord
from datetime import datetime, timedelta, time
from discord.ext import commands, tasks
from discord import Embed
from discord import AllowedMentions, app_commands
from zoneinfo import ZoneInfo
import logging

ET = ZoneInfo("America/New_York")
users = fs.load(fs.USER_TABLE)
problems = fs.load(fs.PROBLEMS_TABLE)
used = set(fs.load(fs.OLD_TABLE))
POST_HOUR = 8
POST_MINUTE = 37
START_DATE = datetime(2025, 5, 29, POST_HOUR, POST_MINUTE, tzinfo=ET)
# CHANNEL_ID = 1372376410059968592
# ROLE = 1372376966270812181
PROBLEMS_CHANNEL = None
DISCUSSION_CHANNEL = None
PROBLEMS_CHANNEL_ID = 1292161967204864041
DISCUSSION_CHANNEL_ID = 1377730821967839392
ROLE = 1292162288022851614
GUILD_ID = 743550548871217172
GUILD = None
member_map = None
OFFICER_ROLE_NAME = "ACC Officer" 
allowed = AllowedMentions(users=True, roles=True)

entries_enabled = True
add_lock = asyncio.Lock()

if "idx" not in problems:
    problems["idx"] = "0"
    fs.save(fs.PROBLEMS_TABLE, problems)

if "total" not in problems:
    problems["total"] = "0"
    fs.save(fs.PROBLEMS_TABLE, problems)


class POTDCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.entries_enabled = True
        self.add_lock = asyncio.Lock()

    def cog_unload(self):
        self.daily_post.cancel()
        self.periodic_update.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        global PROBLEMS_CHANNEL, DISCUSSION_CHANNEL, GUILD, member_map
        GUILD = self.bot.get_guild(GUILD_ID) or await self.bot.fetch_guild(GUILD_ID)
        PROBLEMS_CHANNEL = self.bot.get_channel(PROBLEMS_CHANNEL_ID) or await self.bot.fetch_channel(PROBLEMS_CHANNEL_ID)
        DISCUSSION_CHANNEL = self.bot.get_channel(DISCUSSION_CHANNEL_ID) or await self.bot.fetch_channel(DISCUSSION_CHANNEL_ID)
        member_map = {m.name: m for m in GUILD.members}
        await self.bot.tree.sync(guild=GUILD) 
        await cf.updateCache()
        if not self.daily_post.is_running():
            self.daily_post.start()
        if not self.periodic_update.is_running():
            self.periodic_update.start()
        logging.info(f"Bot online: {self.bot.user} ({self.bot.user.id})")

    @staticmethod
    async def is_officer(interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            return False
        return any(role.name == OFFICER_ROLE_NAME for role in interaction.user.roles)

    async def createEntry(self, easy_link=None, medium_link=None, hard_link=None):
        global problems, used

        provided = easy_link is not None and medium_link is not None and hard_link is not None
        if provided:
            # "❌ One or more problem links are invalid."
            if not cf.validLink(easy_link) or not cf.validLink(medium_link) or not cf.validLink(hard_link):
                return False, None, -1
        
        MAX_TRIES = 50
        tries = 0
        while not provided and tries < MAX_TRIES:
            tries += 1
            provided = True

            easy = await cf.randomProb(900, 1100)
            medium = await cf.randomProb(1100, 1400)
            hard = await cf.randomProb(1400, 1700)
            # f"❌ Error polling Codeforces API."
            if easy is None or medium is None or hard is None:
                return False, None

            easy_link = easy['problem_url']
            medium_link = medium['problem_url']
            hard_link = hard['problem_url']

            if len({easy_link, medium_link, hard_link}) < 3 or \
            any(link in used for link in (easy_link, medium_link, hard_link)):
                provided = False

        # f"❌ Could not generate 3 unused problems after {tries} tries."
        if not provided:
            return False, None, -2

        used.add(easy_link)
        used.add(medium_link)
        used.add(hard_link)
        fs.save(fs.OLD_TABLE, used)

        entry = {
            "date": (START_DATE + timedelta(days=int(problems["idx"]))).isoformat(),
            "levels": {
                "Easy": {"url": easy_link, "solved": []},
                "Medium": {"url": medium_link, "solved": []},
                "Hard": {"url": hard_link, "solved": []}
            }
        }

        problems["total"] = str(int(problems["total"]) + 1)
        fs.save(fs.PROBLEMS_TABLE, problems)
        return True, entry, 1
    
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    def format_leaderboard(self, top_n: int=None) -> str:
        officer_usernames = {
            member.name for member in GUILD.members
            if any(role.name == OFFICER_ROLE_NAME for role in member.roles)
        }

        filtered_items = {
            uname: data for uname, data in users.items()
            if uname not in officer_usernames
        }

        sorted_pairs = sorted(filtered_items.items(), key=lambda kv: int(kv[1]['score']), reverse=True)

        last_score = None
        last_rank = 0
        lines = []

        for i, (uname, data) in enumerate(sorted_pairs, start=1):
            score = int(data['score'])
            if score == last_score:
                rank = last_rank
            else:
                rank = i
                last_score = score
                last_rank = i

            if top_n is not None and rank > top_n:
                break

            member = member_map.get(uname)
            mention = member.mention if member else uname
            pts = "point" if score == 1 else "points"
            # use ․ because normal period breaks discord markdown and makes ties not work
            lines.append(f"{rank}․ {mention} — {score} {pts}")

        return "\n".join(lines) or "No entries yet."

    async def announcement(self) -> Embed:
        current = problems["idx"]
        entry = problems[current]

        embed = Embed(
            title="📢 Problem of the Day!",
            description=f"<@&{ROLE}>",
            color=0x00b0f4
        )
        for level, data in entry['levels'].items():
            embed.add_field(name=level, value=data['url'], inline=True)

        embed.set_footer(text="Solve problems by submitting on Codeforces!")
        return embed

    @tasks.loop(time=time(hour=POST_HOUR, minute=POST_MINUTE, tzinfo=ET))
    async def daily_post(self):
        global problems
        await cf.updateCache()

        idx = str(int(problems["idx"]) + 1)
        problems["idx"] = idx
        fs.save(fs.PROBLEMS_TABLE, problems)
        if idx not in problems:
            ok, entry = await self.createEntry()
            if not ok:
                idx = str(int(problems["idx"]) - 1)
                problems["idx"] = idx
                fs.save(fs.PROBLEMS_TABLE, problems)
                return await PROBLEMS_CHANNEL.send("❌ Error creating new entry.")
            problems[idx] = entry

        embed = await self.announcement()

        top5 = self.format_leaderboard(top_n=5)
        embed.add_field(
            name="🏆 South Coding Club Leaderboard (Top 5)",
            value=top5,
            inline=False
        )

        await PROBLEMS_CHANNEL.send(
            content=f"<@&{ROLE}>",
            embed=embed,
            allowed_mentions=allowed
        )
   
    @tasks.loop(minutes=5)
    async def periodic_update(self):
        # Prepare the “now” timestamp for the embed
        timeNow = datetime.now(ET).strftime('%I:%M %p').lstrip('0')
        embed = Embed(
            title=f"New POTD Solves @ {timeNow}",
            color=0x1abc9c,
            timestamp=datetime.now(ET)
        )

        updates = []

        try:
            max_day = int(problems["idx"])
            for name in list(users):     # use list(...) in case you modify users mid-loop
                member = member_map.get(name)
                mention = member.mention if member else name

                # For each day 1..max_day, check if that user still needs to solve any level
                for i in range(1, max_day + 1):
                    entry_num = str(i)
                    entry = problems[entry_num]
                    entry_date = datetime.fromisoformat(entry["date"])
                    if entry_date > datetime.now(ET):
                        # POTD #i is not live yet
                        continue

                    for level, data in entry["levels"].items():
                        url = data["url"]
                        solved_list = data["solved"]

                        # Skip if user already solved this level
                        if any(name == x[0] for x in solved_list):
                            continue

                        contest_id, index = utils.urlVals(url)
                        ret_solved, solved_ts = await cf.checkSub(
                            users[name]["profile"], contest_id, index, "OK", "200"
                        )
                        if not ret_solved:
                            continue

                        # They *just* solved it. Compute elapsed time.
                        solve_millis = (solved_ts - entry_date.timestamp()) * 1000
                        solve_delta = timedelta(milliseconds=solve_millis)

                        parts = []
                        if solve_delta.days > 0:
                            parts.append(f"{solve_delta.days}d")
                        hours, remainder = divmod(solve_delta.seconds, 3600)
                        if hours > 0:
                            parts.append(f"{hours}h")
                        minutes, seconds = divmod(remainder, 60)
                        if minutes > 0:
                            parts.append(f"{minutes}m")
                        if seconds > 0 or not parts:
                            parts.append(f"{seconds}s")

                        formatted_time = " ".join(parts)

                        # Update in-memory data structures
                        problems[entry_num]["levels"][level]["solved"].append((name, solve_millis))
                        users[name]["solved"].append((entry_num, level, solve_millis))
                        users[name]["score"] += 1

                        updates.append(
                            f"✅ {mention} has completed POTD #{entry_num} - {level} in {formatted_time}!"
                        )

            # If we found _any_ new solves, save to disk and post them:
            if updates:
                fs.save(fs.USER_TABLE, users)
                fs.save(fs.PROBLEMS_TABLE, problems)

                for msg in updates:
                    emoji, text = msg.split(" ", 1)
                    embed.add_field(name=emoji, value=text, inline=False)

                await DISCUSSION_CHANNEL.send(embed=embed, allowed_mentions=allowed)

        except Exception as e:
            # Log the error—so you can see what went wrong—but still persist state
            logging.exception("Error in periodic_update:")
            # Even if something blew up, write out whatever was modified so far:
            fs.save(fs.USER_TABLE, users)
            fs.save(fs.PROBLEMS_TABLE, problems)


    @app_commands.command(name="potd", description="Show the Problem of the Day. Optionally, specify a past `entryNum` to view.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def _potd(self, interaction: discord.Interaction, entry_num: str=None):
        if problems["idx"] == "0":
            return await interaction.response.send_message(embed=Embed(
                description="❌ POTD has not started.",
                color=0xff0000
            ))
        
        if entry_num is None:
            entry_num = problems["idx"]

        res, type = utils.validEntry(entry_num, True)
        if not res:
            if type == -1:
                return await interaction.response.send_message(embed=Embed(
                description="❌ Cannot view future POTD yet.",
                color=0xff0000
                 ))
            else:
                return await interaction.response.send_message(embed=Embed(
                description="❌ Invalid entry number.",
                color=0xff0000
                 ))

        if not entries_enabled:
            return await interaction.response.send_message(embed=Embed(
                description="❌ POTD entries and daily announcements are paused.",
                color=0xff0000
            ))

        entry_num = str(int(entry_num)) # fix for 01 case
        entry = problems[entry_num]
        embed = Embed(
            title=f"🗓️ POTD Day {entry_num}",
            color=0x00b0f4,
            timestamp=datetime.now(ET)
        )

        for lvl, data in entry["levels"].items():
            contest_id, index = utils.urlVals(data['url'])
            embed.add_field(name=lvl, value=f"[{contest_id}{index}]({data['url']})", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.check(is_officer)
    @app_commands.command(name="add", description="(Officer) Add a POTD (either random or with specific problem links).")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def _add(self, interaction: discord.Interaction, easy_link: str=None, medium_link: str=None, hard_link: str=None):
        await interaction.response.defer()
        async with add_lock:
            success, entry = await self.createEntry(easy_link, medium_link, hard_link)
            if success:
                problems[problems["total"]] = entry; 
                await interaction.followup.send(f"✅ POTD for next entry, {problems['total']} has been created.")
            else:
                await interaction.followup.send(f"❌ Error, unable to create next POTD entry.")
        

    @app_commands.command(name="stats", description="Show your POTD progress. You can optionally view stats for another verified user by name.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def _stats(self, interaction: discord.Interaction, member: discord.Member=None):
        target = member or interaction.user
        username = target.name
        if username not in users or 'profile' not in users[username]:
            return await interaction.response.send_message("❌ Not verified.")
        stats = users[username]
        embed = Embed(
            title="📊 Stats",
            description=f"Stats for {target.mention}",
            color=0x9b59b6,
            timestamp=datetime.now(ET)
        )
        embed.add_field(name="Total Points", value=str(stats['score']), inline=False)

        order = ["Easy", "Medium", "Hard"]
        lines = []
        for entry_num in range(1, int(problems["idx"]) + 1):
            entry = problems[str(entry_num)]
            solved_emojis = []
            for level in order:
                data = entry["levels"][level]
                solved = any(username == solver[0] for solver in data["solved"])
                solved_emojis.append("✅" if solved else "❌")
            lines.append(f"**Day {entry_num}** — Easy {solved_emojis[0]}  Medium {solved_emojis[1]}  Hard {solved_emojis[2]}")

        embed.add_field(name="📈 Progress", value="\n".join(lines) or "No weeks yet!", inline=False)
        await interaction.response.send_message(embed=embed, allowed_mentions=allowed)

    @app_commands.command(name="lb", description="Show the current leaderboard with top scores.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def _lb(self, interaction: discord.Interaction):
        text = self.format_leaderboard(top_n=None)
        embed = Embed(
            title="🏆 South Coding Club Leaderboard",
            description=text,
            color=0xF1C40F,
            timestamp=datetime.now(ET)
        )
        await interaction.response.send_message(embed=embed, allowed_mentions=allowed)

    @app_commands.command(name="verify", description="Link your Codeforces account by submitting a compile error to a problem within 60 seconds.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def _verify(self, interaction: discord.Interaction, handle:str):
        await interaction.response.defer()
        target = interaction.user
        name = target.name

        if name in users:
            await interaction.followup.send(f"⚠️​​ Warning: {target.mention} is already verified as `{users[name]['profile']}`.")

        if handle is None:
            return await interaction.followup.send(f"❌ Unable to verify {target.mention}, no Codeforces handle specified. Try `/verify codeforces_username`.")

        problem = await cf.randomProb()
        if not problem:
            return await interaction.followup.send(embed=Embed(
                description="❌ Error polling Codeforces API.",
                color=0xff0000
            ))

        embed = Embed(
            title="🔒 Verification",
            description=(
                f"{target.mention}, submit a **compile error** within 60 seconds to:\n"
                f"{problem['problem_url']}\n\n"
            ),
            color=0x3498db
        )
        await interaction.followup.send(embed=embed, allowed_mentions=allowed)
        await asyncio.sleep(60)
        
        result = await cf.checkSub(handle, problem['contest_id'], problem['index'], 'COMPILATION_ERROR')
        if result[0]:
            users[name] = {'profile': handle, 'solved': [], 'score': 0}
            fs.save(fs.USER_TABLE, users)
            await interaction.followup.send(f"✅ Verified {target.mention} as Codeforces user `{handle}`!", allowed_mentions=allowed)
        else:
            await interaction.followup.send("❌ Verification failed. No matching compile error found.")

    @app_commands.check(is_officer)
    @app_commands.command(name="off", description="(Officer) Pause POTD posts and submissions.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def _off(self, interaction: discord.Interaction):        
        global entries_enabled
        entries_enabled = False
        await interaction.response.send_message("⏸️ POTD entries and daily announcements are now *paused*.")

    @app_commands.check(is_officer)
    @app_commands.command(name="on", description="(Officer) Resume POTD posts and submissions.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def _on(self, interaction: discord.Interaction):
        global entries_enabled
        entries_enabled = True
        await interaction.response.send_message("▶️ POTD entries and daily announcements are now *resumed*.")

    @app_commands.command(name="help", description="View available commands.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def help(self, interaction: discord.Interaction):
        embed = Embed(
            title="📘 POTD Bot Help",
            description="List of available commands and their usage:",
            color=0x2ecc71
        )

        embed.add_field(
            name="`/potd [entryNum]`",
            value="Show the Problem of the Day. Optionally, specify a past `entryNum` to view.",
            inline=False
        )
        embed.add_field(
            name="`/stats [name]`",
            value="Show your POTD progress. You can optionally view stats for another verified user by name.",
            inline=False
        )
        embed.add_field(
            name="`/lb`",
            value="Show the current leaderboard with top scores.",
            inline=False
        )
        embed.add_field(
            name="`/verify codeforces_username`",
            value="Link your Codeforces account by submitting a compile error to a problem within 60 seconds.",
            inline=False
        )
        embed.add_field(
            name="`/add [easy] [medium] [hard]`",
            value="(Officer) Manually add a POTD with specific problem links. If none are provided, random problems will be generated.",
            inline=False
        )
        embed.add_field(
            name="`/on` or `/off`",
            value="(Officer) Pause or resume the daily POTD postings and submissions.",
            inline=False
        )

        await interaction.response.send_message(embed=embed)
        

async def setup(bot: commands.Bot):
    await bot.add_cog(POTDCog(bot))