"""Модуль для генерации голосовых подсказок через OpenAI TTS API."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from app.settings import settings
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Инициализация клиента OpenAI
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Директория для временного хранения аудио
AUDIO_DIR = Path(__file__).parent.parent.parent.parent / "audio_cache"
AUDIO_DIR.mkdir(exist_ok=True)

# Маппинг ошибок на русский текст
FEEDBACK_TEXT_MAP: Dict[str, str] = {
    # Приседания
    "GOOD_REP": "Отлично! Повтор засчитан.",
    "BEND_FORWARD": "Не наклоняйтесь вперёд. Держите спину прямо.",
    "BEND_BACKWARDS": "Не отклоняйтесь назад. Корпус должен быть вертикальным.",
    "LOWER_YOUR_HIPS": "Опускайтесь ниже. Бёдра должны быть параллельны полу.",
    "SQUAT_TOO_DEEP": (
        "Не приседайте слишком глубоко. Колени не должны выходить за носки."
    ),
    "KNEE_OVER_TOE": "Колено выходит за носок. Откорректируйте положение.",
    # Кошка-Корова
    "GOOD_TRANSITION": "Отличный переход! Продолжайте в том же темпе.",
    "SPINE_NOT_ARCHED": (
        "Недостаточный прогиб спины в позе кошки. Округлите спину сильнее."
    ),
    "SPINE_NOT_EXTENDED": (
        "Недостаточное разгибание спины в позе коровы. Прогнитесь глубже."
    ),
    "HEAD_NOT_LIFTED": "Поднимите голову выше в позе коровы.",
    "HEAD_NOT_LOWERED": "Опустите голову ниже в позе кошки.",
}


async def generate_voice_feedback(feedback_codes: List[str]) -> Optional[str]:
    """Генерирует аудио файл с голосовой подсказкой.

    Args:
        feedback_codes: Список кодов ошибок (например,
            ["BEND_FORWARD", "KNEE_OVER_TOE"]).

    Returns:
        Путь к сгенерированному аудио файлу или None при ошибке.
    """
    if not feedback_codes:
        return None

    # Берём только первую ошибку для простоты (можно расширить)
    feedback_code = feedback_codes[0]
    text = FEEDBACK_TEXT_MAP.get(feedback_code, "Скорректируйте технику.")

    # Сохранение аудио файла
    audio_filename = f"{feedback_code}.mp3"
    audio_path = AUDIO_DIR / audio_filename

    # Кэширование: если файл уже существует, не генерируем заново
    if audio_path.exists():
        return str(audio_path)

    try:
        # Генерация аудио через OpenAI TTS
        response = await client.audio.speech.create(
            model="tts-1",  # tts-1-hd для высокого качества
            voice="alloy",  # Голос на русском: alloy, echo, fable, onyx, nova, shimmer
            input=text,
            speed=1.0,  # Скорость речи (0.25 - 4.0)
        )

        audio_path.write_bytes(response.content)
        logger.info(f"Generated TTS audio: {audio_filename}")

        return str(audio_path)

    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        return None
