import os
import json
import threading
import datetime
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = "data"
LOG_FILE = os.path.join(DATA_DIR, "log.txt")

# files names inside data/
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SONGS_FILE = os.path.join(DATA_DIR, "songs.json")
PLAYLISTS_FILE = os.path.join(DATA_DIR, "playlists.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
USER_STATE_FILE = os.path.join(DATA_DIR, "user_state.json")

os.makedirs(DATA_DIR, exist_ok=True)


def _safe_load(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # corrupted => return default (do not overwrite file here to avoid data loss)
        return default


def load_json(path, default):
    """
    path: full path (use constants above)
    default: default return type (list or dict)
    """
    return _safe_load(path, default)


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[utils.save_json] error saving {path}: {e}")


def ensure_data_files():
    """Create files with reasonable defaults if missing (without overwriting existing)."""
    if not os.path.exists(USERS_FILE):
        save_json(USERS_FILE, [])                  # list of user objects
    if not os.path.exists(SONGS_FILE):
        save_json(SONGS_FILE, [])                  # list of songs
    if not os.path.exists(PLAYLISTS_FILE):
        save_json(PLAYLISTS_FILE, [])              # list of playlists
    if not os.path.exists(STATS_FILE):
        save_json(STATS_FILE, {
            "registered_users": 0,
            "songs_played": 0,
            "songs_added": 0,
            "playlists_created": 0,
            "playlists_played": 0,
            "messages_replied": 0,
            "bot_replies": 0
        })
    if not os.path.exists(USER_STATE_FILE):
        save_json(USER_STATE_FILE, {})            # dict user_id -> state


# ----------------- user helpers -----------------
def add_user(user):
    """
    user: telebot types.User or object with .id and .username
    Adds to users.json list if not exists.
    """
    users = load_json(USERS_FILE, [])
    uid = int(user.id)
    if not any(u.get("id") == uid for u in users):
        users.append({
            "id": uid,
            "username": getattr(user, "username", "") or "",
            "first_seen": datetime.datetime.utcnow().isoformat()
        })
        save_json(USERS_FILE, users)
        update_stats("registered_users")
        log_action(f"👤 Новый пользователь добавлен: {user.username or uid}")


# ----------------- stats -----------------
def update_stats(key, amount=1):
    stats = load_json(STATS_FILE, {
        "registered_users": 0,
        "songs_played": 0,
        "songs_added": 0,
        "playlists_created": 0,
        "playlists_played": 0,
        "messages_replied": 0,
        "bot_replies": 0
    })
    stats[key] = stats.get(key, 0) + amount
    save_json(STATS_FILE, stats)


# ----------------- logging -----------------
def log_action(text):
    """Write to local log file and print to console."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {text}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[utils.log_action] cannot write log file: {e}")


def notify_log(bot, log_channel_id, text):
    """
    Send message to log channel (if valid) and write to local log.
    bot: TeleBot instance or object with send_message
    log_channel_id: possibly string; safe-cast to int
    """
    # always log locally
    log_action(text)
    if not log_channel_id:
        return
    try:
        chat = int(str(log_channel_id).strip())
    except Exception:
        return
    try:
        bot.send_message(chat, text)
    except Exception as e:
        log_action(f"⚠️ notify_log: failed to send to {chat}: {e}")


# ----------------- heartbeat -----------------
def start_heartbeat(bot, log_channel_id, initial_delay=5, interval_seconds=3600):
    """
    Periodically notifies the log channel (and local log) that bot is alive.
    initial_delay: seconds before first send
    interval_seconds: seconds between sends (default 3600 = 1 hour)
    """
    def _tick():
        notify_log(bot, log_channel_id, "💓 Бот активен и работает")
        # schedule next
        threading.Timer(interval_seconds, _tick).start()

    # schedule first tick
    threading.Timer(initial_delay, _tick).start()
