from aiogram import types

# ==========================================================
# 1️⃣ Выбор языка
# ==========================================================
KB_LANG = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [types.KeyboardButton(text="Русский")],
        [types.KeyboardButton(text="English")]
    ]
)

# ==========================================================
# 2️⃣ Главное меню (Русская версия)
# ==========================================================
KB_MENU_RU = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [types.KeyboardButton(text="🎵 Слушать музыку")],
        [types.KeyboardButton(text="⬆️ Загрузить свой трек")]
    ]
)

# ==========================================================
# 3️⃣ Главное меню (English version)
# ==========================================================
KB_MENU_EN = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [types.KeyboardButton(text="🎵 Listen to music")],
        [types.KeyboardButton(text="⬆️ Upload your track")]
    ]
)

# ==========================================================
# 4️⃣ Inline-кнопки жанров (одинаковы для RU и EN)
# ==========================================================
GENRES = [
    "LoFi", "Electronic", "Rock", "Pop", "Trap",
    "Chill", "Jazz", "Classical", "Game OST", "Other"
]

KB_GENRES = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text=genre, callback_data=f"genre_{genre}")]
        for genre in GENRES
    ]
)

# ==========================================================
# 5️⃣ Inline-кнопки плеера
# ==========================================================
KB_PLAYER_RU = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text="⏮ Назад", callback_data="prev_track"),
            types.InlineKeyboardButton(text="⭐ Сохранить", callback_data="save_track"),
            types.InlineKeyboardButton(text="⏭ Вперёд", callback_data="next_track")
        ],
        [
            types.InlineKeyboardButton(text="⬆️ В меню", callback_data="back_to_menu")
        ]
    ]
)

KB_PLAYER_EN = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text="⏮ Back", callback_data="prev_track"),
            types.InlineKeyboardButton(text="⭐ Save", callback_data="save_track"),
            types.InlineKeyboardButton(text="⏭ Next", callback_data="next_track")
        ],
        [
            types.InlineKeyboardButton(text="⬆️ Menu", callback_data="back_to_menu")
        ]
    ]
)
