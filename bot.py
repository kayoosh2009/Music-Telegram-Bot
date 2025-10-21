import os
from dotenv import load_dotenv
from telebot import TeleBot
from handlers import register_handlers
from utils import notify_log, start_heartbeat, ensure_data_files

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")  # may be string; utils will handle int conversion

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN is not set in .env")

# prepare data files
ensure_data_files()

bot = TeleBot(BOT_TOKEN)

# register handlers (this binds all message handlers to the bot)
register_handlers(bot)

# start heartbeat (will safely handle missing/invalid LOG_CHANNEL_ID)
start_heartbeat(bot, LOG_CHANNEL_ID)

if __name__ == "__main__":
    notify_log(bot, LOG_CHANNEL_ID, "✅ Бот запущен и готов к работе")
    bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
