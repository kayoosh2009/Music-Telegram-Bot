import random
from telebot import types
from utils import load_json, save_json, add_user, update_stats, log_action
import user_state  # наш модуль user_state.py

SONGS_FILE = "songs.json"
PLAYLISTS_FILE = "playlists.json"

def register_handlers(bot):
    """Регистрирует обработчики. Всё через кнопки, плеер помнит жанр и историю played."""

    # ---- клавиатуры ----
    def main_menu_kb():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("🎲 Рандом", "🎧 Жанры")
        kb.row("🔍 Поиск", "📂 Плейлисты")
        kb.row("🎤 Предложить песню")
        return kb

    def player_kb():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("⏮ Назад", "➕ В плейлист", "⏭ Вперёд")
        kb.row("🔙 В меню")
        return kb

    def create_playlist_kb():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("➕ Создать плейлист", "🔙 В меню")
        return kb

    # ---- /start ----
    @bot.message_handler(commands=["start"])
    def start_cmd(message):
        add_user(message.from_user)
        log_action(bot, None, f"/start от @{message.from_user.username or message.from_user.id}")
        bot.send_message(message.chat.id, "🎵 Добро пожаловать! Выберите действие:", reply_markup=main_menu_kb())

    # ---- Рандом ----
    @bot.message_handler(func=lambda m: m.text == "🎲 Рандом")
    def random_song(message):
        songs = load_json(SONGS_FILE, [])
        if not songs:
            bot.send_message(message.chat.id, "😢 В архиве пока нет песен.", reply_markup=main_menu_kb())
            return
        song = random.choice(songs)
        send_song(bot, message.chat.id, song)
        update_stats("songs_played")
        # сбрасываем genre и ставим played только с этой песней
        user_state.save_user_state(message.from_user.id, {"genre": None, "played": [song["id"]], "last_song_id": song["id"]})

    # ---- Жанры ----
    @bot.message_handler(func=lambda m: m.text == "🎧 Жанры")
    def genres_list(message):
        songs = load_json(SONGS_FILE, [])
        genres = sorted({s.get("genre", "Unknown") for s in songs})
        if not genres:
            bot.send_message(message.chat.id, "🎵 Жанров пока нет.", reply_markup=main_menu_kb())
            return
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for g in genres:
            kb.add(g)
        kb.add("🔙 В меню")
        bot.send_message(message.chat.id, "🎼 Выберите жанр:", reply_markup=kb)

    # ---- Выбор жанра (только если текст совпадает с жанром) ----
    @bot.message_handler(func=lambda m: True)
    def choose_genre_or_handle_buttons(message):
        txt = (message.text or "").strip()
        chat = message.chat.id

        # кнопка возврата
        if txt == "🔙 В меню":
            bot.send_message(chat, "🏠 Главное меню", reply_markup=main_menu_kb())
            return

        # команды плеера
        if txt in {"⏮ Назад", "⏭ Вперёд", "➕ В плейлист"}:
            # перенаправляем в отдельный handler (внутри одного файла — просто вызываем функцию)
            handle_player_controls(message)
            return

        # если это жанр — обрабатываем
        songs = load_json(SONGS_FILE, [])
        genres = {s.get("genre", "Unknown") for s in songs}
        if txt in genres:
            songs_by_genre = [s for s in songs if (s.get("genre") or "").lower() == txt.lower()]
            if not songs_by_genre:
                bot.send_message(chat, "😢 Песен в этом жанре пока нет.", reply_markup=main_menu_kb())
                return
            # выбор песни без повторов: отмечаем played
            state = user_state.get_user_state(message.from_user.id)
            played = state.get("played", [])
            available = [s for s in songs_by_genre if s["id"] not in played]
            if not available:
                # все сыграны — очистим историю (но сохраним last_song_id если хотим)
                played = []
                available = songs_by_genre.copy()
            song = random.choice(available)
            played.append(song["id"])
            state["genre"] = txt
            state["played"] = played
            state["last_song_id"] = song["id"]
            user_state.save_user_state(message.from_user.id, state)
            send_song(bot, chat, song)
            update_stats("songs_played")
            return

        # остальное — проверка на меню-кнопки (игнорируем вводы свободного текста)
        buttons = {"🎲 Рандом", "🎧 Жанры", "🔍 Поиск", "📂 Плейлисты", "🎤 Предложить песню"}
        if txt in buttons:
            # обработчик отдельных кнопок уже создан, просто вернёмся
            return

        # если текст не распознан — напомнить использовать кнопки
        bot.send_message(chat, "📱 Пожалуйста, используйте кнопки меню.", reply_markup=main_menu_kb())

    # ---- Плеер: Prev / Next / Add to playlist ----
    def handle_player_controls(message):
        txt = (message.text or "").strip()
        chat = message.chat.id
        user_id = message.from_user.id

        songs = load_json(SONGS_FILE, [])
        if not songs:
            bot.send_message(chat, "😢 В архиве нет песен.", reply_markup=main_menu_kb())
            return

        state = user_state.get_user_state(user_id)
        genre = state.get("genre")  # может быть None
        played = state.get("played", [])
        last_song_id = state.get("last_song_id")

        # используем pool — если genre задан, берём песни только из него
        if genre:
            pool = [s for s in songs if (s.get("genre") or "").lower() == genre.lower()]
        else:
            pool = songs.copy()

        # убрать повторы подряд: доступные — те, что не в played
        available = [s for s in pool if s["id"] not in played]

        if txt == "⏭ Вперёд":
            if not available:
                # если все сыграны — очистим историю и доступен весь пул
                played = []
                available = pool.copy()
            # выбираем случайную из available
            song = random.choice(available)
            played.append(song["id"])
            state["played"] = played
            state["last_song_id"] = song["id"]
            user_state.save_user_state(user_id, state)
            send_song(bot, chat, song)
            update_stats("songs_played")
            return

        if txt == "⏮ Назад":
            # попробуем найти предыдущую: если played есть и len>1 — вернём предыдущий элемент
            if played and len(played) >= 2:
                # current is last element; previous is -2
                prev_id = played[-2]
                prev_song = next((s for s in pool if s["id"] == prev_id), None)
                if prev_song:
                    # откатываем played: удаляем последний (current), оставляем prev как последний
                    played = played[:-1]
                    state["played"] = played
                    state["last_song_id"] = prev_id
                    user_state.save_user_state(user_id, state)
                    send_song(bot, chat, prev_song)
                    return
            # если нет истории — просто сработает как вперёд (или случайная)
            if not pool:
                bot.send_message(chat, "Нет доступных треков.", reply_markup=main_menu_kb())
                return
            song = random.choice(pool)
            # обновляем played: добавляем, но не душим массив
            if song["id"] not in played:
                played.append(song["id"])
            state["played"] = played
            state["last_song_id"] = song["id"]
            user_state.save_user_state(user_id, state)
            send_song(bot, chat, song)
            update_stats("songs_played")
            return

        if txt == "➕ В плейлист":
            # добавление текущей песни в плейлист
            if not last_song_id:
                bot.send_message(chat, "Нет последней проигранной песни для добавления.", reply_markup=main_menu_kb())
                return
            # загрузим плейлисты пользователя (структура: dict user_id -> list of playlists)
            pls_all = load_json(PLAYLISTS_FILE, {})
            pls_user = pls_all.get(str(user_id), [])
            if not pls_user:
                bot.send_message(chat, "У вас нет плейлистов. Хотите создать?", reply_markup=create_playlist_kb())
                return
            # предложим выбрать плейлист (кнопки)
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for p in pls_user:
                kb.add(p["name"])
            kb.add("➕ Создать плейлист", "🔙 В меню")
            # временно сохраняем в state, что мы ждём выбора плейлиста для добавления
            state["awaiting_add_song_id"] = last_song_id
            user_state.save_user_state(user_id, state)
            bot.send_message(chat, "Выберите плейлист для добавления:", reply_markup=kb)
            return

    # ---- Плейлисты: показать / создать / добавить ----
    @bot.message_handler(func=lambda m: m.text == "📂 Плейлисты")
    def show_playlists(message):
        user_id = message.from_user.id
        pls_all = load_json(PLAYLISTS_FILE, {})
        pls_user = pls_all.get(str(user_id), [])
        if not pls_user:
            bot.send_message(message.chat.id, "📂 У вас пока нет плейлистов.", reply_markup=create_playlist_kb())
            return
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for p in pls_user:
            kb.add(p["name"])
        kb.add("➕ Создать плейлист", "🔙 В меню")
        bot.send_message(message.chat.id, "Ваши плейлисты:", reply_markup=kb)

    # обработка создания нового плейлиста
    @bot.message_handler(func=lambda m: m.text == "➕ Создать плейлист")
    def create_playlist_start(message):
        bot.send_message(message.chat.id, "Введите имя нового плейлиста:")
        bot.register_next_step_handler(message, create_playlist_name)

    def create_playlist_name(message):
        name = (message.text or "").strip()
        if not name:
            bot.send_message(message.chat.id, "Имя не может быть пустым.", reply_markup=main_menu_kb())
            return
        user_id = message.from_user.id
        pls_all = load_json(PLAYLISTS_FILE, {})
        pls_user = pls_all.get(str(user_id), [])
        if any(p["name"].lower() == name.lower() for p in pls_user):
            bot.send_message(message.chat.id, "Плейлист с таким именем уже существует.", reply_markup=main_menu_kb())
            return
        pls_user.append({"name": name, "songs": []})
        pls_all[str(user_id)] = pls_user
        save_json(PLAYLISTS_FILE, pls_all)
        update_stats("playlists_created")
        bot.send_message(message.chat.id, f"✅ Плейлист «{name}» создан.", reply_markup=main_menu_kb())

    # обработка выбора плейлиста (в т.ч. для добавления песни)
    @bot.message_handler(func=lambda m: True)
    def playlist_selection_and_other(message):
        txt = (message.text or "").strip()
        user_id = message.from_user.id
        # сначала проверим: возможно пользователь выбрал существующий плейлист (название)
        pls_all = load_json(PLAYLISTS_FILE, {})
        pls_user = pls_all.get(str(user_id), [])
        matching = next((p for p in pls_user if p["name"] == txt), None)
        if matching:
            # если в state есть awaiting_add_song_id -> добавляем туда
            state = user_state.get_user_state(user_id)
            pending = state.get("awaiting_add_song_id")
            if pending:
                # добавляем song id (int)
                if pending not in matching["songs"]:
                    matching["songs"].append(pending)
                    save_json(PLAYLISTS_FILE, pls_all)
                    bot.send_message(message.chat.id, f"✅ Песня добавлена в плейлист «{matching['name']}»", reply_markup=main_menu_kb())
                    # очистим ожидание
                    state.pop("awaiting_add_song_id", None)
                    user_state.save_user_state(user_id, state)
                    return
                else:
                    bot.send_message(message.chat.id, "Песня уже в плейлисте.", reply_markup=main_menu_kb())
                    state.pop("awaiting_add_song_id", None)
                    user_state.save_user_state(user_id, state)
                    return
            # если просто захотел проиграть плейлист — отправляем все песни
            if matching.get("songs"):
                bot.send_message(message.chat.id, f"▶️ Воспроизвожу плейлист «{matching['name']}»...")
                # удаляем старые контролы — у тебя это можно реализовать отдельно, но тут просто отправим песни
                for sid in matching["songs"]:
                    s = next((x for x in load_json(SONGS_FILE, []) if x["id"] == sid), None)
                    if s:
                        bot.send_audio(message.chat.id, s.get("url", "").replace("file_id:", ""), caption=f"{s.get('name')} — {s.get('artist')}")
                bot.send_message(message.chat.id, "Готово.", reply_markup=main_menu_kb())
                return
            else:
                bot.send_message(message.chat.id, "Плейлист пуст.", reply_markup=main_menu_kb())
                return

        # если не совпало с именем плейлиста — ничего не делаем здесь (другие обработчики выше уже)
        # для прочих случаев — не шлём ошибки, а попросим использовать меню
        if txt not in {"🎲 Рандом", "🎧 Жанры", "🔍 Поиск", "📂 Плейлисты", "🎤 Предложить песню", "🔙 В меню", "⏮ Назад", "⏭ Вперёд", "➕ В плейлист", "➕ Создать плейлист"}:
            bot.send_message(message.chat.id, "📱 Используйте кнопки меню.", reply_markup=main_menu_kb())

    # ---- отправка песни (с контролами) ----
    def send_song(bot_obj, chat_id, song):
        audio_id = song.get("url", "").replace("file_id:", "")
        caption = f"🎵 <b>{song.get('name')}</b>\n👤 {song.get('artist')}\n🎼 {song.get('genre')} | 🌐 {song.get('lang')}"
        try:
            bot_obj.send_audio(chat_id, audio_id, caption=caption, parse_mode="HTML")
        except Exception:
            # на всякий случай — если отправка через file_id не работает, пробуем как есть
            try:
                bot_obj.send_audio(chat_id, song.get("url"))
            except Exception as e:
                bot_obj.send_message(chat_id, f"Ошибка отправки аудио: {e}")
                return
        # контрольные кнопки (reply keyboard)
        bot_obj.send_message(chat_id, "🎧 Управление плеером:", reply_markup=player_kb())

    # экспорт функции в глобальную область (если другие модули хотят вызвать)
    globals()["send_song"] = send_song
