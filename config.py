import json
import os

SECRETS_FILE = "secrets.json"

if not os.path.exists(SECRETS_FILE):
    raise FileNotFoundError(f"{SECRETS_FILE} не найден! Создай его в корне проекта.")

with open(SECRETS_FILE, "r") as f:
    secrets = json.load(f)

TELEGRAM_BOT_TOKEN = secrets["TELEGRAM_BOT_TOKEN"]
ADMIN_USER_IDS = secrets["ADMIN_USER_IDS"]
SONGS_CHANNEL_ID = secrets.get("SONGS_CHANNEL_ID")
LOGS_CHANNEL_ID = secrets.get("LOGS_CHANNEL_ID")

SONGS_FILE = "songs.json"  # файл с песнями, который редактируешь только ты
