import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import start, menu, random_song, genres, suggest

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()

    # Регистрируем все роутеры
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(random_song.router)
    dp.include_router(genres.router)
    dp.include_router(suggest.router)

    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
