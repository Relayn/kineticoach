"""
Основной файл приложения FastAPI для KinetiCoach.
Определяет точки входа API и основную конфигурацию.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .analysis.pose_analyzer import PoseAnalyzer
from .bot.main import start_bot, stop_bot
from .schemas import ClientMessage, ServerMessage

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


@app.websocket("/ws/analysis")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Обрабатывает WebSocket-соединения для анализа движений в реальном времени.
    """
    await websocket.accept()
    # Создаем экземпляр анализатора для этой конкретной сессии
    analyzer = PoseAnalyzer()
    logger.info("WebSocket-соединение установлено, создан экземпляр PoseAnalyzer.")

    try:
        while True:
            data = await websocket.receive_json()
            try:
                client_msg = ClientMessage.model_validate(data)
                logger.info(f"Получено валидное сообщение: {client_msg.type}")

                if client_msg.type == "POSE_DATA":
                    response_msg = analyzer.process_frame(client_msg.payload)
                elif client_msg.type == "END_SESSION":
                    logger.info(
                        "Получен запрос на завершение сессии. Генерация отчета."
                    )
                    response_msg = analyzer.generate_report()
                    await websocket.send_json(response_msg.model_dump())
                    break  # Выходим из цикла и закрываем соединение
                else:
                    response_payload = {
                        "status": "processed",
                        "original_type": client_msg.type,
                    }
                    response_msg = ServerMessage(type="INFO", payload=response_payload)

                await websocket.send_json(response_msg.model_dump())

            except ValidationError as e:
                logger.warning(f"Ошибка валидации данных от клиента: {e.errors()}")
                error_payload = {"errors": e.errors()}
                error_msg = ServerMessage(type="ERROR", payload=error_payload)
                await websocket.send_json(error_msg.model_dump())

    except WebSocketDisconnect:
        logger.info("WebSocket-соединение разорвано клиентом.")
    except Exception as e:
        logger.error(f"Произошла неперехваченная ошибка в WebSocket: {e}")
        await websocket.close(code=1011)
