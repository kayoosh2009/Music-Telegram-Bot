from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, bot
from config import ADMIN_USER_IDS

class UploadStates(StatesGroup):
    waiting_for_audio = State()
    waiting_for_name = State()
    waiting_for_artist = State()
    waiting_for_genre = State()

@dp.message_handler(commands=["upload"])
async def upload_start_handler(message: types.Message):
    await message.answer("Отправь аудио файл или ссылку на песню 🎵")
    await UploadStates.waiting_for_audio.set()

@dp.message_handler(content_types=[types.ContentType.AUDIO, types.ContentType.DOCUMENT], state=UploadStates.waiting_for_audio)
async def audio_received_handler(message: types.Message, state: FSMContext):
    file_id = message.audio.file_id if message.audio else message.document.file_id
    await state.update_data(audio=file_id)
    await message.answer("Введи название песни:")
    await UploadStates.waiting_for_name.set()

@dp.message_handler(state=UploadStates.waiting_for_name)
async def name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Кто исполнитель?")
    await UploadStates.waiting_for_artist.set()

@dp.message_handler(state=UploadStates.waiting_for_artist)
async def artist_handler(message: types.Message, state: FSMContext):
    await state.update_data(artist=message.text)
    await message.answer("Какой жанр?")
    await UploadStates.waiting_for_genre.set()

@dp.message_handler(state=UploadStates.waiting_for_genre)
async def genre_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_data["genre"] = message.text

    text = (
        f"🎶 *Новая песня от пользователя {message.from_user.full_name}*\n\n"
        f"Название: {user_data['name']}\n"
        f"Исполнитель: {user_data['artist']}\n"
        f"Жанр: {user_data['genre']}\n"
        f"ID пользователя: {message.from_user.id}"
    )

    for admin_id in ADMIN_USER_IDS:
        await bot.send_message(admin_id, text, parse_mode="Markdown")
        if "audio" in user_data:
            await bot.send_audio(admin_id, user_data["audio"])

    await message.answer("✅ Песня отправлена администратору на рассмотрение.")
    await state.finish()
