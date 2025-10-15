from aiogram import executor
from loader import dp
import handlers.upload  # подключаем обработчик загрузки треков

async def on_startup(dp):
    print("Бот запущен и готов к работе!")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
