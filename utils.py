import os
import json
import threading
import time
from datetime import datetime
from dotenv import load_dotenv

# ======================================
# Загрузка .env
# ======================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID", "0"))

# ======================================
# Пути к файлам
# ======================================
USERS_FILE = "user.json"
SONGS_FILE = "songs.json"
STATS_FILE = "stats.json"
PLAYLISTS_FILE = "playlists.json"

# ======================================
# Автоматическое создание файлов при запуске
# ======================================
def ensure_files():
    """Создаёт все нужные файлы, если их нет"""
    for file in [USERS_FILE, SONGS_FILE, STATS_FILE, PLAYLISTS_FILE]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                if file == STATS_FILE:
                    json.dump({
                        "registered_users": 0,
                        "songs_played": 0,
                        "songs_added": 0,
                        "playlists_created": 0,
                        "playlists_played": 0,
                        "messages_replied": 0
                    }, f, ensure_ascii=False, indent=2)
                else:
                    json.dump([], f, ensure_ascii=False, indent=2)

ensure_files()

# ======================================
# Работа с JSON
# ======================================
def load_json(filename, default=None):
    if not os.path.exists(filename):
        return default or []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default or []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================================
# Пользователи
# ======================================
def add_user(user):
    users = load_json(USERS_FILE, [])
    if not any(u["id"] == user.id for u in users):
        users.append({
            "id": user.id,
            "username": user.username or "аноним",
            "first_seen": datetime.utcnow().isoformat()
        })
        save_json(USERS_FILE, users)
        update_stats("registered_users", 1)
        print(f"[NEW USER] @{user.username or 'аноним'} ({user.id})")

# ======================================
# Статистика
# ======================================
def update_stats(key, amount=1):
    stats = load_json(STATS_FILE, {})
    if key not in stats:
        stats[key] = 0
    stats[key] += amount
    save_json(STATS_FILE, stats)

# ======================================
# Логирование
# ======================================
def log_action(bot, log_chat, text):
    """Отправляет сообщение в лог-канал и выводит в консоль"""
    if not text:
        return
    try:
        if log_chat:
            bot.send_message(log_chat, text)
        print(f"[LOG] {text}")
    except Exception as e:
        print(f"[LOG ERROR] {e}")

# ======================================
# Heartbeat (проверка активности)
# ======================================
def start_heartbeat(bot, log_chat):
    """Периодически сообщает, что бот жив"""
    def loop():
        while True:
            try:
                msg = f"💓 Бот активен — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                log_action(bot, log_chat, msg)
            except Exception as e:
                print(f"[HEARTBEAT ERROR] {e}")
            time.sleep(60)  # каждые 60 секунд

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()

# ======================================
# Вспомогательная функция для песен
# ======================================
def format_song(song):
    return f"🎧 <b>{song.get('name')}</b>\n👤 {song.get('artist')}\n🎼 {song.get('genre')} | 🌐 {song.get('lang')}"

# ======================================
# Отладочная печать статистики
# ======================================
def print_stats():
    stats = load_json(STATS_FILE, {})
    print("📊 Текущая статистика:")
    for k, v in stats.items():
        print(f" - {k}: {v}")
