import json, random
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

def load_songs():
    with open("songs.json", "r", encoding="utf-8") as f:
        return json.load(f)

@router.message(F.text == "🎲 Рандом")
async def random_song(message: Message):
    songs = load_songs()
    song = random.choice(songs)

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏮ Назад", callback_data="prev_song"),
            InlineKeyboardButton(text="⬅️ В меню", callback_data="menu"),
            InlineKeyboardButton(text="⏭ Вперёд", callback_data="next_song")
        ]
    ])

    await message.answer_audio(
        audio=song["url"],
        caption=f"{song['name']} — {song['artist']} ({song['genre']})",
        reply_markup=buttons
    ) 
