import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID ваших каналов (можно получить через @username_to_id_bot)
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID", 0))
