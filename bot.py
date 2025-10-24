import os
import threading
import time
from dotenv import load_dotenv
import telebot

from utilits import log_action

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID", 0))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# Import handlers after bot is created to avoid circular import issues
import handlers  # noqa: E402 (handlers will import `bot`)

# Heartbeat thread: sends a message to LOG_CHANNEL_ID every minute with remaining time
def heartbeat_thread(total_minutes=24 * 60):
    remaining = total_minutes
    try:
        while remaining >= 0:
            hours = remaining // 60
            mins = remaining % 60
            text = f"⏱ Host uptime countdown — remaining: {hours}h {mins}m"
            try:
                bot.send_message(LOG_CHANNEL_ID, text)
            except Exception as e:
                # If logging fails, print to console (so you can debug hosting issues)
                print("Failed to send heartbeat to LOG channel:", e)
            remaining -= 1
            time.sleep(60)
        # final message
        try:
            bot.send_message(LOG_CHANNEL_ID, "⚠️ Hosting session ended (24h reached).")
        except Exception as e:
            print("Failed to send final heartbeat:", e)
    except Exception as e:
        print("Heartbeat thread error:", e)

def start_heartbeat():
    t = threading.Thread(target=heartbeat_thread, daemon=True)
    t.start()
    log_action(bot, "Heartbeat thread started")

if __name__ == "__main__":
    start_heartbeat()
    log_action(bot, "Bot started")
    print("Bot polling started...")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        log_action(bot, "Bot stopped by KeyboardInterrupt")
    except Exception as e:
        log_action(bot, f"Bot stopped with error: {e}")
        raise
