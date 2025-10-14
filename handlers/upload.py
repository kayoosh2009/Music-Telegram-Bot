import pathlib
from aiogram import types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from config import TMP_DOWNLOAD_DIR, ARCHIVE_CHANNEL_ID, LOGS_CHANNEL_ID, ADMIN_USER_IDS
from texts import TEXTS, TEXTS_EN
from firebase_utils import upload_file_to_storage, save_track_metadata
from keyboards import genres_keyboard

pathlib.Path(TMP_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

class UploadStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_name = State()
    waiting_for_artist = State()
    waiting_for_genre = State()

async def upload_start_handler(message: types.Message, state: FSMContext):
    if ADMIN_USER_IDS and message.from_user.id not in ADMIN_USER_IDS:
        await message.reply(TEXTS["only_admin"] if (await state.get_data()).get("lang", "ru") == "ru" else TEXTS_EN["only_admin"])
        return
    await message.reply("Пришлите аудиофайл (mp3/ogg) или документ Telegram с треком:")
    await state.set_state(UploadStates.waiting_for_file)

async def audio_received_handler(message: types.Message, state: FSMContext):
    if not (message.audio or message.document):
        await message.reply("Пожалуйста, пришлите аудиофайл.")
        return
    file = message.audio or message.document
    file_id = file.file_id
    local_path = f"{TMP_DOWNLOAD_DIR}/{file_id}"
    await message.bot.download(file=file, destination=local_path)
    await state.update_data(local_file_path=local_path)
    await message.reply(TEXTS["ask_name"])
    await state.set_state(UploadStates.waiting_for_name)

async def name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.reply(TEXTS["ask_artist"])
    await state.set_state(UploadStates.waiting_for_artist)

async def artist_handler(message: types.Message, state: FSMContext):
    await state.update_data(artist=message.text.strip())
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await message.reply(TEXTS["ask_genre"] if lang == "ru" else TEXTS_EN["ask_genre"], reply_markup=genres_keyboard(lang))
    await state.set_state(UploadStates.waiting_for_genre)

async def genre_handler(message: types.Message, state: FSMContext):
    genre = message.text.strip()
    data = await state.get_data()
    local_path = data.get("local_file_path")
    name = data.get("name")
    artist = data.get("artist")
    lang = data.get("lang", "ru")
    if not all([local_path, name, artist]):
        await message.reply("Что-то пошло не так — начните загрузку заново.")
        await state.clear()
        return

    dest_name = f"tracks/{pathlib.Path(local_path).name}"
    try:
        public_url = upload_file_to_storage(local_path, dest_name)
    except Exception as e:
        await message.reply("Ошибка загрузки в Firebase: " + str(e))
        await state.clear()
        return

    caption = f"ID: pending\nNAME: {name}\nARTIST: {artist}\nGENRE: {genre}"
    try:
        await message.bot.send_audio(chat_id=ARCHIVE_CHANNEL_ID, audio=FSInputFile(local_path), caption=caption)
    except Exception as e:
        # still continue: store metadata
        print("Archive send error:", e)

    metadata = {
        "name": name,
        "artist": artist,
        "genre": genre,
        "storage_url": public_url,
    }
    try:
        doc_id = save_track_metadata(metadata)
    except Exception as e:
        await message.reply("Ошибка сохранения метаданных: " + str(e))
        await state.clear()
        return

    # Optionally log
    try:
        await message.bot.send_message(LOGS_CHANNEL_ID, f"User {message.from_user.id} uploaded track {name} ({doc_id})")
    except Exception:
        pass

    await message.reply(TEXTS["upload_done"] if lang == "ru" else TEXTS_EN["upload_done"], reply_markup=types.ReplyKeyboardRemove())
    await state.clear()
