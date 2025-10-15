from aiogram import types
from song_utils import get_songs_by_genre
import random

async def genre_selected_handler(message: types.Message):
    genre = message.text
    songs = get_songs_by_genre(genre)
    
    if not songs:
        await message.answer("❌ Нет треков в этом жанре.")
        return
    
    song = random.choice(songs)
    caption = f"🎵 <b>{song['name']}</b>\n👤 {song['artist']}\n🎧 {song['genre']}"
    
    await message.answer_audio(song["file_id"], caption=caption, parse_mode="HTML")
