from aiogram import types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from keyboards import KB_LANG, KB_MENU_RU, KB_MENU_EN
from texts import TEXTS, TEXTS_EN
from firebase_utils import init_user_messages_list

async def start_handler(message: types.Message, state: FSMContext):
    init_user_messages_list(message.from_user.id)
    kb = KB_LANG
    await message.answer(TEXTS["start_ru"], reply_markup=kb)

async def language_choice_handler(message: types.Message, state: FSMContext):
    txt = message.text.strip().lower()
    if txt == "русский":
        await state.update_data(lang="ru")
        await message.answer(TEXTS["menu_prompt_ru"], reply_markup=KB_MENU_RU)
    elif txt == "english":
        await state.update_data(lang="en")
        await message.answer(TEXTS_EN["menu_prompt_en"], reply_markup=KB_MENU_EN)
    else:
        # ignore
        return
