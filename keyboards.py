from aiogram import types

KB_LANG = types.ReplyKeyboardMarkup(resize_keyboard=True)
KB_LANG.add(types.KeyboardButton("Русский"), types.KeyboardButton("English"))

KB_MENU_RU = types.ReplyKeyboardMarkup(resize_keyboard=True)
KB_MENU_RU.add(types.KeyboardButton("Слушать музыку"))
KB_MENU_RU.add(types.KeyboardButton("Загрузить свой трек"))

KB_MENU_EN = types.ReplyKeyboardMarkup(resize_keyboard=True)
KB_MENU_EN.add(types.KeyboardButton("Listen music"))
KB_MENU_EN.add(types.KeyboardButton("Upload your track"))

genres = ["LoFi", "Trap", "Techno", "Rock", "Pop", "Jazz", "HipHop", "Chill", "Metal", "Other"]

KB_GENRES = types.ReplyKeyboardMarkup(resize_keyboard=True)
for g in genres:
    KB_GENRES.add(types.KeyboardButton(g))
