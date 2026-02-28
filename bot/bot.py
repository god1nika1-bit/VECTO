"""Точка входа Telegram-бота VECTO.

Запуск: cd bot && python bot.py
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TELEGRAM_BOT_TOKEN
from handlers import start, survey, report

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Подключаем роутеры (порядок важен: start → survey → report)
    dp.include_router(start.router)
    dp.include_router(survey.router)

    logger.info("Бот VECTO запущен")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
