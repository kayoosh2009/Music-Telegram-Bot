#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Полный обновлённый bot.py
Включает: поиск, плейлисты, player controls (reply buttons), /tell, stats.json и совместимость с songs.json и user.json
Автор: ChatGPT (на основе кода пользователя)
"""

import os
import json
import random
import threading
import time
from datetime import datetime
from dotenv import load_dotenv
import telebot
from telebot import types

# ---------------------------
# Конфигурация (из .env)
# ---------------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("ERROR: BOT_TOKEN not set in .env")

LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0") or 0)
ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID", "0") or 0)
ADMIN_ID = 7898886950  # твой ID для /tell, как просил

# ---------------------------
# Пути файлов (абсолютные)
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SONGS_FILE = os.path.join(BASE_DIR, "songs.json")      # внешний формат: список треков
USERS_FILE = os.path.join(BASE_DIR, "user.json")
PLAYLISTS_FILE = os.path.join(BASE_DIR, "playlists.json")
STATS_FILE = os.path.join(BASE_DIR, "stats.json")

# ---------------------------
# Инициализация файлов, если нет
# ---------------------------
def ensure_file(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

ensure_file(SONGS_FILE, [])  # предполагаем, что songs.json — список объектов
ensure_file(USERS_FILE, [])
ensure_file(PLAYLISTS_FILE, [])
ensure_file(STATS_FILE, {
    "registered_users": 0,
    "songs_played": 0,
    "messages_handled": 0,
    "playlists_created": 0,
    "playlists_played": 0,
    "songs_added": 0
})

# ---------------------------
# Инициализация бота
# ---------------------------
bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}            # in-memory state: user chat_id -> dict
last_bot_messages = {}     # chat_id -> list of bot message ids we may delete (controls, audio message ids)

# ---------------------------
# Локализация (RU/EN)
# ---------------------------
LOCALES = {
    "ru": {
        "choose_lang": "👋 Привет! Выберите язык:",
        "welcome": "🎵 Добро пожаловать в главное меню!",
        "main_menu": "🏠 Главное меню:",
        "random": "🎲 Рандом",
        "genres": "🎧 Жанры",
        "suggest": "🎤 Предложить песню",
        "search": "🔎 Поиск",
        "playlists": "📁 Плейлисты",
        "no_songs": "😢 В архиве пока нет песен.",
        "genre_select": "🎼 Выберите жанр:",
        "more_or_menu": "🔁 Напишите «ещё» чтобы получить другую песню из жанра, или «меню» для возврата.",
        "thank_song": "✅ Спасибо! Ваша песня отправлена в архив и добавлена в базу 🎶",
        "back_to_menu": "🔙 Назад в меню",
        "more": "ещё",
        "menu": "меню",
        "player_controls_info": "Кнопки: ⏮ Назад — ➕ Добавить в плейлист — ⏭ Вперёд — меню",
        "create_playlist": "➕ Создать плейлист",
        "my_playlists": "👤 Мои плейлисты",
        "public_playlists": "🌐 Публичные плейлисты",
        "no_playlists": "У вас ещё нет плейлистов.",
        "choose_playlist": "Выберите плейлист:",
        "playlist_created": "✅ Плейлист создан",
        "add_to_playlist": "➕ Добавить в плейлист",
        "playlist_empty": "Плейлист пуст.",
        "playlist_playing": "▶️ Воспроизвожу плейлист: ",
        "tell_no_perm": "❌ У вас нет права использовать /tell",
        "ask_search": "🔎 Введите название песни, артиста или плейлиста:",
        "no_results": "Ничего не найдено.",
        "choose_number": "Выберите номер для воспроизведения/открытия (или напишите 'меню').",
        "invalid_choice": "Неверный выбор.",
        "playlist_added_song": "✅ Песня добавлена в плейлист.",
        "song_already_in_playlist": "Песня уже в плейлисте.",
        "no_last_song": "Нет последней песни для добавления.",
        "prompt_playlist_public": "Сделать плейлист публичным? (да/нет)",
        "prompt_playlist_name": "Введите имя плейлиста:",
        "prompt_choose_playlist_for_add": "Выберите плейлист для добавления:"
    },
    "en": {
        "choose_lang": "👋 Hello! Choose your language:",
        "welcome": "🎵 Welcome to the main menu!",
        "main_menu": "🏠 Main menu:",
        "random": "🎲 Random",
        "genres": "🎧 Genres",
        "suggest": "🎤 Suggest a song",
        "search": "🔎 Search",
        "playlists": "📁 Playlists",
        "no_songs": "😢 No songs in the archive yet.",
        "genre_select": "🎼 Choose a genre:",
        "more_or_menu": "🔁 Type 'more' to get another song from this genre or 'menu' to return.",
        "thank_song": "✅ Thanks! Your song has been added to the archive 🎶",
        "back_to_menu": "🔙 Back to menu",
        "more": "more",
        "menu": "menu",
        "player_controls_info": "Controls: ⏮ Prev — ➕ Add to playlist — ⏭ Next — menu",
        "create_playlist": "➕ Create playlist",
        "my_playlists": "👤 My playlists",
        "public_playlists": "🌐 Public playlists",
        "no_playlists": "You don't have playlists yet.",
        "choose_playlist": "Choose a playlist:",
        "playlist_created": "✅ Playlist created",
        "add_to_playlist": "➕ Add to playlist",
        "playlist_empty": "Playlist is empty.",
        "playlist_playing": "▶️ Playing playlist: ",
        "tell_no_perm": "❌ You don't have permission to use /tell",
        "ask_search": "🔎 Type title/artist/playlist:",
        "no_results": "No results.",
        "choose_number": "Choose number to play/open (or type 'menu').",
        "invalid_choice": "Invalid choice.",
        "playlist_added_song": "✅ Song added to playlist.",
        "song_already_in_playlist": "Song already in playlist.",
        "no_last_song": "No last song to add.",
        "prompt_playlist_public": "Make playlist public? (yes/no)",
        "prompt_playlist_name": "Enter playlist name:",
        "prompt_choose_playlist_for_add": "Choose playlist to add:"
    }
}

# ---------------------------
# Helpers: safe load/save JSON
# ---------------------------
def safe_load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def safe_save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------
# Data helpers: songs/users/playlists/stats
# ---------------------------
def load_songs():
    # supports songs.json as list OR songs key inside dict
    data = safe_load(SONGS_FILE, [])
    if isinstance(data, dict) and "songs" in data:
        songs = data.get("songs", [])
    elif isinstance(data, list):
        songs = data
    else:
        songs = []
    # filter invalid entries
    songs = [s for s in songs if isinstance(s, dict) and s.get("id") is not None and s.get("url")]
    return songs

def save_songs(songs):
    safe_save(SONGS_FILE, songs)

def load_users():
    return safe_load(USERS_FILE, [])

def save_users(users):
    safe_save(USERS_FILE, users)

def load_playlists():
    return safe_load(PLAYLISTS_FILE, [])

def save_playlists(pls):
    safe_save(PLAYLISTS_FILE, pls)

def load_stats():
    return safe_load(STATS_FILE, {
        "registered_users": 0,
        "songs_played": 0,
        "messages_handled": 0,
        "playlists_created": 0,
        "playlists_played": 0,
        "songs_added": 0
    })

def save_stats(s):
    safe_save(STATS_FILE, s)

def increment_stat(key, amount=1):
    s = load_stats()
    s[key] = s.get(key, 0) + amount
    save_stats(s)

# ---------------------------
# Logging + heartbeat
# ---------------------------
def log_action(text):
    print(text)
    try:
        if LOG_CHANNEL_ID:
            bot.send_message(LOG_CHANNEL_ID, text)
    except Exception:
        pass

def heartbeat():
    while True:
        log_action("✅ Бот работает")
        time.sleep(60)

threading.Thread(target=heartbeat, daemon=True).start()

# ---------------------------
# Keyboard factories
# ---------------------------
def main_menu_kb(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(LOCALES[lang]["random"], LOCALES[lang]["genres"])
    kb.row(LOCALES[lang]["search"], LOCALES[lang]["playlists"])
    kb.row(LOCALES[lang]["suggest"])
    return kb

def player_controls_kb(lang):
    # reply keyboard to appear under messages (not inline)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("⏮ Назад", "➕ Добавить в плейлист", "⏭ Вперёд")
    kb.row(LOCALES[lang]["menu"])
    return kb

def playlists_menu_kb(lang, include_create=True):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if include_create:
        kb.add(LOCALES[lang]["create_playlist"])
    kb.add(LOCALES[lang]["my_playlists"], LOCALES[lang]["public_playlists"])
    kb.add(LOCALES[lang]["back_to_menu"])
    return kb

# ---------------------------
# Message safe-delete helpers
# ---------------------------
def safe_delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

def clear_last_bot_messages(chat_id):
    ids = last_bot_messages.get(chat_id, [])
    for mid in ids:
        safe_delete_message(chat_id, mid)
    last_bot_messages[chat_id] = []

# ---------------------------
# Send song + controls: keeps last song in user_state and tracks message ids
# ---------------------------
def send_song_with_controls(chat_id, song, lang):
    # remove previous bot messages (controls) before sending new pair
    clear_last_bot_messages(chat_id)

    caption = f"🎧 <b>{song.get('name')}</b>\n👤 {song.get('artist')}\n🎵 {song.get('genre')} | 🌐 {song.get('lang')}"
    try:
        # send audio
        sent_audio = bot.send_audio(chat_id, song["url"].replace("file_id:", ""), caption=caption, parse_mode="HTML")
    except Exception:
        # try file_id fallback
        try:
            fid = song["url"].split("file_id:", 1)[1]
            sent_audio = bot.send_audio(chat_id, fid, caption=caption, parse_mode="HTML")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ Не удалось отправить аудио: {e}")
            return

    # store last song in memory for this user
    user_state.setdefault(chat_id, {})
    user_state[chat_id].update({
        "last_song": song,
        "mode": user_state.get(chat_id, {}).get("mode", None)
    })

    # update stats
    increment_stat("songs_played", 1)

    # send control message
    ctrl = bot.send_message(chat_id, LOCALES[lang]["player_controls_info"], reply_markup=player_controls_kb(lang))

    # save message ids for deletion later: audio msg id and control msg id
    last_bot_messages.setdefault(chat_id, [])
    try:
        last_bot_messages[chat_id].append(sent_audio.message_id)
    except Exception:
        pass
    try:
        last_bot_messages[chat_id].append(ctrl.message_id)
    except Exception:
        pass

# ---------------------------
# Utility: find song by id
# ---------------------------
def find_song(song_id):
    songs = load_songs()
    for s in songs:
        try:
            if int(s.get("id")) == int(song_id):
                return s
        except Exception:
            continue
    return None

# ---------------------------
# Add user helper
# ---------------------------
def add_user_record(user):
    users = load_users()
    if not any(u.get("id") == user.id for u in users):
        users.append({
            "id": user.id,
            "username": user.username or "аноним",
            "first_seen": datetime.utcnow().isoformat()
        })
        save_users(users)
        # stat
        increment_stat("registered_users", 1)
        log_action(f"🆕 Новый пользователь: @{user.username or 'аноним'} (ID: {user.id})")

# ---------------------------
# /start
# ---------------------------
@bot.message_handler(commands=["start"])
def cmd_start(message):
    add_user_record(message.from_user)
    chat_id = message.chat.id
    user_state[chat_id] = {"step": "choose_lang", "lang": "ru"}  # default ru
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("🇷🇺 Русский", "🇬🇧 English")
    bot.send_message(chat_id, LOCALES["ru"]["choose_lang"], reply_markup=kb)
    increment_stat("messages_handled", 1)
    log_action(f"/start from @{message.from_user.username or message.from_user.id}")

# ---------------------------
# Language selection
# ---------------------------
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "choose_lang")
def handle_choose_lang(message):
    chat_id = message.chat.id
    txt = (message.text or "")
    lang = "ru" if "🇷🇺" in txt else ("en" if "🇬🇧" in txt else "ru")
    user_state[chat_id] = {"step": "menu", "lang": lang, "mode": None}
    bot.send_message(chat_id, LOCALES[lang]["welcome"], reply_markup=main_menu_kb(lang))
    increment_stat("messages_handled", 1)
    log_action(f"Language set to {lang} for @{message.from_user.username or message.from_user.id}")

# ---------------------------
# RANDOM handler
# ---------------------------
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "menu" and
                     m.text in [LOCALES["ru"]["random"], LOCALES["en"]["random"]])
def handle_random(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    songs = load_songs()
    if not songs:
        bot.send_message(chat, LOCALES[lang]["no_songs"])
        return
    song = random.choice(songs)
    # set mode to random so prev/next use full song list
    user_state[chat]["mode"] = "random"
    user_state[chat]["last_song"] = song
    send_song_with_controls(chat, song, lang)
    increment_stat("messages_handled", 1)
    log_action(f"🎲 random by @{m.from_user.username or m.from_user.id}: {song.get('name')}")

# ---------------------------
# GENRES handlers
# ---------------------------
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "menu" and
                     m.text in [LOCALES["ru"]["genres"], LOCALES["en"]["genres"]])
def handle_genres(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    songs = load_songs()
    genres = sorted({s.get("genre", "Unknown") for s in songs})
    if not genres:
        bot.send_message(chat, LOCALES[lang]["no_songs"])
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for g in genres:
        kb.add(g)
    kb.add(LOCALES[lang]["back_to_menu"])
    user_state[chat]["step"] = "choose_genre"
    bot.send_message(chat, LOCALES[lang]["genre_select"], reply_markup=kb)
    increment_stat("messages_handled", 1)

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "choose_genre")
def handle_choose_genre(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    if m.text == LOCALES[lang]["back_to_menu"]:
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        return
    genre = m.text
    songs = [s for s in load_songs() if s.get("genre", "").lower() == genre.lower()]
    if not songs:
        bot.send_message(chat, LOCALES[lang]["no_songs"])
        return
    song = random.choice(songs)
    user_state[chat]["mode"] = "genre"
    user_state[chat]["genre"] = genre
    user_state[chat]["last_song"] = song
    send_song_with_controls(chat, song, lang)
    user_state[chat]["step"] = "genre_loop"
    bot.send_message(chat, LOCALES[lang]["more_or_menu"])
    increment_stat("messages_handled", 1)
    log_action(f"Genre {genre} chosen by @{m.from_user.username or m.from_user.id}: {song.get('name')}")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "genre_loop")
def handle_genre_loop(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    txt = (m.text or "").lower()
    if txt == LOCALES[lang]["menu"]:
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        increment_stat("messages_handled", 1)
        return
    if txt == LOCALES[lang]["more"]:
        genre = user_state[chat]["genre"]
        songs = [s for s in load_songs() if s.get("genre", "").lower() == genre.lower()]
        if songs:
            song = random.choice(songs)
            user_state[chat]["last_song"] = song
            send_song_with_controls(chat, song, lang)
            log_action(f"More in genre {genre} for @{m.from_user.username or m.from_user.id}: {song.get('name')}")
        return
    bot.send_message(chat, LOCALES[lang]["more_or_menu"])

# ---------------------------
# SEARCH flow (songs/artists/playlists)
# ---------------------------
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "menu" and
                     m.text in [LOCALES["ru"]["search"], LOCALES["en"]["search"]])
def handle_search_start(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    user_state[chat]["step"] = "search"
    bot.send_message(chat, LOCALES[lang]["ask_search"])
    increment_stat("messages_handled", 1)

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "search")
def handle_search_query(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    q = (m.text or "").strip().lower()
    if not q:
        bot.send_message(chat, ("Напишите запрос." if lang=="ru" else "Please type a query."))
        return
    songs = load_songs()
    playlists = load_playlists()
    found_songs = [s for s in songs if q in (s.get("name","").lower()) or q in (s.get("artist","").lower())]
    found_playlists = [p for p in playlists if q in p.get("name","").lower() and (p.get("public") or p.get("owner_id") == m.from_user.id)]
    lines = []
    mapping = {}
    idx = 1
    if found_songs:
        lines.append("🎵 Songs:")
        for s in found_songs:
            lines.append(f"{idx}. {s.get('name')} — {s.get('artist')} (id:{s.get('id')})")
            mapping[str(idx)] = ("song", s.get("id"))
            idx += 1
    if found_playlists:
        lines.append("\n📁 Playlists:")
        for p in found_playlists:
            lines.append(f"{idx}. {p.get('name')} (id:{p.get('id')})")
            mapping[str(idx)] = ("playlist", p.get("id"))
            idx += 1
    if not lines:
        bot.send_message(chat, LOCALES[lang]["no_results"])
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        return
    bot.send_message(chat, "\n".join(lines) + "\n\n" + (LOCALES[lang]["choose_number"]))
    user_state[chat]["step"] = "search_choose"
    user_state[chat]["search_map"] = mapping

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "search_choose")
def handle_search_choose(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    txt = (m.text or "").strip()
    if txt.lower() == LOCALES[lang]["menu"]:
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        return
    mapping = user_state[chat].get("search_map", {})
    choice = mapping.get(txt)
    if not choice:
        bot.send_message(chat, LOCALES[lang]["invalid_choice"])
        return
    typ, oid = choice
    if typ == "song":
        song = find_song(oid)
        if song:
            user_state[chat]["last_song"] = song
            user_state[chat]["mode"] = "search"
            send_song_with_controls(chat, song, lang)
            user_state[chat]["step"] = "menu"
            bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
            log_action(f"Search play song {song.get('name')} for @{m.from_user.username or m.from_user.id}")
    elif typ == "playlist":
        playlists = load_playlists()
        pl = next((p for p in playlists if int(p.get("id")) == int(oid)), None)
        if not pl:
            bot.send_message(chat, LOCALES[lang]["invalid_choice"])
            return
        play_playlist(chat, pl, lang)
        user_state[chat]["step"] = "menu"
        log_action(f"Search play playlist {pl.get('name')} for @{m.from_user.username or m.from_user.id}")

# ---------------------------
# Playlists: create / list / play / add
# ---------------------------
def next_playlist_id():
    pls = load_playlists()
    if not pls:
        return 1
    try:
        return max(int(p.get("id", 0)) for p in pls) + 1
    except Exception:
        return int(time.time())

def play_playlist(chat_id, playlist, lang):
    # Delete bot's previous messages then send all songs from playlist
    clear_last_bot_messages(chat_id)
    song_ids = playlist.get("songs", [])
    if not song_ids:
        bot.send_message(chat_id, LOCALES[lang]["playlist_empty"])
        return
    bot.send_message(chat_id, LOCALES[lang]["playlist_playing"] + playlist.get("name"))
    songs_sent = 0
    for sid in song_ids:
        s = find_song(sid)
        if s:
            try:
                bot.send_audio(chat_id, s["url"].replace("file_id:", ""), caption=f"🎧 <b>{s.get('name')}</b>\n👤 {s.get('artist')}", parse_mode="HTML")
                songs_sent += 1
                increment_stat("songs_played", 1)
                time.sleep(0.15)  # gentle rate limit
            except Exception:
                pass
    increment_stat("playlists_played", 1)
    bot.send_message(chat_id, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
    log_action(f"Played playlist '{playlist.get('name')}' ({songs_sent} songs) for chat {chat_id}")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "menu" and
                     m.text in [LOCALES["ru"]["playlists"], LOCALES["en"]["playlists"]])
def handle_playlists_menu(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    user_state[chat]["step"] = "playlists_menu"
    bot.send_message(chat, LOCALES[lang]["choose_playlist"], reply_markup=playlists_menu_kb(lang))
    increment_stat("messages_handled", 1)

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "playlists_menu")
def handle_playlists_menu_actions(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    text = m.text
    if text == LOCALES[lang]["create_playlist"]:
        user_state[chat]["step"] = "creating_playlist_name"
        bot.send_message(chat, LOCALES[lang]["prompt_playlist_name"])
        return
    if text == LOCALES[lang]["my_playlists"]:
        pls = [p for p in load_playlists() if p.get("owner_id") == m.from_user.id]
        if not pls:
            bot.send_message(chat, LOCALES[lang]["no_playlists"])
            return
        lines = []
        for p in pls:
            lines.append(f"{p.get('id')}. {p.get('name')} (public={p.get('public')})")
        bot.send_message(chat, "\n".join(lines) + ("\n\nВведите ID плейлиста, чтобы проиграть, или 'меню'." if lang=="ru" else "\n\nType playlist ID to play, or 'menu'."))
        user_state[chat]["step"] = "choose_playlist_from_list"
        user_state[chat]["playlist_list"] = {str(p.get("id")): p.get("id") for p in pls}
        return
    if text == LOCALES[lang]["public_playlists"]:
        pls = [p for p in load_playlists() if p.get("public")]
        if not pls:
            bot.send_message(chat, ("Публичных плейлистов нет." if lang=="ru" else "No public playlists."))
            return
        lines = []
        for p in pls:
            lines.append(f"{p.get('id')}. {p.get('name')} (owner: {p.get('owner_id')})")
        bot.send_message(chat, "\n".join(lines) + ("\n\nВведите ID плейлиста, чтобы проиграть, или 'меню'." if lang=="ru" else "\n\nType playlist ID to play, or 'menu'."))
        user_state[chat]["step"] = "choose_playlist_from_public"
        user_state[chat]["playlist_list"] = {str(p.get("id")): p.get("id") for p in pls}
        return
    if text == LOCALES[lang]["back_to_menu"]:
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        return
    bot.send_message(chat, ("Неизвестная команда." if lang=="ru" else "Unknown command."))

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") in ["choose_playlist_from_list", "choose_playlist_from_public"])
def handle_choose_playlist_by_id(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    txt = (m.text or "").strip()
    if txt.lower() == LOCALES[lang]["menu"]:
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        return
    mapping = user_state[chat].get("playlist_list", {})
    pid = mapping.get(txt)
    if not pid:
        bot.send_message(chat, ( "Неверный ID." if lang=="ru" else "Invalid ID." ))
        return
    pls = load_playlists()
    pl = next((p for p in pls if int(p.get("id")) == int(pid)), None)
    if not pl:
        bot.send_message(chat, ( "Плейлист не найден." if lang=="ru" else "Playlist not found." ))
        return
    # Play playlist
    play_playlist(chat, pl, lang)
    increment_stat("playlists_played", 1)
    log_action(f"Playlist {pl.get('name')} played for @{m.from_user.username or m.from_user.id}")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "creating_playlist_name")
def handle_create_playlist_name(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    name = (m.text or "").strip()
    if not name:
        bot.send_message(chat, LOCALES[lang]["prompt_playlist_name"])
        return
    user_state[chat]["new_playlist_name"] = name
    user_state[chat]["step"] = "creating_playlist_public"
    bot.send_message(chat, LOCALES[lang]["prompt_playlist_public"])

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "creating_playlist_public")
def handle_create_playlist_public(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    txt = (m.text or "").strip().lower()
    public = txt in ["да", "yes", "y", "true", "1"]
    pls = load_playlists()
    pid = next_playlist_id()
    new_pl = {
        "id": pid,
        "owner_id": m.from_user.id,
        "name": user_state[chat].get("new_playlist_name"),
        "public": bool(public),
        "songs": [],
        "created_at": datetime.utcnow().isoformat()
    }
    pls.append(new_pl)
    save_playlists(pls)
    increment_stat("playlists_created", 1)
    user_state[chat]["step"] = "menu"
    bot.send_message(chat, LOCALES[lang]["playlist_created"], reply_markup=main_menu_kb(lang))
    log_action(f"Playlist created: {new_pl.get('name')} (public={new_pl.get('public')}) by @{m.from_user.username or m.from_user.id}")

# ---------------------------
# Player controls: Prev / Next / Add to playlist / Menu
# These are reply-based buttons, handled globally
# ---------------------------
@bot.message_handler(func=lambda m: m.text in ["⏮ Назад", "⏭ Вперёд", "➕ Добавить в плейлист", LOCALES["ru"]["menu"], LOCALES["en"]["menu"]])
def handle_player_controls(m):
    chat = m.chat.id
    text = m.text
    st = user_state.get(chat, {})
    lang = st.get("lang", "ru")
    # Prev/Next: naive implementation uses current mode to find list to iterate
    if text in ["⏮ Назад", "⏭ Вперёд"]:
        mode = st.get("mode")
        last = st.get("last_song")
        data_songs = load_songs()
        if mode == "genre":
            genre = st.get("genre")
            pool = [s for s in data_songs if s.get("genre","").lower() == (genre or "").lower()]
        else:
            pool = data_songs
        if not pool:
            bot.send_message(chat, LOCALES[lang]["no_songs"])
            return
        # find index
        idx = 0
        if last:
            ids = [int(s.get("id")) for s in pool]
            try:
                idx = ids.index(int(last.get("id")))
            except Exception:
                idx = 0
        if text == "⏭ Вперёд":
            idx = (idx + 1) % len(pool)
        else:
            idx = (idx - 1) % len(pool)
        song = pool[idx]
        st["last_song"] = song
        user_state[chat] = st
        send_song_with_controls(chat, song, lang)
        log_action(f"Player control {text} used by @{m.from_user.username or m.from_user.id}")
        return

    # Add to playlist
    if text == "➕ Добавить в плейлист":
        last = st.get("last_song")
        if not last:
            bot.send_message(chat, LOCALES[lang]["no_last_song"])
            return
        # show user's playlists and create option
        pls = [p for p in load_playlists() if p.get("owner_id") == m.from_user.id]
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if pls:
            for p in pls:
                kb.add(f"ID:{p.get('id')} {p.get('name')}")
        kb.add(LOCALES[lang]["create_playlist"], LOCALES[lang]["back_to_menu"])
        user_state[chat]["step"] = "add_to_playlist_choose"
        user_state[chat]["to_add_song_id"] = last.get("id")
        bot.send_message(chat, LOCALES[lang]["prompt_choose_playlist_for_add"], reply_markup=kb)
        return

    # Menu
    if text.lower() in [LOCALES[lang]["menu"], LOCALES[lang]["back_to_menu"], "menu", "меню"]:
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        return

# Adding song into chosen playlist flow
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "add_to_playlist_choose")
def handle_add_to_playlist_choose(m):
    chat = m.chat.id
    st = user_state.get(chat, {})
    lang = st.get("lang","ru")
    txt = (m.text or "").strip()
    if txt == LOCALES[lang]["create_playlist"]:
        user_state[chat]["step"] = "creating_playlist_name_from_add"
        bot.send_message(chat, LOCALES[lang]["prompt_playlist_name"])
        return
    if txt == LOCALES[lang]["back_to_menu"]:
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        return
    # parse "ID:<id> <name>"
    if txt.startswith("ID:"):
        pid = txt.split()[0].replace("ID:", "")
        pls = load_playlists()
        pl = next((p for p in pls if int(p.get("id")) == int(pid) and p.get("owner_id") == m.from_user.id), None)
        if not pl:
            bot.send_message(chat, ( "Плейлист не найден." if lang=="ru" else "Playlist not found." ))
            return
        sid = user_state[chat].get("to_add_song_id")
        if sid is None:
            bot.send_message(chat, ( LOCALES[lang]["no_last_song"] ))
            return
        if int(sid) not in pl.get("songs", []):
            pl["songs"].append(int(sid))
            save_playlists(pls)
            bot.send_message(chat, LOCALES[lang]["playlist_added_song"])
            increment_stat("messages_handled", 1)
            log_action(f"Song {sid} added to playlist {pl.get('name')} by @{m.from_user.username or m.from_user.id}")
        else:
            bot.send_message(chat, LOCALES[lang]["song_already_in_playlist"])
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        return
    bot.send_message(chat, LOCALES[lang]["invalid_choice"])

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "creating_playlist_name_from_add")
def handle_create_playlist_from_add_name(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    name = (m.text or "").strip()
    if not name:
        bot.send_message(chat, LOCALES[lang]["prompt_playlist_name"])
        return
    user_state[chat]["new_playlist_name"] = name
    user_state[chat]["step"] = "creating_playlist_public_from_add"
    bot.send_message(chat, LOCALES[lang]["prompt_playlist_public"])

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "creating_playlist_public_from_add")
def handle_create_playlist_from_add_public(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    txt = (m.text or "").strip().lower()
    public = txt in ["да","yes","y","true","1"]
    pls = load_playlists()
    pid = next_playlist_id()
    new_pl = {
        "id": pid,
        "owner_id": m.from_user.id,
        "name": user_state[chat].get("new_playlist_name"),
        "public": bool(public),
        "songs": [],
        "created_at": datetime.utcnow().isoformat()
    }
    # add song if present
    sid = user_state[chat].get("to_add_song_id")
    if sid:
        new_pl["songs"].append(int(sid))
    pls.append(new_pl)
    save_playlists(pls)
    increment_stat("playlists_created", 1)
    user_state[chat]["step"] = "menu"
    bot.send_message(chat, LOCALES[lang]["playlist_created"], reply_markup=main_menu_kb(lang))
    log_action(f"Playlist created and song added: {new_pl.get('name')} by @{m.from_user.username or m.from_user.id}")

# ---------------------------
# Suggest / Add song (improved)
# ---------------------------
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "menu" and
                     m.text in [LOCALES["ru"]["suggest"], LOCALES["en"]["suggest"]])
def handle_suggest_start(m):
    chat = m.chat.id
    lang = user_state[chat]["lang"]
    user_state[chat]["step"] = "audio"
    bot.send_message(chat, "🎶 " + ("Пришлите аудиофайл песни (mp3, wav и т.п.)" if lang=="ru" else "Send audio file (mp3, wav etc.)"))

@bot.message_handler(content_types=["audio"])
def handle_get_audio(m):
    chat = m.chat.id
    st = user_state.get(chat, {})
    # allow audio even if no state (treat as new suggest flow)
    if st.get("step") != "audio":
        return
    st["audio"] = m.audio.file_id
    st["step"] = "name"
    user_state[chat] = st
    bot.send_message(chat, "📛 " + ("Введите название песни:" if st.get("lang","ru")=="ru" else "Enter song title:"))

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "name")
def handle_get_name(m):
    chat = m.chat.id
    st = user_state.get(chat, {})
    st["name"] = m.text
    st["step"] = "artist"
    user_state[chat] = st
    bot.send_message(chat, "👤 Введите имя артиста:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "artist")
def handle_get_artist(m):
    chat = m.chat.id
    st = user_state.get(chat, {})
    st["artist"] = m.text
    st["step"] = "genre"
    user_state[chat] = st
    bot.send_message(chat, "🎧 Введите жанр песни:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "genre")
def handle_get_genre(m):
    chat = m.chat.id
    st = user_state.get(chat, {})
    st["genre"] = m.text
    st["step"] = "lang_song"
    user_state[chat] = st
    bot.send_message(chat, "🌐 Введите язык песни:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "lang_song")
def handle_get_lang_song(m):
    chat = m.chat.id
    st = user_state.get(chat, {})
    st["lang"] = m.text
    # send to archive channel
    try:
        sent = bot.send_audio(ARCHIVE_CHANNEL_ID, audio=st["audio"], caption=f"{st['name']} — {st['artist']} ({st['genre']})")
    except Exception:
        bot.send_message(chat, "Ошибка при отправке в архив: убедитесь, что бот добавлен в канал как админ.")
        user_state.pop(chat, None)
        return
    # create song entry
    sid = int(time.time())  # local unique id if not using telegram msg id
    # attempt to use telegram message id if available
    try:
        sid = sent.message_id
    except Exception:
        sid = sid
    try:
        short_chat = str(sent.chat.id)
        if short_chat.startswith("-100"):
            short = short_chat[4:]
        else:
            short = short_chat.lstrip("-")
        archive_url = f"https://t.me/c/{short}/{sent.message_id}"
    except Exception:
        archive_url = ""
    song_entry = {
        "id": sid,
        "name": st["name"],
        "artist": st["artist"],
        "genre": st["genre"],
        "lang": st["lang"],
        "url": f"file_id:{st['audio']}",
        "archive_url": archive_url
    }
    songs = load_songs()
    songs.append(song_entry)
    save_songs(songs)
    increment_stat("songs_added", 1)
    bot.send_message(chat, LOCALES[st.get("lang","ru")]["thank_song"], reply_markup=main_menu_kb(st.get("lang","ru")))
    user_state[chat] = {"step": "menu", "lang": st.get("lang","ru")}
    increment_stat("messages_handled", 1)
    log_action(f"🎵 @{m.from_user.username or 'аноним'} added song: {song_entry['name']} — {song_entry['artist']} (id:{sid})")

# ---------------------------
# /tell admin -> broadcast
# ---------------------------
@bot.message_handler(commands=["tell"])
def handle_tell(m):
    if m.from_user.id != ADMIN_ID:
        bot.send_message(m.chat.id, LOCALES["ru"]["tell_no_perm"])
        return
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(m.chat.id, "Usage: /tell <message>")
        return
    msg = parts[1]
    users = load_users()
    sent_count = 0
    for u in users:
        try:
            bot.send_message(u.get("id"), f"📢 Админ сообщение:\n\n{msg}")
            sent_count += 1
            time.sleep(0.05)
        except Exception:
            pass
    bot.send_message(m.chat.id, f"Разослано: {sent_count}")
    log_action(f"/tell by admin -> {sent_count} users")

# ---------------------------
# /stats admin
# ---------------------------
@bot.message_handler(commands=["stats"])
def handle_stats(m):
    if m.from_user.id != ADMIN_ID:
        bot.send_message(m.chat.id, "No permission")
        return
    s = load_stats()
    users_count = len(load_users())
    songs_count = len(load_songs())
    pls_count = len(load_playlists())
    bot.send_message(m.chat.id, f"📊 Stats:\nUsers: {users_count}\nSongs: {songs_count}\nPlaylists: {pls_count}\n\nDetails:\n{json.dumps(s, ensure_ascii=False, indent=2)}")

# ---------------------------
# Fallback: keep UX friendly
# ---------------------------
@bot.message_handler(func=lambda m: True)
def fallback(m):
    chat = m.chat.id
    st = user_state.get(chat)
    if not st:
        add_user_record(m.from_user)
        user_state[chat] = {"step": "choose_lang", "lang": "ru"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add("🇷🇺 Русский", "🇬🇧 English")
        bot.send_message(chat, LOCALES["ru"]["choose_lang"], reply_markup=kb)
        return
    lang = st.get("lang", "ru")
    txt = (m.text or "").strip()
    # basic menu shortcut
    if txt.lower() in [LOCALES[lang]["menu"], LOCALES[lang]["back_to_menu"], "menu", "меню"]:
        user_state[chat]["step"] = "menu"
        bot.send_message(chat, LOCALES[lang]["main_menu"], reply_markup=main_menu_kb(lang))
        return
    # otherwise polite hint
    bot.send_message(chat, ("Я не понял, выберите опцию из меню." if lang=="ru" else "I didn't understand, please choose from the menu."))
    increment_stat("messages_handled", 1)

# ---------------------------
# Start polling
# ---------------------------
if __name__ == "__main__":
    print("✅ Advanced Music Bot (full) started")
    bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
