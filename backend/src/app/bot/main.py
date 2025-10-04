"""
Основной модуль для инициализации и управления Telegram-ботом.
"""

import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.bot.handlers import router
from app.settings import settings

logger = logging.getLogger(__name__)

# Инициализируем бота и диспетчер
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def start_bot() -> None:
    """Запускает процесс поллинга для бота."""
    # Регистрируем наши обработчики
    dp.include_router(router)
    logger.info("Starting Telegram bot...")
    # Удаляем вебхук, если он был установлен ранее, чтобы избежать конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем получение обновлений
    await dp.start_polling(bot)
    logger.info("Telegram bot started.")


async def stop_bot() -> None:
    """Останавливает бота."""
    logger.info("Stopping Telegram bot...")
    await dp.storage.close()
    await bot.session.close()
    logger.info("Telegram bot stopped.")
