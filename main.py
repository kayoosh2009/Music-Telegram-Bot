import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart

from config import TELEGRAM_BOT_TOKEN, ADMIN_USER_IDS
from handlers.start_menu import start_handler, language_choice_handler
from handlers.upload import upload_start_handler, audio_received_handler, name_handler, artist_handler, genre_handler, UploadStates
from handlers.player import listen_music_handler, genre_choice_handler, callback_player

from keyboards import KB_LANG, KB_MENU_RU, KB_MENU_EN
from config import GENRES

import logging
logging.basicConfig(level=logging.INFO)

if not TELEGRAM_BOT_TOKEN:
    print("TELEGRAM_BOT_TOKEN not provided. Exiting.")
    exit(1)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: types.FSMContext):
    await start_handler(message, state)

@dp.message()
async def all_messages_handler(message: types.Message, state: types.FSMContext):
    text = message.text or ""
    text = text.strip()

    # Language selection
    if text.lower() in ["русский", "english"]:
        await language_choice_handler(message, state)
        return

    # Main menu
    if text in ["🎧 Слушать музыку", "🎧 Listen music"]:
        await listen_music_handler(message, state)
        return

    if text in ["⬆️ Загрузить свой трек", "⬆️ Upload your track"]:
        await upload_start_handler(message, state)
        return

    # Genres
    if text in GENRES:
        await genre_choice_handler(message, state)
        return

    # Upload flow states handlers
    st = await state.get_state()
    if st == UploadStates.waiting_for_name.state:
        await name_handler(message, state)
        return
    if st == UploadStates.waiting_for_artist.state:
        await artist_handler(message, state)
        return
    if st == UploadStates.waiting_for_genre.state:
        await genre_handler(message, state)
        return

@dp.message(lambda message: message.audio or message.document)
async def handle_audio(message: types.Message, state: types.FSMContext):
    await audio_received_handler(message, state)

@dp.callback_query()
async def handle_callback(cb: types.CallbackQuery, state: types.FSMContext):
    await callback_player(cb, state)

async def main():
    print("Bot starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
