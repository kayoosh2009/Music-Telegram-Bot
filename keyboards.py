from aiogram import types
from config import GENRES
from aiogram.utils.keyboard import InlineKeyboardBuilder

KB_LANG = types.ReplyKeyboardMarkup(resize_keyboard=True)
KB_LANG.add(types.KeyboardButton("Русский"), types.KeyboardButton("English"))

KB_MENU_RU = types.ReplyKeyboardMarkup(resize_keyboard=True)
KB_MENU_RU.add(types.KeyboardButton("🎧 Слушать музыку"))
KB_MENU_RU.add(types.KeyboardButton("⬆️ Загрузить свой трек"))

KB_MENU_EN = types.ReplyKeyboardMarkup(resize_keyboard=True)
KB_MENU_EN.add(types.KeyboardButton("🎧 Listen music"))
KB_MENU_EN.add(types.KeyboardButton("⬆️ Upload your track"))

def genres_keyboard(lang: str = "ru") -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for g in GENRES:
        kb.insert(types.KeyboardButton(g))
    if lang == "ru":
        kb.add(types.KeyboardButton("🔙 Назад"))
        kb.add(types.KeyboardButton("🏠 В меню"))
    else:
        kb.add(types.KeyboardButton("🔙 Back"))
        kb.add(types.KeyboardButton("🏠 Menu"))
    return kb

def player_inline_kb(current_index: int, total: int, lang: str = "ru"):
    kb = InlineKeyboardBuilder()
    back_text = "◀️ Назад" if lang == "ru" else "◀️ Prev"
    save_text = "💾 Сохранить" if lang == "ru" else "💾 Save"
    next_text = "Вперёд ▶️" if lang == "ru" else "Next ▶️"
    menu_text = "🏠 В меню" if lang == "ru" else "🏠 Menu"

    kb.row(
        types.InlineKeyboardButton(text=back_text, callback_data=f"player_prev:{current_index}"),
        types.InlineKeyboardButton(text=save_text, callback_data=f"player_save:{current_index}"),
        types.InlineKeyboardButton(text=next_text, callback_data=f"player_next:{current_index}"),
    )
    kb.row(types.InlineKeyboardButton(text=menu_text, callback_data="player_menu"))
    return kb.as_markup()
