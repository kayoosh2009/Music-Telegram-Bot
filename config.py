import os
from pathlib import Path

# ---------------------------
# Telegram Bot
# ---------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ---------------------------
# Channels
# ---------------------------
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID", "-1003086244737"))
ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID", "-1003197881242"))

# ---------------------------
# Admins
# ---------------------------
ADMIN_USER_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x]

# ---------------------------
# Firebase
# ---------------------------
import json

FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if FIREBASE_SERVICE_ACCOUNT_JSON is None:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON not set in environment variables")

try:
    FIREBASE_CREDENTIALS = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
except json.JSONDecodeError as e:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON: " + str(e))

FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", FIREBASE_CREDENTIALS.get("storageBucket"))

# ---------------------------
# Temp download folder
# ---------------------------
TMP_DOWNLOAD_DIR = Path("tmp_tracks")
TMP_DOWNLOAD_DIR.mkdir(exist_ok=True, parents=True)
