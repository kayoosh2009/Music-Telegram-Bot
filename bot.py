import os
import json
import random
import threading
import time
import telebot
from telebot import types
from dotenv import load_dotenv

# ============ ENV SETUP ============
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

DATA_DIR = "data"
SONGS_FILE = os.path.join(DATA_DIR, "songs.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

os.makedirs(DATA_DIR, exist_ok=True)
for path in [SONGS_FILE, USERS_FILE]:
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("[]")

ADMIN_USERNAME = "kayoosh_x"

# ============ UTILITIES ============
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_action(text):
    print("LOG:", text)
    try:
        bot.send_message(LOG_CHANNEL_ID, f"🪵 <b>Log:</b> {text}")
    except:
        pass

def record_user(user):
    users = load_json(USERS_FILE)
    if not any(u["id"] == user["id"] for u in users):
        users.append(user)
        save_json(USERS_FILE, users)
        log_action(f"👤 New user @{user['username']} ({user['id']})")

def get_random_song():
    songs = load_json(SONGS_FILE)
    return random.choice(songs) if songs else None

def get_genres():
    songs = load_json(SONGS_FILE)
    return sorted(list(set(s["genre"] for s in songs if s.get("genre"))))

def get_songs_by_genre(genre):
    return [s for s in load_json(SONGS_FILE) if s.get("genre", "").lower() == genre.lower()]

def extract_file_id(url):
    return url.replace("file_id:", "") if url.startswith("file_id:") else None

def search_songs(q):
    q = q.lower()
    songs = load_json(SONGS_FILE)
    return [s for s in songs if q in s["name"].lower() or q in s["artist"].lower() or q in s["genre"].lower() or q in s["lang"].lower()]

# ============ TIMER FUNCTION ============
def log_timer():
    while True:
        for remaining in range(24 * 60, 0, -1):
            try:
                bot.send_message(LOG_CHANNEL_ID, f"⏱ Timer: {remaining} minutes left until next cycle.")
            except:
                pass
            time.sleep(60)  # every minute
        try:
            bot.send_message(LOG_CHANNEL_ID, "♻️ 24 hours cycle completed. Restarting timer...")
        except:
            pass

# Запускаем таймер в отдельном потоке
timer_thread = threading.Thread(target=log_timer, daemon=True)
timer_thread.start()

# ============ REPLY KEYBOARD ============
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎲 Random", "🎧 Genres")
    kb.row("🔎 Search", "➕ Suggest Song")
    kb.row("📂 Playlists")
    return kb

# ============ COMMANDS ============
@bot.message_handler(commands=["start", "menu"])
def start_menu(message):
    record_user({
        "id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name or "",
    })
    bot.send_message(message.chat.id, "🎧 Welcome! What do you want to do?", reply_markup=main_keyboard())

# /tell — only for @kayoosh_x
@bot.message_handler(commands=["tell"])
def tell_all(message):
    if message.from_user.username != ADMIN_USERNAME:
        bot.reply_to(message, "⛔ You are not authorized to use this command.")
        return
    text = message.text.replace("/tell", "").strip()
    if not text:
        bot.reply_to(message, "Please add a message after /tell.")
        return

    users = load_json(USERS_FILE)
    count = 0
    for u in users:
        try:
            bot.send_message(u["id"], f"📢 {text}")
            count += 1
        except:
            pass
    bot.reply_to(message, f"✅ Message sent to {count} users.")
    log_action(f"Broadcast by @{ADMIN_USERNAME}: {text}")

# ============ MESSAGE HANDLER ============
@bot.message_handler(content_types=["text"])
def handle_message(message):
    text = message.text.strip().lower()

    # Random song
    if text == "🎲 random":
        song = get_random_song()
        if not song:
            bot.send_message(message.chat.id, "No songs found.")
            return
        file_id = extract_file_id(song["url"])
        bot.send_audio(message.chat.id, file_id, caption=f"{song['name']} — {song['artist']} ({song['genre']}, {song['lang']})")
        log_action(f"Sent random song to {message.from_user.id}")

    # Genres
    elif text == "🎧 genres":
        genres = get_genres()
        if not genres:
            bot.send_message(message.chat.id, "No genres available.")
            return
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for g in genres:
            kb.row(g)
        kb.row("⬅️ Back to Menu")
        bot.send_message(message.chat.id, "Choose a genre:", reply_markup=kb)

    # Back button
    elif text == "⬅️ back to menu":
        bot.send_message(message.chat.id, "🎧 Back to menu:", reply_markup=main_keyboard())

    # Search
    elif text == "🔎 search":
        msg = bot.send_message(message.chat.id, "Type your search query:")
        bot.register_next_step_handler(msg, handle_search)

    # Suggest song
    elif text == "➕ suggest song":
        msg = bot.send_message(message.chat.id, "Please send me the <b>audio file</b> first 🎵")
        bot.register_next_step_handler(msg, suggest_audio_first)

    # Playlist (placeholder)
    elif text == "📂 playlists":
        bot.send_message(message.chat.id, "📂 Playlist feature coming soon!")

    # Genre selection
    else:
        genres = get_genres()
        if text in genres:
            songs = get_songs_by_genre(text)
            if not songs:
                bot.send_message(message.chat.id, "No songs found for this genre.")
                return
            song = random.choice(songs)
            file_id = extract_file_id(song["url"])
            bot.send_audio(message.chat.id, file_id, caption=f"{song['name']} — {song['artist']}")
            log_action(f"Sent genre {text} song to {message.from_user.id}")

# ============ SEARCH HANDLER ============
def handle_search(message):
    query = message.text.strip()
    results = search_songs(query)
    if not results:
        bot.send_message(message.chat.id, "No results found.", reply_markup=main_keyboard())
        return
    for s in results[:5]:
        bot.send_audio(message.chat.id, extract_file_id(s["url"]), caption=f"{s['name']} — {s['artist']}")
    log_action(f"Search '{query}' by {message.from_user.id}")
    bot.send_message(message.chat.id, "Done ✅", reply_markup=main_keyboard())

# ============ SUGGEST SONG ============
user_suggest_data = {}

def suggest_audio_first(message):
    if not message.audio:
        msg = bot.send_message(message.chat.id, "Please send an audio file 🎧")
        bot.register_next_step_handler(msg, suggest_audio_first)
        return

    try:
        forwarded = bot.forward_message(ARCHIVE_CHANNEL_ID, message.chat.id, message.message_id)
        file_id = forwarded.audio.file_id
        archive_link = f"https://t.me/c/{str(ARCHIVE_CHANNEL_ID).replace('-100', '')}/{forwarded.message_id}"

        user_suggest_data[message.from_user.id] = {
            "url": f"file_id:{file_id}",
            "archive_url": archive_link
        }
        msg = bot.send_message(message.chat.id, "Nice! Now send me the <b>song name</b>:")
        bot.register_next_step_handler(msg, suggest_name)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {e}")

def suggest_name(message):
    user_suggest_data[message.from_user.id]["name"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Artist name?")
    bot.register_next_step_handler(msg, suggest_artist)

def suggest_artist(message):
    user_suggest_data[message.from_user.id]["artist"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Genre?")
    bot.register_next_step_handler(msg, suggest_genre)

def suggest_genre(message):
    user_suggest_data[message.from_user.id]["genre"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Language?")
    bot.register_next_step_handler(msg, suggest_lang)

def suggest_lang(message):
    user_suggest_data[message.from_user.id]["lang"] = message.text.strip()
    save_suggested_song(message)

def save_suggested_song(message):
    try:
        data = user_suggest_data[message.from_user.id]
        new_song = {
            "id": random.randint(1000, 9999),
            "name": data["name"],
            "artist": data["artist"],
            "genre": data["genre"],
            "lang": data["lang"],
            "url": data["url"],
            "archive_url": data["archive_url"]
        }

        songs = load_json(SONGS_FILE)
        songs.append(new_song)
        save_json(SONGS_FILE, songs)

        bot.send_message(message.chat.id, f"✅ Added song: {data['name']} by {data['artist']}", reply_markup=main_keyboard())
        log_action(f"New song added by {message.from_user.id}: {data['name']}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Failed to save song: {e}", reply_markup=main_keyboard())

# ============ INLINE MODE ============
@bot.inline_handler(func=lambda q: True)
def inline_search(query):
    q = query.query.lower()
    songs = load_json(SONGS_FILE)
    results = []
    for s in songs:
        if q and q not in s["name"].lower() and q not in s["artist"].lower():
            continue
        file_id = extract_file_id(s["url"])
        if not file_id:
            continue
        results.append(types.InlineQueryResultCachedAudio(
            id=str(s["id"]),
            audio_file_id=file_id,
            title=s["name"],
            performer=s["artist"]
        ))
        if len(results) >= 25:
            break
    bot.answer_inline_query(query.id, results, cache_time=1)

# ============ START BOT ============
print("🤖 Bot is running with timer...")
bot.infinity_polling(skip_pending=True)
