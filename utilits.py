import json
import os
import random
import time
from typing import List, Dict, Optional

from telebot import TeleBot, types

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SONGS_FILE = os.path.join(DATA_DIR, "songs.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
PLAYLIST_FILE = os.path.join(DATA_DIR, "playlist.json")

# --- JSON helpers ---
def load_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Songs / search / playlists ---
def get_all_songs() -> List[Dict]:
    return load_json(SONGS_FILE)

def get_random_song() -> Optional[Dict]:
    songs = get_all_songs()
    if not songs:
        return None
    return random.choice(songs)

def get_genres() -> List[str]:
    songs = get_all_songs()
    genres = sorted({s.get("genre", "Unknown") for s in songs})
    return genres

def get_songs_by_genre(genre: str) -> List[Dict]:
    songs = get_all_songs()
    return [s for s in songs if s.get("genre", "").lower() == genre.lower()]

def search_songs(query: str) -> List[Dict]:
    q = query.lower().strip()
    results = []
    songs = get_all_songs()
    for s in songs:
        if q in s.get("name", "").lower() or q in s.get("artist", "").lower() or q in s.get("genre", "").lower() or q in s.get("lang", "").lower():
            results.append(s)
    return results

def add_song_metadata(song_meta: Dict) -> Dict:
    """
    Add metadata to songs.json and return the stored object (with id).
    Expects song_meta to include: name, artist, genre, lang, url (file_id or archive link), archive_url (optional)
    """
    songs = get_all_songs()
    next_id = (max((s.get("id", 0) for s in songs), default=0) + 1) if songs else 1
    song_meta = dict(song_meta)
    song_meta["id"] = next_id
    songs.append(song_meta)
    save_json(SONGS_FILE, songs)
    return song_meta

def extract_file_id_from_url(url: str) -> Optional[str]:
    """
    Accepts url like "file_id:ABC..." or a direct file_id and returns the file id string.
    """
    if not url:
        return None
    if url.startswith("file_id:"):
        return url.split("file_id:", 1)[1]
    return url

# --- Users & stats ---
def record_user(user_obj: dict):
    users = load_json(USERS_FILE)
    user_ids = {u.get("id") for u in users}
    if user_obj.get("id") not in user_ids:
        users.append(user_obj)
        save_json(USERS_FILE, users)

def update_stats(action: str):
    stats = load_json(STATS_FILE) or {}
    stats.setdefault("total_actions", 0)
    stats["total_actions"] += 1
    stats.setdefault("last_action", "")
    stats["last_action"] = action
    stats.setdefault("last_updated", int(time.time()))
    save_json(STATS_FILE, stats)

# --- Logging to LOG_CHANNEL ---
def log_action(bot: TeleBot, text: str):
    """
    Sends a log message to the configured LOG_CHANNEL_ID read from env in bot code.
    We purposely avoid importing env vars here to keep this module testable.
    """
    # Try to get LOG_CHANNEL_ID from bot.user_data if set, else env lookup
    import os
    log_id = os.getenv("LOG_CHANNEL_ID")
    if log_id:
        try:
            bot.send_message(int(log_id), text)
        except Exception as e:
            print("log_action failed:", e)
    else:
        print("LOG_CHANNEL_ID not configured; log:", text)
