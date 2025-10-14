import os

# Env vars (from GitHub secrets)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID")) if os.getenv("LOGS_CHANNEL_ID") else None
ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID")) if os.getenv("ARCHIVE_CHANNEL_ID") else None
ADMIN_USER_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()]

TMP_DOWNLOAD_DIR = "/tmp/musicbot_files"

GENRES = [
    "LoFi",
    "Electronic",
    "Rock",
    "Pop",
    "Trap",
    "Chill",
    "Jazz",
    "Classical",
    "Game OST",
    "Other",
]

# Basic checks (do not raise in GitHub Actions; they will be caught at runtime)
if not TELEGRAM_BOT_TOKEN:
    print("Warning: TELEGRAM_BOT_TOKEN not set.")
if not FIREBASE_SERVICE_ACCOUNT_JSON:
    print("Warning: FIREBASE_SERVICE_ACCOUNT_JSON not set.")
if not FIREBASE_STORAGE_BUCKET:
    print("Warning: FIREBASE_STORAGE_BUCKET not set.")
