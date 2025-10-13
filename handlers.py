import json
import logging
import os
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

router = Router()
logger = logging.getLogger(__name__)

ADMIN_ID = int(os.getenv("ADMIN_ID"))
LOGS_ID = os.getenv("LOGS_ID")
SONGS_FILE = "songs.json"


# --- FSM для добавления песен ---
class AddSong(StatesGroup):
    waiting_for_info = State()


class MessageAdmin(StatesGroup):
    waiting_for_text = State()


# --- Работа с songs.json ---
def load_songs():
    try:
        with open(SONGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.error(f"Ошибка загрузки песен: {e}")
        return []


def save_songs(data):
    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


songs = load_songs()


# --- Главное меню ---
def genre_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎧 Lofi", callback_data="genre_lofi")],
        [InlineKeyboardButton(text="💫 Synthwave", callback_data="genre_synthwave")],
        [InlineKeyboardButton(text="🔥 Other", callback_data="genre_other")]
    ])


# --- Команда /start ---
@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "⚡️ Бот работает на бесплатном хостинге Render, "
        "поэтому может запускаться с задержкой до 60 секунд ⏳\n\n"
        "🎶 Привет! Выбери жанр музыки:",
        reply_markup=genre_keyboard()
    )


# --- Команда /menu ---
@router.message(Command("menu"))
async def menu_cmd(message: types.Message, bot):
    chat_id = message.chat.id
    # Удаляем последние 50 сообщений
    for msg_id in range(message.message_id, message.message_id - 50, -1):
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    await bot.send_message(chat_id, "🎵 Главное меню:", reply_markup=genre_keyboard())


# --- Команда /admin ---
@router.message(Command("admin"))
async def contact_admin(message: types.Message, state: FSMContext):
    await message.reply("✉️ Напиши сообщение админу:")
    await state.set_state(MessageAdmin.waiting_for_text)


@router.message(MessageAdmin.waiting_for_text)
async def forward_to_admin(message: types.Message, bot, state: FSMContext):
    text = f"📩 Сообщение админу:\nОт: @{message.from_user.username or message.from_user.full_name}\n\n{text}"
    await bot.send_message(ADMIN_ID, text)
    await message.reply("✅ Сообщение отправлено админу.")
    await state.clear()


# --- Получение аудио от админа ---
@router.message(F.audio)
async def handle_audio(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ У вас нет прав добавлять песни.")
        return

    file_id = message.audio.file_id
    await state.update_data(file_id=file_id)
    await message.reply(
        "🎵 Отправь данные о песне в формате:\n\n"
        "`NAME: ...`\n`ARTIST: ...`\n`GENRE: ...`",
        parse_mode="Markdown"
    )
    await state.set_state(AddSong.waiting_for_info)


# --- Получаем описание песни от админа ---
@router.message(AddSong.waiting_for_info)
async def get_song_info(message: types.Message, state: FSMContext, bot):
    data = await state.get_data()
    file_id = data["file_id"]

    lines = message.text.strip().split("\n")
    song_info = {"id": len(songs) + 1, "file_id": file_id}

    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        song_info[key.strip().lower()] = value.strip()

    if not all(k in song_info for k in ("name", "artist", "genre")):
        await message.reply("⚠️ Ошибка: нужно указать NAME, ARTIST и GENRE.")
        return

    # Проверка на дубликат
    for s in songs:
        if s["name"].lower() == song_info["name"].lower():
            s.update(song_info)
            save_songs(songs)
            await message.reply(f"🔁 Песня обновлена: *{s['name']}*", parse_mode="Markdown")
            await state.clear()
            return

    songs.append(song_info)
    save_songs(songs)

    await message.reply(f"✅ Песня добавлена: *{song_info['name']}* — {song_info['artist']}",
                        parse_mode="Markdown")

    # лог в канал
    try:
        await bot.send_message(
            LOGS_ID,
            f"🎵 Добавлена новая песня:\n"
            f"ID: {song_info['id']}\n"
            f"Название: {song_info['name']}\n"
            f"Исполнитель: {song_info['artist']}\n"
            f"Жанр: {song_info['genre']}"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить лог: {e}")

    await state.clear()


# --- Выбор жанра ---
@router.callback_query(lambda c: c.data.startswith("genre_"))
async def select_genre(callback: types.CallbackQuery):
    genre = callback.data.split("_", 1)[1]
    genre_songs = [s for s in songs if s["genre"].lower() == genre.lower()]

    if not genre_songs:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться", callback_data="go_back")]
        ])
        await callback.message.edit_text(
            f"😕 Песни в жанре *{genre}* пока не найдены.",
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

    song = genre_songs[0]
    caption = f"🎵 <b>{song['name']}</b>\n👤 <i>{song['artist']}</i>\n🎧 Жанр: {song['genre']}"
    buttons = [
        [InlineKeyboardButton(text="▶️ Слушать", callback_data=f"play_{song['id']}")],
        [InlineKeyboardButton(text="📥 Импортировать", callback_data=f"import_{song['id']}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="go_back")]
    ]
    await callback.message.edit_text(caption, parse_mode="HTML",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# --- Возврат к выбору жанров ---
@router.callback_query(lambda c: c.data == "go_back")
async def go_back(callback: types.CallbackQuery):
    await callback.message.edit_text("🎶 Выбери жанр:", reply_markup=genre_keyboard())


# --- Прослушивание песни ---
@router.callback_query(lambda c: c.data.startswith("play_"))
async def play_song(callback: types.CallbackQuery):
    song_id = int(callback.data.split("_", 1)[1])
    song = next((s for s in songs if s["id"] == song_id), None)

    if not song:
        await callback.answer("❌ Ошибка: песня не найдена.", show_alert=True)
        return

    await callback.message.answer_audio(
        audio=song["file_id"],
        caption=f"🎧 Сейчас играет: <b>{song['name']}</b>\n👤 {song['artist']}",
        parse_mode="HTML"
    )

    await callback.answer("▶️ Воспроизведение началось")
