import aiohttp
import random
import re
import fs
import logging

# Global session, initially None
session: aiohttp.ClientSession | None = None
cachedProblems: list[dict] = []

async def get_session() -> aiohttp.ClientSession:
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()
    return session

async def shutdown() -> None:
    global session
    if session is not None and not session.closed:
        await session.close()
    session = None

def validLink(link: str) -> bool:
    return bool(re.match(r"https://codeforces\.com/contest/\d+/problem/[A-Z]\d*", link))

async def updateCache() -> None:
    global cachedProblems
    sess = await get_session()
    api_url = "https://codeforces.com/api/problemset.problems"
    async with sess.get(api_url) as resp:
        if resp.status != 200:
            logging.error("Unable to update cache - polling Codeforces failed")
            return
        payload = await resp.json()
        cachedProblems = payload["result"]["problems"]
        fs.save(fs.CACHE_TABLE, cachedProblems)

async def randomProb(minRating: int = 800, maxRating: int = 3500, tags: list[str] | None = None, after: int = 1624) -> dict | None:
    if not cachedProblems:
        return None

    candidates = []
    for p in cachedProblems:
        if p["contestId"] < after:
            continue
        rating = p.get("rating", 0)
        if minRating <= rating <= maxRating and (tags is None or any(t in p["tags"] for t in tags)):
            candidates.append({
                "problem_url": f"https://codeforces.com/contest/{p['contestId']}/problem/{p['index']}",
                "contest_id":  p["contestId"],
                "index":       p["index"],
                "rating":      rating
            })

    return random.choice(candidates) if candidates else None

async def checkSub(username: str,contest_id: int, index: str, verdict: str, count: int = 200) -> tuple[bool, int]:
    sess = await get_session()
    url = f"https://codeforces.com/api/user.status?handle={username}&from=1&count={count}"
    async with sess.get(url) as resp:
        if resp.status != 200:
            logging.error("Unable to check new submissions - polling Codeforces failed")
            return False, -1
        data = await resp.json()
        for sub in data.get("result", []):
            if sub.get("verdict") is None:
                continue
                
            if (sub["problem"]["contestId"] == contest_id and
                sub["problem"]["index"] == index and
                sub["verdict"] == verdict):
                return True, sub["creationTimeSeconds"]
        return False, -1