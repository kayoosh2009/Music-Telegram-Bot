import os
import random
from telebot import types
from utils import load_json, save_json, add_user, update_stats, log_action
import user_state

# Пути к JSON
DATA_DIR = "data"
SONGS_FILE = os.path.join(DATA_DIR, "songs.json")
PLAYLISTS_FILE = os.path.join(DATA_DIR, "playlists.json")

# --- Клавиатуры ---
def kb_main():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎧 Жанры", "🎲 Рандом")
    kb.add("🎵 Мои плейлисты", "➕ Создать плейлист")
    kb.add("📊 Статистика", "💬 Предложить песню")
    return kb


def kb_genres():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # русские жанры сверху
    genres = ["Панк", "Постпанк", "Лоуфай", "Поп", "Рок", "Рэп", "Инди"]
    kb.add(*genres)
    kb.add("🔙 В меню")
    return kb


def kb_player():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⏮ Назад", "⏭ Вперёд")
    kb.add("➕ В плейлист", "🔙 В меню")
    return kb


def kb_playlist_base():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📜 Мои плейлисты", "➕ Создать плейлист")
    kb.add("🔙 В меню")
    return kb


# --- Утилиты ---
def _norm(txt: str) -> str:
    return str(txt).strip().lower()


def _send_audio(bot, chat_id, song):
    """Отправка трека пользователю"""
    try:
        if str(song["url"]).startswith("file_id:"):
            file_id = song["url"].replace("file_id:", "")
            bot.send_audio(chat_id, file_id, title=song["name"], performer=song["artist"])
        else:
            bot.send_message(chat_id, f"⚠️ Файл не найден для {song['name']}")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при отправке трека: {e}")
        log_action(f"Ошибка отправки трека {song.get('name')}: {e}")


# === РЕГИСТРАЦИЯ ВСЕХ ХЕНДЛЕРОВ ===
def register_handlers(bot):
    # /start
    @bot.message_handler(commands=["start"])
    def cmd_start(msg):
        add_user(msg.from_user)
        update_stats("registered_users")
        bot.send_message(
            msg.chat.id,
            f"Привет, {msg.from_user.first_name}! 👋\n\nЯ — Telegram Music 🎧\n"
            "Выбери жанр или включи рандом, чтобы начать слушать!",
            reply_markup=kb_main(),
        )
        log_action(f"Пользователь {msg.from_user.id} запустил бота")

    # Главное меню
    @bot.message_handler(func=lambda m: _norm(m.text) in {_norm("🏠 меню"), _norm("🔙 в меню")})
    def cmd_menu(msg):
        bot.send_message(msg.chat.id, "🏠 Главное меню", reply_markup=kb_main())

    # --- ЖАНРЫ ---
    @bot.message_handler(func=lambda m: _norm(m.text) in {_norm("🎧 жанры")})
    def cmd_genres(msg):
        bot.send_message(msg.chat.id, "Выберите жанр:", reply_markup=kb_genres())

    @bot.message_handler(func=lambda m: _norm(m.text) in {_norm(x) for x in ["панк", "постпанк", "лоуфай", "поп", "рок", "рэп", "инди"]})
    def handle_genre_selection(msg):
        genre = msg.text.strip()
        songs = load_json(SONGS_FILE, [])
        available = [s for s in songs if _norm(s.get("genre")) == _norm(genre)]

        if not available:
            bot.send_message(msg.chat.id, f"⚠️ Нет песен в жанре {genre}.", reply_markup=kb_main())
            return

        song = random.choice(available)
        _send_audio(bot, msg.chat.id, song)

        user_state.save_user_state(msg.from_user.id, {"genre": genre, "played": [song["id"]], "last_song_id": song["id"]})
        update_stats("songs_played")

        bot.send_message(msg.chat.id, "🎧 Управление плеером:", reply_markup=kb_player())

    # --- РАНДОМ ---
    @bot.message_handler(func=lambda m: _norm(m.text) == _norm("🎲 рандом"))
    def cmd_random(msg):
        songs = load_json(SONGS_FILE, [])
        if not songs:
            bot.send_message(msg.chat.id, "Нет песен для воспроизведения.", reply_markup=kb_main())
            return

        st = user_state.get_user_state(msg.from_user.id)
        played = st.get("played", [])

        available = [s for s in songs if s["id"] not in played]
        if not available:
            st["played"] = []
            user_state.save_user_state(msg.from_user.id, st)
            available = songs

        song = random.choice(available)
        _send_audio(bot, msg.chat.id, song)

        st.setdefault("played", []).append(song["id"])
        st["last_song_id"] = song["id"]
        user_state.save_user_state(msg.from_user.id, st)

        update_stats("songs_played")
        bot.send_message(msg.chat.id, "🎧 Управление плеером:", reply_markup=kb_player())

    # --- ПЛЕЕР ---
    @bot.message_handler(func=lambda m: _norm(m.text) in {_norm("⏭ вперёд"), _norm("⏮ назад"), _norm("➕ в плейлист"), _norm("🔙 в меню")})
    def cmd_player_controls(msg):
        txt = _norm(msg.text)
        chat = msg.chat.id
        uid = msg.from_user.id

        if txt == _norm("🔙 в меню"):
            bot.send_message(chat, "🏠 Главное меню", reply_markup=kb_main())
            return

        songs = load_json(SONGS_FILE, [])
        if not songs:
            bot.send_message(chat, "⚠️ Нет песен.", reply_markup=kb_main())
            return

        st = user_state.get_user_state(uid)
        genre = st.get("genre")
        played = st.get("played", [])
        last_id = st.get("last_song_id")

        # Вперёд
        if txt == _norm("⏭ вперёд"):
            pool = [s for s in songs if not genre or _norm(s.get("genre")) == _norm(genre)]
            available = [s for s in pool if s["id"] not in played and s["id"] != last_id]

            if not available:
                st["played"] = []
                user_state.save_user_state(uid, st)
                available = [s for s in pool if s["id"] != last_id]

            if not available:
                bot.send_message(chat, "🎵 Это все песни в этом жанре!", reply_markup=kb_main())
                return

            song = random.choice(available)
            st.setdefault("played", []).append(song["id"])
            st["last_song_id"] = song["id"]
            user_state.save_user_state(uid, st)

            _send_audio(bot, chat, song)
            update_stats("songs_played")
            return

        # Назад
        if txt == _norm("⏮ назад"):
            if len(played) >= 2:
                prev_id = played[-2]
                prev_song = next((s for s in songs if s["id"] == prev_id), None)
                if prev_song:
                    st["played"] = played[:-1]
                    st["last_song_id"] = prev_id
                    user_state.save_user_state(uid, st)
                    _send_audio(bot, chat, prev_song)
                    return
            bot.send_message(chat, "Нет предыдущей песни.", reply_markup=kb_player())
            return

        # Добавить в плейлист
        if txt == _norm("➕ в плейлист"):
            last = st.get("last_song_id")
            if not last:
                bot.send_message(chat, "Нет активной песни для добавления.", reply_markup=kb_main())
                return

            pls = load_json(PLAYLISTS_FILE, [])
            my = [p for p in pls if p["owner_id"] == uid]
            if not my:
                bot.send_message(chat, "У вас нет плейлистов.", reply_markup=kb_playlist_base())
                return

            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for p in my:
                kb.add(p["name"])
            kb.add("🔙 В меню")

            st["awaiting_add_song_id"] = last
            user_state.save_user_state(uid, st)

            bot.send_message(chat, "Выберите плейлист для добавления:", reply_markup=kb)
            return

    # --- СОЗДАНИЕ ПЛЕЙЛИСТА ---
    @bot.message_handler(func=lambda m: _norm(m.text) == _norm("➕ создать плейлист"))
    def cmd_create_playlist(msg):
        pls = load_json(PLAYLISTS_FILE, [])
        new_pl = {
            "id": len(pls) + 1,
            "owner_id": msg.from_user.id,
            "name": f"Мой плейлист {len(pls) + 1}",
            "public": True,
            "songs": [],
        }
        pls.append(new_pl)
        save_json(PLAYLISTS_FILE, pls)
        update_stats("playlists_created")
        bot.send_message(msg.chat.id, f"✅ Создан новый плейлист: {new_pl['name']}", reply_markup=kb_playlist_base())

    # --- ДОБАВЛЕНИЕ ПЕСНИ ---
    @bot.message_handler(func=lambda m: True)
    def handle_all(msg):
        uid = msg.from_user.id
        st = user_state.get_user_state(uid)
        song_id = st.get("awaiting_add_song_id")

        if song_id and msg.text:
            pls = load_json(PLAYLISTS_FILE, [])
            pl = next((p for p in pls if p["owner_id"] == uid and _norm(p["name"]) == _norm(msg.text)), None)

            if pl:
                if song_id not in pl["songs"]:
                    pl["songs"].append(song_id)
                    save_json(PLAYLISTS_FILE, pls)
                    bot.send_message(msg.chat.id, "✅ Песня добавлена в плейлист!", reply_markup=kb_player())
                else:
                    bot.send_message(msg.chat.id, "⚠️ Песня уже в этом плейлисте.", reply_markup=kb_player())
            else:
                bot.send_message(msg.chat.id, "⚠️ Плейлист не найден.", reply_markup=kb_main())

            st.pop("awaiting_add_song_id", None)
            user_state.save_user_state(uid, st)
            return

        # Если ничего не подходит
        bot.send_message(msg.chat.id, "📱 Пожалуйста, используйте кнопки меню.", reply_markup=kb_main())
