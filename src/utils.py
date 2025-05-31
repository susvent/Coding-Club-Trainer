import main
from datetime import datetime, timedelta

def urlVals(url):
    parts = url.split('/')
    contest_id = int(parts[4])
    index = parts[6]
    return contest_id, index

def readify(ms:int):
    td = timedelta(milliseconds=ms)
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds or not parts: parts.append(f"{seconds}s")

    return " ".join(parts)

def validEntry(entryNum:str, future:bool=False):
    try:
        entryNum = int(entryNum)
        if ((future and entryNum > int(main.problems["idx"]))):
            return False, -1
        if (entryNum <= 0):
            return False, -2
    except Exception as e:
        return False, -3
    
    return True, 1