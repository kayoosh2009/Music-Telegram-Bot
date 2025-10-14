from aiogram import types
from aiogram.fsm.context import FSMContext
from firebase_utils import get_tracks_by_genre, save_user_session, load_user_session, get_track_by_id, add_favorite
from keyboards import player_inline_kb
from keyboards import genres_keyboard

async def listen_music_handler(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("lang", "ru")
    await message.reply("Выберите жанр:" if lang == "ru" else "Choose genre:", reply_markup=genres_keyboard(lang))

async def genre_choice_handler(message: types.Message, state: FSMContext):
    genre = message.text.strip()
    tracks = get_tracks_by_genre(genre)
    if not tracks:
        await message.reply("Треков в этом жанре пока нет.")
        return
    sess = {"genre": genre, "tracks": [t["id"] for t in tracks], "index": 0}
    save_user_session(message.from_user.id, sess)
    first = tracks[0]
    caption = f"NAME: {first.get('name')}\nARTIST: {first.get('artist')}\nGENRE: {first.get('genre')}"
    try:
        await message.reply_audio(first.get("storage_url"), caption=caption, reply_markup=player_inline_kb(0, len(tracks), (await state.get_data()).get("lang", "ru")))
    except Exception:
        await message.reply(caption + "\n" + first.get("storage_url"), reply_markup=player_inline_kb(0, len(tracks), (await state.get_data()).get("lang", "ru")))

async def callback_player(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data or ""
    lang = (await state.get_data()).get("lang", "ru")
    sess = load_user_session(callback.from_user.id)
    if not sess:
        await callback.answer("Session expired. Choose genre again.")
        return
    tracks = sess.get("tracks", [])
    idx = sess.get("index", 0)
    if data.startswith("player_prev"):
        idx = max(0, idx - 1)
    elif data.startswith("player_next"):
        idx = min(len(tracks) - 1, idx + 1)
    elif data.startswith("player_save"):
        track_id = tracks[idx]
        add_favorite(callback.from_user.id, track_id)
        await callback.answer("Saved to favorites!" if lang == "en" else "Сохранено в избранное!")
        return
    elif data == "player_menu":
        try:
            await callback.message.delete()
        except Exception:
            pass
        if lang == "ru":
            await callback.message.answer("Меню:", reply_markup=types.ReplyKeyboardMarkup().add(types.KeyboardButton("🎧 Слушать музыку"), types.KeyboardButton("⬆️ Загрузить свой трек")))
        else:
            await callback.message.answer("Menu:", reply_markup=types.ReplyKeyboardMarkup().add(types.KeyboardButton("🎧 Listen music"), types.KeyboardButton("⬆️ Upload your track")))
        return

    sess["index"] = idx
    save_user_session(callback.from_user.id, sess)
    track = get_track_by_id(tracks[idx])
    caption = f"NAME: {track.get('name')}\nARTIST: {track.get('artist')}\nGENRE: {track.get('genre')}"
    try:
        await callback.message.edit_media(types.InputMediaAudio(media=track.get("storage_url"), caption=caption), reply_markup=player_inline_kb(idx, len(tracks), lang))
    except Exception:
        await callback.message.answer(caption, reply_markup=player_inline_kb(idx, len(tracks), lang))
    await callback.answer()
