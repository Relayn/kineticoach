"""
Основной файл приложения FastAPI для KinetiCoach.
Определяет точки входа API и основную конфигурацию.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from app.analysis.pose_analyzer import PoseAnalyzer
from app.analysis.poseanalyzer_catcow import CatCowAnalyzer
from app.analysis.tts import generate_voice_feedback
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .bot.main import start_bot, stop_bot

# Настраиваем базовый логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    Запускает и останавливает Telegram-бота вместе с FastAPI.
    """
    logger.info("FastAPI app starting up...")
    # Запускаем бота в фоновой задаче
    bot_task = asyncio.create_task(start_bot())
    yield  # Приложение работает здесь
    logger.info("FastAPI app shutting down...")
    bot_task.cancel()  # Отменяем задачу бота
    await stop_bot()


app = FastAPI(
    title="KinetiCoach API",
    description="API для анализа техники приседаний в реальном времени.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Проверяет, что сервис запущен и работает."""
    return {"status": "ok"}


async def _handle_start_session(
    websocket: WebSocket, payload: dict[str, Any]
) -> tuple[Any, Optional[str]]:
    """Обрабатывает сообщение START_SESSION."""
    exercise_type = payload.get("exerciseType")
    analyzer: Any = None

    if exercise_type == "squat":
        analyzer = PoseAnalyzer()
        logger.info("Session started: SQUAT")
    elif exercise_type == "cat-cow":
        analyzer = CatCowAnalyzer()
        logger.info("Session started: CAT-COW")
    else:
        await websocket.send_json(
            {
                "type": "ERROR",
                "payload": {"message": f"Unknown exercise type: {exercise_type}"},
            }
        )
        return None, None

    # Подтверждение старта сессии
    await websocket.send_json(
        {
            "type": "INFO",
            "payload": {"message": f"Session started for {exercise_type}"},
        }
    )
    return analyzer, exercise_type


async def _handle_pose_data(
    websocket: WebSocket, analyzer: Any, payload: dict[str, Any]
) -> None:
    """Обрабатывает данные о позе."""
    if not analyzer:
        await websocket.send_json(
            {
                "type": "ERROR",
                "payload": {
                    "message": "Session not started. Send START_SESSION first."
                },
            }
        )
        return

    result = analyzer.process_frame(payload)
    response_data = result.model_dump()

    # Генерация TTS если есть feedback
    feedback_codes = response_data.get("payload", {}).get("feedback", [])
    if feedback_codes:
        audio_path = await generate_voice_feedback(feedback_codes)
        if audio_path:
            # Преобразуем путь к файлу в URL для frontend
            # TODO: Настроить static file serving или S3
            response_data["payload"]["audioPath"] = audio_path

    await websocket.send_json(response_data)


async def _handle_end_session(
    websocket: WebSocket, analyzer: Any, exercise_type: Optional[str]
) -> None:
    """Завершает сессию и отправляет отчет."""
    if not analyzer:
        await websocket.send_json(
            {
                "type": "ERROR",
                "payload": {"message": "No active session to end."},
            }
        )
        return

    report = analyzer.generate_report()
    await websocket.send_json(report.model_dump())
    logger.info(f"Session ended for {exercise_type}")


@app.websocket("/ws/analysis")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint для real-time анализа поз.

    Поддерживает multiple типы упражнений через START_SESSION message.
    """
    await websocket.accept()

    analyzer: Any = None
    exercise_type: Optional[str] = None

    try:
        async for message in websocket.iter_json():
            msg_type = message.get("type")
            payload = message.get("payload", {})

            if msg_type == "START_SESSION":
                analyzer, exercise_type = await _handle_start_session(
                    websocket, payload
                )

            elif msg_type in ("POSEDATA", "POSE_DATA"):
                await _handle_pose_data(websocket, analyzer, payload)

            elif msg_type in ("END_SESSION", "ENDSESSION"):
                await _handle_end_session(websocket, analyzer, exercise_type)
                # Сброс для новой сессии
                analyzer = None
                exercise_type = None

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json(
                {"type": "ERROR", "payload": {"message": "Internal server error"}}
            )
        except Exception:  # nosec B110
            # Игнорируем ошибки при попытке отправить сообщение в закрытый сокет
            pass
