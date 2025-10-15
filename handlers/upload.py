from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from song_utils import add_song, load_songs

class UploadStates(StatesGroup):
    waiting_for_audio = State()
    waiting_for_name = State()
    waiting_for_artist = State()
    waiting_for_genre = State()

async def upload_start_handler(message: types.Message):
    await message.answer("🎵 Пришли мне аудио-файл, чтобы загрузить трек.")
    await UploadStates.waiting_for_audio.set()

async def audio_received_handler(message: types.Message, state: FSMContext):
    if not message.audio:
        await message.answer("⚠️ Это не аудио. Пришли аудиофайл.")
        return

    await state.update_data(file_id=message.audio.file_id)
    await message.answer("Введите название трека:")
    await UploadStates.waiting_for_name.set()

async def name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите исполнителя:")
    await UploadStates.waiting_for_artist.set()

async def artist_handler(message: types.Message, state: FSMContext):
    await state.update_data(artist=message.text)
    await message.answer("Введите жанр:")
    await UploadStates.waiting_for_genre.set()

async def genre_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data["name"]
    artist = user_data["artist"]
    file_id = user_data["file_id"]
    genre = message.text

    songs = load_songs()
    song_id = len(songs) + 1
    add_song(song_id, name, artist, genre, file_id)

    await message.answer(f"✅ Трек добавлен!\n\nID: {song_id}\nНазвание: {name}\nИсполнитель: {artist}\nЖанр: {genre}")
    await state.finish()
