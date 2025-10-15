from aiogram import types
from aiogram.dispatcher import FSMContext
from keyboards import KB_LANG, KB_MENU_RU, KB_MENU_EN, KB_GENRES
from handlers.upload import upload_start_handler
from handlers.player import genre_selected_handler

async def start_handler(message: types.Message):
    await message.answer("🌐 Выберите язык / Choose language", reply_markup=KB_LANG)

async def language_choice_handler(message: types.Message, state: FSMContext):
    if message.text == "Русский":
        await message.answer("Что будем слушать сегодня?", reply_markup=KB_MENU_RU)
    elif message.text == "English":
        await message.answer("What do you want to listen today?", reply_markup=KB_MENU_EN)
    else:
        await message.answer("❌ Выберите язык / Choose language")

async def menu_handler(message: types.Message):
    text = message.text.lower()
    if text in ["слушать музыку", "listen music"]:
        await message.answer("Выберите жанр:", reply_markup=KB_GENRES)
    elif text in ["загрузить свой трек", "upload your track"]:
        await upload_start_handler(message)
    else:
        await message.answer("❌ Неизвестная команда.")
