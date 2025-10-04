"""
Обработчики для команд и сообщений Telegram-бота.
"""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.settings import settings

# Создаем роутер для обработчиков. Аналог Blueprint во Flask или APIRouter в FastAPI.
router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Этот обработчик срабатывает на команду /start.
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Начать тренировку",
        web_app=WebAppInfo(url=settings.WEB_APP_URL),
    )
    await message.answer(
        "Добро пожаловать в KinetiCoach! Нажмите кнопку ниже, чтобы начать.",
        reply_markup=builder.as_markup(),
    )
