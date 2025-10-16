from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import json

# Загружаем конфиг
with open("config.json", "r") as f:
    config = json.load(f)

bot = Bot(token=config["bot_token"])
dp = Dispatcher(bot)

# Временное хранилище
user_data = {}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("🎶 Добро пожаловать! Отправьте аудиофайл, чтобы предложить песню в архив.")

@dp.message_handler(content_types=types.ContentType.AUDIO)
async def handle_audio(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {"file_id": message.audio.file_id}
    await message.answer("✅ Аудио получено!\nТеперь напишите название песни:")

@dp.message_handler(lambda msg: msg.from_user.id in user_data and "title" not in user_data[msg.from_user.id])
async def get_title(message: types.Message):
    user_data[message.from_user.id]["title"] = message.text
    await message.answer("✍️ Кто автор песни?")

@dp.message_handler(lambda msg: "title" in user_data[msg.from_user.id] and "artist" not in user_data[msg.from_user.id])
async def get_artist(message: types.Message):
    user_data[message.from_user.id]["artist"] = message.text
    await message.answer("🎼 Какой жанр?")

@dp.message_handler(lambda msg: "artist" in user_data[msg.from_user.id] and "genre" not in user_data[msg.from_user.id])
async def get_genre(message: types.Message):
    user_data[msg.from_user.id]["genre"] = message.text
    await message.answer("🌍 На каком языке песня?")

@dp.message_handler(lambda msg: "genre" in user_data[msg.from_user.id] and "language" not in user_data[msg.from_user.id])
async def get_language(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["language"] = message.text

    song_json = json.dumps(user_data[user_id], indent=2, ensure_ascii=False)

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Разрешить", callback_data=f"approve_{user_id}")
    )

    await bot.send_message(
        config["log_channel_id"],
        f"🎵 Новая песня от @{message.from_user.username or 'пользователя'}:\n\n<pre>{song_json}</pre>\n\n{config['admin_username']}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await message.answer("🎧 Спасибо! Песня отправлена на модерацию.")
    user_data[user_id]["audio_message_id"] = message.message_id

@dp.callback_query_handler(lambda c: c.data.startswith("approve_"))
async def approve_song(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    data = user_data.get(user_id)

    if data:
        await bot.forward_message(
            config["archive_channel_id"],
            from_chat_id=callback.message.chat.id,
            message_id=data["audio_message_id"]
        )
        await callback.answer("✅ Песня добавлена в архив!")
    else:
        await callback.answer("⚠️ Ошибка: данные не найдены.")

if __name__ == "__main__":
    executor.start_polling(dp)
