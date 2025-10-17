from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Bot
from config import ARCHIVE_CHANNEL_ID, LOG_CHANNEL_ID

router = Router()

class SuggestSong(StatesGroup):
    waiting_audio = State()
    waiting_name = State()
    waiting_artist = State()
    waiting_genre = State()
    waiting_lang = State()

@router.message(F.text == "🎤 Предложить песню")
async def suggest_start(message: Message, state: FSMContext):
    await message.answer("🎶 Пришлите аудиофайл песни (mp3, wav и т.п.)")
    await state.set_state(SuggestSong.waiting_audio)

@router.message(SuggestSong.waiting_audio, F.audio)
async def get_audio(message: Message, state: FSMContext):
    await state.update_data(audio=message.audio.file_id)
    await message.answer("📛 Введите название песни:")
    await state.set_state(SuggestSong.waiting_name)

@router.message(SuggestSong.waiting_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("👤 Введите имя артиста:")
    await state.set_state(SuggestSong.waiting_artist)

@router.message(SuggestSong.waiting_artist)
async def get_artist(message: Message, state: FSMContext):
    await state.update_data(artist=message.text)
    await message.answer("🎧 Введите жанр:")
    await state.set_state(SuggestSong.waiting_genre)

@router.message(SuggestSong.waiting_genre)
async def get_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await message.answer("🌐 Введите язык песни (например: English, Russian):")
    await state.set_state(SuggestSong.waiting_lang)

@router.message(SuggestSong.waiting_lang)
async def get_lang(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    audio_id = data["audio"]

    sent_audio = await bot.send_audio(
        chat_id=ARCHIVE_CHANNEL_ID,
        audio=audio_id,
        caption=f"{data['name']} — {data['artist']} ({data['genre']})"
    )

    archive_url = f"https://t.me/c/{str(sent_audio.chat.id)[4:]}/{sent_audio.message_id}"

    json_entry = {
        "id": sent_audio.message_id,
        "name": data["name"],
        "artist": data["artist"],
        "genre": data["genre"],
        "lang": message.text,
        "url": archive_url
    }

    await bot.send_message(
        LOG_CHANNEL_ID,
        f"🎵 Новая песня от @{message.from_user.username or 'аноним'}\n\n"
        f"```json\n{json_entry}\n```"
    )

    await message.answer("✅ Спасибо! Ваша песня отправлена на модерацию 🎶")
    await state.clear() 
