import logging
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import yt_dlp
import asyncio

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (берём из переменных окружения для безопасности)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('music_cache.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tracks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  artist TEXT,
                  youtube_url TEXT UNIQUE,
                  file_id TEXT,
                  genre TEXT,
                  duration INTEGER)''')
    conn.commit()
    conn.close()

# Жанры с примерами запросов
GENRES = {
    '🎸 Рок': ['rock music', 'rock hits', 'classic rock'],
    '🎤 Поп': ['pop music', 'pop hits', 'top pop songs'],
    '🎧 Хип-хоп': ['hip hop music', 'rap hits', 'hip hop beats'],
    '🎹 Джаз': ['jazz music', 'smooth jazz', 'jazz classics'],
    '🎵 Электро': ['electronic music', 'edm hits', 'electronic dance'],
    '🎻 Классика': ['classical music', 'orchestra', 'classical piano']
}

# Функция для поиска музыки на YouTube
def search_youtube(query, max_results=5):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'socket_timeout': 30,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            if 'entries' in search_results:
                return search_results['entries']
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
    return []

# Функция для скачивания музыки
async def download_audio(youtube_url):
    output_path = '/tmp/downloads'
    os.makedirs(output_path, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            return filename, info.get('title', 'Unknown'), info.get('duration', 0)
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None, None, None

# Проверка кэша в БД
def get_cached_track(youtube_url):
    conn = sqlite3.connect('music_cache.db')
    c = conn.cursor()
    c.execute("SELECT file_id, title FROM tracks WHERE youtube_url = ?", (youtube_url,))
    result = c.fetchone()
    conn.close()
    return result

# Сохранение в кэш
def save_to_cache(title, youtube_url, file_id, genre, duration):
    conn = sqlite3.connect('music_cache.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO tracks (title, youtube_url, file_id, genre, duration) VALUES (?, ?, ?, ?, ?)",
                  (title, youtube_url, file_id, genre, duration))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Уже существует
    conn.close()

# Главное меню
def main_menu_keyboard():
    keyboard = []
    row = []
    for i, genre in enumerate(GENRES.keys()):
        row.append(InlineKeyboardButton(genre, callback_data=f"genre_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔍 Поиск", callback_data="search")])
    return InlineKeyboardMarkup(keyboard)

# Меню жанра
def genre_menu_keyboard(genre_index):
    keyboard = []
    genre_name = list(GENRES.keys())[genre_index]
    
    keyboard.append([InlineKeyboardButton("🎲 Случайный трек", callback_data=f"random_{genre_index}")])
    keyboard.append([InlineKeyboardButton("🔍 Поиск в жанре", callback_data=f"search_{genre_index}")])
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_main")])
    
    return InlineKeyboardMarkup(keyboard)

# Меню результатов поиска
def search_results_keyboard(results, genre=None):
    keyboard = []
    for i, result in enumerate(results[:5]):
        title = result.get('title', 'Unknown')
        if len(title) > 40:
            title = title[:37] + "..."
        keyboard.append([InlineKeyboardButton(
            f"🎵 {title}", 
            callback_data=f"play_{result['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 *Музыкальный бот*\n\n"
        "Выбери жанр или используй поиск:",
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard()
    )

# Обработка нажатий кнопок
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Главное меню
    if data == "back_main":
        await query.edit_message_text(
            "🎵 *Музыкальный бот*\n\n"
            "Выбери жанр или используй поиск:",
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )
    
    # Выбор жанра
    elif data.startswith("genre_"):
        genre_index = int(data.split("_")[1])
        genre_name = list(GENRES.keys())[genre_index]
        await query.edit_message_text(
            f"*{genre_name}*\n\nЧто хочешь послушать?",
            parse_mode='Markdown',
            reply_markup=genre_menu_keyboard(genre_index)
        )
    
    # Случайный трек из жанра
    elif data.startswith("random_"):
        genre_index = int(data.split("_")[1])
        genre_name = list(GENRES.keys())[genre_index]
        search_query = GENRES[genre_name][0]
        
        await query.edit_message_text(f"🔍 Ищу музыку в жанре {genre_name}...")
        
        results = search_youtube(search_query, max_results=5)
        if results:
            await query.edit_message_text(
                f"*{genre_name}*\n\nВыбери трек:",
                parse_mode='Markdown',
                reply_markup=search_results_keyboard(results, genre_name)
            )
        else:
            await query.edit_message_text(
                "❌ Ничего не найдено. Попробуй другой жанр.",
                reply_markup=main_menu_keyboard()
            )
    
    # Поиск
    elif data == "search":
        await query.edit_message_text(
            "🔍 *Поиск музыки*\n\n"
            "Отправь мне название песни или исполнителя:",
            parse_mode='Markdown'
        )
        context.user_data['awaiting_search'] = True
    
    # Воспроизведение трека
    elif data.startswith("play_"):
        video_id = data.split("_", 1)[1]
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Проверяем кэш
        cached = get_cached_track(youtube_url)
        
        if cached:
            file_id, title = cached
            await query.edit_message_text(f"🎵 Отправляю: *{title}*", parse_mode='Markdown')
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=file_id
            )
            await query.message.reply_text(
                "Хочешь ещё музыки?",
                reply_markup=main_menu_keyboard()
            )
        else:
            await query.edit_message_text("⏳ Загружаю трек... Это может занять несколько секунд.")
            
            filename, title, duration = await download_audio(youtube_url)
            
            if filename and os.path.exists(filename):
                try:
                    with open(filename, 'rb') as audio:
                        message = await context.bot.send_audio(
                            chat_id=query.message.chat_id,
                            audio=audio,
                            title=title,
                            duration=duration
                        )
                        
                        # Сохраняем file_id в кэш
                        file_id = message.audio.file_id
                        save_to_cache(title, youtube_url, file_id, "Unknown", duration)
                    
                    # Удаляем файл после отправки
                    os.remove(filename)
                    
                    await query.edit_message_text(
                        f"✅ *{title}*\n\nОтправлено!",
                        parse_mode='Markdown'
                    )
                    await query.message.reply_text(
                        "Хочешь ещё музыки?",
                        reply_markup=main_menu_keyboard()
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки файла: {e}")
                    if os.path.exists(filename):
                        os.remove(filename)
                    await query.edit_message_text(
                        "❌ Не удалось отправить трек. Попробуй другой.",
                        reply_markup=main_menu_keyboard()
                    )
            else:
                await query.edit_message_text(
                    "❌ Не удалось загрузить трек. Попробуй другой.",
                    reply_markup=main_menu_keyboard()
                )

# Обработка текстовых сообщений (поиск)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_search'):
        search_query = update.message.text
        context.user_data['awaiting_search'] = False
        
        msg = await update.message.reply_text(f"🔍 Ищу: *{search_query}*...", parse_mode='Markdown')
        
        results = search_youtube(search_query, max_results=5)
        
        if results:
            await msg.edit_text(
                f"*Результаты поиска:*\n\n`{search_query}`",
                parse_mode='Markdown',
                reply_markup=search_results_keyboard(results)
            )
        else:
            await msg.edit_text(
                "❌ Ничего не найдено. Попробуй изменить запрос.",
                reply_markup=main_menu_keyboard()
            )

# Главная функция
def main():
    init_db()
    
    # Проверка наличия токена
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Не указан BOT_TOKEN! Установи переменную окружения BOT_TOKEN")
        return
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    logger.info("🚀 Бот запущен на Render!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 
