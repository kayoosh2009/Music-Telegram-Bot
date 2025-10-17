import json, random
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

def load_songs():
    with open("songs.json", "r", encoding="utf-8") as f:
        return json.load(f)

@router.message(F.text == "🎧 Жанры")
async def choose_genre(message: Message):
    songs = load_songs()
    genres = sorted(set(song["genre"] for song in songs))
    buttons = [[InlineKeyboardButton(text=g, callback_data=f"genre_{g}")] for g in genres]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите жанр:", reply_markup=kb)

@router.callback_query(F.data.startswith("genre_"))
async def send_genre(callback, bot):
    genre = callback.data.replace("genre_", "")
    songs = [s for s in load_songs() if s["genre"].lower() == genre.lower()]
    if not songs:
        await callback.answer("Нет песен в этом жанре 😢", show_alert=True)
        return
    song = random.choice(songs)
    await bot.send_audio(
        chat_id=callback.from_user.id,
        audio=song["url"],
        caption=f"{song['name']} — {song['artist']} ({song['genre']})"
    )
    await callback.answer() 
