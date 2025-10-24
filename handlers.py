import os
import telebot
from telebot import types
from telebot.types import InlineQueryResultCachedAudio, InlineQueryResultArticle, InputTextMessageContent

from utilits import (
    get_random_song, get_genres, get_songs_by_genre, search_songs,
    add_song_metadata, extract_file_id_from_url, record_user, update_stats, log_action,
    get_all_songs
)

# bot is created in bot.py and imported into this module
from bot import bot, LOG_CHANNEL_ID, ARCHIVE_CHANNEL_ID

# ------------- START / MAIN MENU -------------
MAIN_MENU_TEXT = "What would you like to listen to today? (All in English.)"

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

@bot.message_handler(commands=["start", "help"])
def start_handler(message: types.Message):
    record_user({
        "id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "time": message.date
    })
    update_stats("start")
    log_action(bot, f"/start from @{message.from_user.username} ({message.from_user.id})")
    bot.send_message(message.chat.id, MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())

# ------------- CALLBACKS -------------
@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("menu_"))
def menu_callback(call: types.CallbackQuery):
    data = call.data
    if data == "menu_random":
        song = get_random_song()
        if not song:
            bot.answer_callback_query(call.id, "No songs available.")
            return
        file_id = extract_file_id_from_url(song.get("url"))
        caption = f"{song.get('name')} — {song.get('artist')} ({song.get('genre')}, {song.get('lang')})"
        try:
            bot.send_audio(call.message.chat.id, file_id, caption=caption)
            update_stats("send_random")
            log_action(bot, f"Sent random song id={song.get('id')} to {call.from_user.id}")
        except Exception as e:
            bot.send_message(call.message.chat.id, "Failed to send audio. Maybe file_id invalid.")
            log_action(bot, f"Failed to send random song: {e}")
        bot.answer_callback_query(call.id)
    elif data == "menu_genres":
        genres = get_genres()
        kb = types.InlineKeyboardMarkup(row_width=2)
        for g in genres:
            kb.add(types.InlineKeyboardButton(g, callback_data=f"genre:{g}"))
        kb.add(types.InlineKeyboardButton("Back", callback_data="menu_back"))
        bot.edit_message_text("Choose a genre:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif data.startswith("genre:"):
        _, genre = data.split(":", 1)
        songs = get_songs_by_genre(genre)
        if not songs:
            bot.answer_callback_query(call.id, "No songs for this genre.")
            return
        # Send a random song from this genre
        song = songs[0] if len(songs) == 1 else songs[telebot.util.randint(0, len(songs)-1)]
        file_id = extract_file_id_from_url(song.get("url"))
        caption = f"{song.get('name')} — {song.get('artist')} ({song.get('genre')}, {song.get('lang')})"
        try:
            bot.send_audio(call.message.chat.id, file_id, caption=caption)
            log_action(bot, f"Sent genre song id={song.get('id')} genre={genre} to {call.from_user.id}")
            update_stats("send_genre")
        except Exception as e:
            bot.send_message(call.message.chat.id, "Failed to send audio.")
            log_action(bot, f"Failed to send genre song: {e}")
        bot.answer_callback_query(call.id)
    elif data == "menu_playlists":
        # We display playlists from playlist.json (if any)
        from utilits import load_json
        playlists = load_json(os.path.join(os.path.dirname(__file__), "data", "playlist.json"))
        if not playlists:
            bot.answer_callback_query(call.id, "No playlists yet.")
            return
        kb = types.InlineKeyboardMarkup()
        for p in playlists:
            kb.add(types.InlineKeyboardButton(p.get("name", "Unnamed"), callback_data=f"playlist:{p.get('id')}"))
        kb.add(types.InlineKeyboardButton("Back", callback_data="menu_back"))
        bot.edit_message_text("Available playlists:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif data.startswith("playlist:"):
        _, pid = data.split(":", 1)
        from utilits import load_json
        playlists = load_json(os.path.join(os.path.dirname(__file__), "data", "playlist.json"))
        pl = next((x for x in playlists if str(x.get("id")) == pid), None)
        if not pl:
            bot.answer_callback_query(call.id, "Playlist not found.")
            return
        song_ids = pl.get("song_ids", [])
        songs = get_all_songs()
        sent_any = False
        for sid in song_ids:
            song = next((s for s in songs if s.get("id") == sid), None)
            if song:
                file_id = extract_file_id_from_url(song.get("url"))
                bot.send_audio(call.message.chat.id, file_id, caption=f"{song.get('name')} — {song.get('artist')}")
                sent_any = True
        if not sent_any:
            bot.send_message(call.message.chat.id, "No songs found in this playlist.")
        else:
            update_stats("send_playlist")
            log_action(bot, f"Sent playlist id={pid} to {call.from_user.id}")
        bot.answer_callback_query(call.id)
    elif data == "menu_search":
        bot.send_message(call.message.chat.id, "Please send your search query (song, artist, genre, or language):")
        bot.register_next_step_handler(call.message, handle_search_query)
        bot.answer_callback_query(call.id)
    elif data == "menu_suggest":
        bot.send_message(call.message.chat.id, "Let's add a suggestion. What is the song name?")
        bot.register_next_step_handler(call.message, suggest_step_name)
        bot.answer_callback_query(call.id)
    elif data == "menu_back":
        bot.edit_message_text(MAIN_MENU_TEXT, call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard())
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, "Unknown action.")

# ------------- SEARCH FLOW -------------
def handle_search_query(message: types.Message):
    query = message.text or ""
    if not query:
        bot.send_message(message.chat.id, "Empty query. Please try again.")
        return
    results = search_songs(query)
    if not results:
        bot.send_message(message.chat.id, "No results found.")
        return
    for s in results[:10]:
        fid = extract_file_id_from_url(s.get("url"))
        caption = f"{s.get('name')} — {s.get('artist')} ({s.get('genre')}, {s.get('lang')})"
        try:
            bot.send_audio(message.chat.id, fid, caption=caption)
        except Exception:
            bot.send_message(message.chat.id, f"{s.get('name')} — {s.get('artist')} (audio missing)")
    update_stats("search")
    log_action(bot, f"Search by @{message.from_user.username}: {query}")

# ------------- SUGGEST SONG FLOW -------------
# We'll collect name -> artist -> genre -> lang -> audio file
def suggest_step_name(message: types.Message):
    name = message.text or ""
    if not name:
        bot.send_message(message.chat.id, "Song name cannot be empty. Please send the song name:")
        bot.register_next_step_handler(message, suggest_step_name)
        return
    message.chat_data = {"suggest": {"name": name}}
    bot.send_message(message.chat.id, "Who is the artist?")
    bot.register_next_step_handler(message, suggest_step_artist)

def suggest_step_artist(message: types.Message):
    artist = message.text or ""
    if not artist:
        bot.send_message(message.chat.id, "Artist cannot be empty. Please send the artist name:")
        bot.register_next_step_handler(message, suggest_step_artist)
        return
    # retrieve stored
    chat_data = getattr(message, "chat_data", {})
    suggest = chat_data.get("suggest", {})
    suggest["artist"] = artist
    message.chat_data = {"suggest": suggest}
    bot.send_message(message.chat.id, "Genre?")
    bot.register_next_step_handler(message, suggest_step_genre)

def suggest_step_genre(message: types.Message):
    genre = message.text or ""
    if not genre:
        bot.send_message(message.chat.id, "Genre cannot be empty. Please send genre:")
        bot.register_next_step_handler(message, suggest_step_genre)
        return
    chat_data = getattr(message, "chat_data", {})
    suggest = chat_data.get("suggest", {})
    suggest["genre"] = genre
    message.chat_data = {"suggest": suggest}
    bot.send_message(message.chat.id, "Language (e.g., English, Japanese):")
    bot.register_next_step_handler(message, suggest_step_lang)

def suggest_step_lang(message: types.Message):
    lang = message.text or ""
    if not lang:
        bot.send_message(message.chat.id, "Language cannot be empty. Please send language:")
        bot.register_next_step_handler(message, suggest_step_lang)
        return
    chat_data = getattr(message, "chat_data", {})
    suggest = chat_data.get("suggest", {})
    suggest["lang"] = lang
    message.chat_data = {"suggest": suggest}
    bot.send_message(message.chat.id, "Now please send the audio file (mp3, m4a, ogg...) or forward the message containing the audio.")
    bot.register_next_step_handler(message, suggest_step_receive_audio)

def suggest_step_receive_audio(message: types.Message):
    # Accept either a direct audio file or a forwarded audio. We attempt to forward to archive channel.
    suggest = getattr(message, "chat_data", {}).get("suggest", {})
    if not suggest:
        bot.send_message(message.chat.id, "Internal error: suggestion data lost. Please try again.")
        return

    # We expect audio in message.audio or message.document (some clients send music as document)
    forward_source_chat = message.chat.id
    forwarded_message = None
    try:
        # If the user forwarded a message that already contains audio, we forward that message to archive channel.
        if message.forward_from or message.forward_from_chat:
            # user forwarded a message; forward the whole message to archive channel
            forwarded_message = bot.forward_message(ARCHIVE_CHANNEL_ID, message.chat.id, message.message_id)
        elif message.audio:
            # forward the current message to archive (preserves file in channel)
            forwarded_message = bot.forward_message(ARCHIVE_CHANNEL_ID, message.chat.id, message.message_id)
        elif message.document:
            forwarded_message = bot.forward_message(ARCHIVE_CHANNEL_ID, message.chat.id, message.message_id)
        else:
            bot.send_message(message.chat.id, "No audio detected. Please send an audio file (mp3/m4a) or forward a message with audio.")
            bot.register_next_step_handler(message, suggest_step_receive_audio)
            return
    except Exception as e:
        bot.send_message(message.chat.id, "Failed to forward the audio to archive channel. Make sure the bot is admin in the archive channel.")
        log_action(bot, f"Failed to forward suggestion audio: {e}")
        return

    # If forward succeeded, forwarded_message contains info about the message inside the archive channel
    file_id = None
    archive_url = None
    try:
        # Telebot returns message object; check for audio/document fields
        if forwarded_message.audio:
            file_id = forwarded_message.audio.file_id
        elif forwarded_message.document:
            file_id = forwarded_message.document.file_id
        # archive url: t.me/c/{channel_id_without_minus}/{message_id}
        # When using channels, the internal id for t.me/c/... uses the archive channel id without -100 prefix.
        # Example: -1003197881242 -> 3197881242
        cid = str(ARCHIVE_CHANNEL_ID)
        archive_link = None
        if cid.startswith("-100"):
            numeric = cid.replace("-100", "")
            archive_link = f"https://t.me/c/{numeric}/{forwarded_message.message_id}"
        else:
            # Fallback: use message link if possible
            archive_link = f"Archive message id={forwarded_message.message_id}"
        archive_url = archive_link
    except Exception as e:
        log_action(bot, f"Error extracting file_id from forwarded message: {e}")

    # Prepare metadata and store to songs.json
    metadata = {
        "name": suggest.get("name"),
        "artist": suggest.get("artist"),
        "genre": suggest.get("genre"),
        "lang": suggest.get("lang"),
        "url": f"file_id:{file_id}" if file_id else "",
        "archive_url": archive_url or ""
    }
    stored = add_song_metadata(metadata)
    bot.send_message(message.chat.id, f"Thanks! Your suggestion has been added with id {stored.get('id')}.")
    update_stats("suggest_song")
    log_action(bot, f"User @{message.from_user.username} suggested song id={stored.get('id')} name={stored.get('name')}")

# ------------- INLINE QUERY HANDLER -------------
@bot.inline_handler(func=lambda query: True)
def inline_query(inline_query: types.InlineQuery):
    """
    Return cached audio results based on songs.json.
    The songs.json should contain 'url' as 'file_id:...' or plain file_id.
    """
    q = inline_query.query.strip().lower()
    songs = get_all_songs()
    results = []
    for s in songs:
        # if query is empty — return some top songs (limit results)
        if q:
            if not (q in s.get("name", "").lower() or q in s.get("artist", "").lower() or q in s.get("genre", "").lower()):
                continue
        fid = extract_file_id_from_url(s.get("url"))
        if not fid:
            continue
        result_id = f"song-{s.get('id')}"
        try:
            r = InlineQueryResultCachedAudio(
                id=result_id,
                audio_file_id=fid,
                title=s.get("name", "Unknown"),
                performer=s.get("artist", "")
            )
            results.append(r)
        except Exception:
            # fallback to article with metadata text if cached audio creation fails
            r = InlineQueryResultArticle(
                id=result_id + "-txt",
                title=s.get("name", "Unknown"),
                input_message_content=InputTextMessageContent(
                    f"{s.get('name')} — {s.get('artist')}\nGenre: {s.get('genre')}\nLanguage: {s.get('lang')}\nLink: {s.get('archive_url')}"
                )
            )
            results.append(r)
        if len(results) >= 30:
            break
    try:
        bot.answer_inline_query(inline_query.id, results)
    except Exception as e:
        print("Inline answer failed:", e)
