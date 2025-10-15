import logging
from aiogram import Bot, Dispatcher, executor, types
from config import TELEGRAM_BOT_TOKEN
from handlers.start_menu import start_handler, language_choice_handler, menu_handler
from handlers.upload import (
    upload_start_handler,
    audio_received_handler,
    name_handler,
    artist_handler,
    genre_handler,
    UploadStates,
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# --- Команды ---
dp.register_message_handler(start_handler, commands=["start"])
dp.register_message_handler(language_choice_handler, lambda m: m.text in ["Русский", "English"])
dp.register_message_handler(menu_handler, lambda m: m.text.lower() in [
    "слушать музыку", "listen music", "загрузить свой трек", "upload your track"
])

# --- Загрузка треков ---
dp.register_message_handler(upload_start_handler, commands=["upload"], state="*")
dp.register_message_handler(audio_received_handler, content_types=types.ContentType.AUDIO, state=UploadStates.waiting_for_audio)
dp.register_message_handler(name_handler, state=UploadStates.waiting_for_name)
dp.register_message_handler(artist_handler, state=UploadStates.waiting_for_artist)
dp.register_message_handler(genre_handler, state=UploadStates.waiting_for_genre)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
