import os
from dotenv import load_dotenv
from telebot import TeleBot
from handlers import register_handlers
from utils import log_action, start_heartbeat

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

bot = TeleBot(BOT_TOKEN)

register_handlers(bot)
start_heartbeat(bot, LOG_CHANNEL_ID)

if __name__ == "__main__":
    log_action(bot, LOG_CHANNEL_ID, "✅ Бот запущен и готов к работе")
    bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
