import json

USER_TABLE = 'data/users.json'
PROBLEMS_TABLE = 'data/problems.json'
OLD_TABLE = 'data/old.json'
CACHE_TABLE = 'data/cache.json'

def load(table):
    try:
        with open(table, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save(table, data):
    with open(table, 'w') as f:
        json.dump(list(data) if isinstance(data, set) else data, f, indent=4)