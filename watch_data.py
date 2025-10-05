# watch_data.py
import json
import os

WATCH_FILE = os.path.expanduser("~/.anime_watch_data.json")

def save_watch_data(anime_name: str, episode_file: str, position_ms: int = 0):
    data = {}
    if os.path.exists(WATCH_FILE):
        with open(WATCH_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    data[anime_name] = {
        "episode": episode_file,
        "position_ms": position_ms
    }
    os.makedirs(os.path.dirname(WATCH_FILE), exist_ok=True)
    with open(WATCH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_watch_data(anime_name: str):
    if not os.path.exists(WATCH_FILE):
        return None
    with open(WATCH_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if anime_name in data:
        entry = data[anime_name]
        return entry.get("episode", ""), entry.get("position_ms", 0)
    return None
