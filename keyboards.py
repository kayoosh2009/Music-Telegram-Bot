from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang:ru")],
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang:en")],
    ])

def main_kb(name: str, lang: str):
    if lang == "en":
        listen = "🎧 Listen music"
        suggest = "💡 Suggest song"
        title = f"What to listen today, {name}?"
    else:
        listen = "🎧 Послушать музыку"
        suggest = "💡 Предложить песню"
        title = f"Что слушаем сегодня, {name}?"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=title, callback_data="menu:none")],
        [
            InlineKeyboardButton(text=listen, callback_data="menu:listen"),
            InlineKeyboardButton(text=suggest, callback_data="menu:suggest")
        ]
    ])

def genres_kb():
    genres = ["LOFI", "POP", "ROCK", "RAP", "ELECTRONIC", "OTHER"]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=g, callback_data=f"genre:{g}")] for g in genres
        ]
    )

def playback_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏭️ Next", callback_data="play:next"),
            InlineKeyboardButton(text="🏠 Menu", callback_data="menu:main")
        ]
    ])
