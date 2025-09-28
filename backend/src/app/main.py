"""
Основной файл приложения FastAPI для KinetiCoach.
Определяет точки входа API и основную конфигурацию.
"""

import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .analysis.pose_analyzer import PoseAnalyzer
from .schemas import ClientMessage, ServerMessage

# Настраиваем базовый логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KinetiCoach API",
    description="API для анализа техники приседаний в реальном времени.",
    version="0.1.0",
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
                    # Передаем данные в анализатор и получаем ответ
                    response_msg = analyzer.process_data(client_msg.payload)
                else:
                    # Обрабатываем другие типы сообщений, если они появятся
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
