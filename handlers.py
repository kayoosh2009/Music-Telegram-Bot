# handlers.py
import os
import telebot
from telebot import types
from bot import bot, LOG_CHANNEL_ID, ARCHIVE_CHANNEL_ID
from utilits import (
    get_random_song, get_genres, get_songs_by_genre, search_songs,
    add_song_metadata, extract_file_id_from_url,
    record_user, update_stats, log_action, get_all_songs, load_json
)

# ---------------- MAIN MENU ----------------
MAIN_MENU_TEXT = "🎵 What would you like to listen to today?"
def main_menu_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🎲 Random", callback_data="menu_random"),
        types.InlineKeyboardButton("🎧 Genres", callback_data="menu_genres"),
    )
    kb.add(
        types.InlineKeyboardButton("📂 Playlists", callback_data="menu_playlists"),
        types.InlineKeyboardButton("🔎 Search", callback_data="menu_search"),
    )
    kb.add(types.InlineKeyboardButton("➕ Suggest a song", callback_data="menu_suggest"))
    return kb

# ---------------- /START COMMAND ----------------
@bot.message_handler(commands=["start", "help"])
def start_handler(message: types.Message):
    print(f"✅ Received /start from {message.from_user.username} ({message.from_user.id})")

    record_user({
        "id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "time": message.date
    })
    update_stats("start")
    log_action(bot, f"/start from @{message.from_user.username} ({message.from_user.id})")

    bot.send_message(
        message.chat.id,
        MAIN_MENU_TEXT,
        reply_markup=main_menu_keyboard()
    )

# ---------------- CALLBACK HANDLERS ----------------
@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("menu_"))
def handle_menu(call: types.CallbackQuery):
    action = call.data
    user = call.from_user.username or call.from_user.id
    print(f"▶️ Callback received: {action} from {user}")

    # ---- RANDOM SONG ----
    if action == "menu_random":
        song = get_random_song()
        if not song:
            bot.answer_callback_query(call.id, "No songs available.")
            return
        file_id = extract_file_id_from_url(song.get("url"))
        caption = f"{song.get('name')} — {song.get('artist')} ({song.get('genre')}, {song.get('lang')})"
        try:
            bot.send_audio(call.message.chat.id, file_id, caption=caption)
            update_stats("send_random")
            log_action(bot, f"Sent random song {song.get('id')} to {user}")
        except Exception as e:
            bot.send_message(call.message.chat.id, "Failed to send audio.")
            log_action(bot, f"Failed to send random: {e}")
        bot.answer_callback_query(call.id)

    # ---- GENRES ----
    elif action == "menu_genres":
        genres = get_genres()
        kb = types.InlineKeyboardMarkup(row_width=2)
        for g in genres:
            kb.add(types.InlineKeyboardButton(g, callback_data=f"genre:{g}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_back"))
        bot.edit_message_text("Choose a genre:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    elif action.startswith("genre:"):
        _, genre = action.split(":", 1)
        songs = get_songs_by_genre(genre)
        if not songs:
            bot.answer_callback_query(call.id, "No songs in this genre.")
            return
        import random
        song = random.choice(songs)
        file_id = extract_file_id_from_url(song.get("url"))
        caption = f"{song.get('name')} — {song.get('artist')} ({song.get('genre')}, {song.get('lang')})"
        try:
            bot.send_audio(call.message.chat.id, file_id, caption=caption)
            log_action(bot, f"Sent genre song {genre} to {user}")
            update_stats("send_genre")
        except Exception as e:
            bot.send_message(call.message.chat.id, "Failed to send genre audio.")
            log_action(bot, f"Error sending genre song: {e}")
        bot.answer_callback_query(call.id)

    # ---- PLAYLISTS ----
    elif action == "menu_playlists":
        playlists = load_json(os.path.join("data", "playlist.json"))
        if not playlists:
            bot.answer_callback_query(call.id, "No playlists available.")
            return
        kb = types.InlineKeyboardMarkup()
        for p in playlists:
            kb.add(types.InlineKeyboardButton(p.get("name", "Unnamed"), callback_data=f"playlist:{p.get('id')}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_back"))
        bot.edit_message_text("Available playlists:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    elif action.startswith("playlist:"):
        _, pid = action.split(":", 1)
        playlists = load_json(os.path.join("data", "playlist.json"))
        playlist = next((p for p in playlists if str(p.get("id")) == pid), None)
        if not playlist:
            bot.answer_callback_query(call.id, "Playlist not found.")
            return
        songs = get_all_songs()
        for sid in playlist.get("song_ids", []):
            song = next((s for s in songs if s.get("id") == sid), None)
            if song:
                fid = extract_file_id_from_url(song.get("url"))
                bot.send_audio(call.message.chat.id, fid, caption=f"{song.get('name')} — {song.get('artist')}")
        update_stats("send_playlist")
        log_action(bot, f"Sent playlist {pid} to {user}")
        bot.answer_callback_query(call.id)

    # ---- SEARCH ----
    elif action == "menu_search":
        bot.send_message(call.message.chat.id, "🔍 Please type what you want to search for:")
        bot.register_next_step_handler(call.message, handle_search_query)
        bot.answer_callback_query(call.id)

    # ---- SUGGEST ----
    elif action == "menu_suggest":
        bot.send_message(call.message.chat.id, "Let's add a new song! What is the name?")
        bot.register_next_step_handler(call.message, suggest_step_name)
        bot.answer_callback_query(call.id)

    elif action == "menu_back":
        bot.edit_message_text(MAIN_MENU_TEXT, call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard())
        bot.answer_callback_query(call.id)

# ---------------- SEARCH ----------------
def handle_search_query(message: types.Message):
    query = (message.text or "").strip()
    if not query:
        bot.send_message(message.chat.id, "Empty query. Try again.")
        return
    results = search_songs(query)
    if not results:
        bot.send_message(message.chat.id, "No results found.")
        return
    for s in results[:5]:
        fid = extract_file_id_from_url(s.get("url"))
        caption = f"{s.get('name')} — {s.get('artist')} ({s.get('genre')}, {s.get('lang')})"
        try:
            bot.send_audio(message.chat.id, fid, caption=caption)
        except:
            bot.send_message(message.chat.id, caption)
    update_stats("search")
    log_action(bot, f"Search from @{message.from_user.username}: {query}")

# ---------------- SUGGESTION ----------------
def suggest_step_name(message: types.Message):
    name = message.text.strip()
    if not name:
        bot.send_message(message.chat.id, "Name cannot be empty. Try again:")
        bot.register_next_step_handler(message, suggest_step_name)
        return
    message.chat_data = {"suggest": {"name": name}}
    bot.send_message(message.chat.id, "Who is the artist?")
    bot.register_next_step_handler(message, suggest_step_artist)

def suggest_step_artist(message: types.Message):
    artist = message.text.strip()
    data = getattr(message, "chat_data", {"suggest": {}})
    data["suggest"]["artist"] = artist
    message.chat_data = data
    bot.send_message(message.chat.id, "What is the genre?")
    bot.register_next_step_handler(message, suggest_step_genre)

def suggest_step_genre(message: types.Message):
    genre = message.text.strip()
    data = getattr(message, "chat_data", {"suggest": {}})
    data["suggest"]["genre"] = genre
    message.chat_data = data
    bot.send_message(message.chat.id, "Language?")
    bot.register_next_step_handler(message, suggest_step_lang)

def suggest_step_lang(message: types.Message):
    lang = message.text.strip()
    data = getattr(message, "chat_data", {"suggest": {}})
    data["suggest"]["lang"] = lang
    message.chat_data = data
    bot.send_message(message.chat.id, "Now send the audio file:")
    bot.register_next_step_handler(message, suggest_step_audio)

def suggest_step_audio(message: types.Message):
    suggest = getattr(message, "chat_data", {}).get("suggest", {})
    try:
        forwarded = bot.forward_message(ARCHIVE_CHANNEL_ID, message.chat.id, message.message_id)
        fid = forwarded.audio.file_id if forwarded.audio else None
        link = f"https://t.me/c/{str(ARCHIVE_CHANNEL_ID).replace('-100', '')}/{forwarded.message_id}"
        meta = {
            **suggest,
            "url": f"file_id:{fid}" if fid else "",
            "archive_url": link
        }
        stored = add_song_metadata(meta)
        bot.send_message(message.chat.id, f"✅ Added your song! ID: {stored.get('id')}")
        update_stats("suggest_song")
        log_action(bot, f"New song suggested by @{message.from_user.username}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Failed to save audio: {e}")

# ---------------- INLINE SEARCH ----------------
@bot.inline_handler(func=lambda q: True)
def inline_handler(query: types.InlineQuery):
    q = query.query.lower()
    songs = get_all_songs()
    results = []
    for s in songs:
        if q and q not in s.get("name", "").lower() and q not in s.get("artist", "").lower():
            continue
        fid = extract_file_id_from_url(s.get("url"))
        if not fid:
            continue
        results.append(types.InlineQueryResultCachedAudio(
            id=str(s.get("id")),
            audio_file_id=fid,
            title=s.get("name"),
            performer=s.get("artist")
        ))
        if len(results) >= 25:
            break
    bot.answer_inline_query(query.id, results, cache_time=1)
