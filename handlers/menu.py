from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()

def get_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎲 Рандом")],
            [KeyboardButton(text="🎧 Жанры")],
            [KeyboardButton(text="🎤 Предложить песню")]
        ],
        resize_keyboard=True
    )
    return kb

@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery):
    await callback.message.answer("🎵 Добро пожаловать в главное меню!", reply_markup=get_menu())
    await callback.answer() 
