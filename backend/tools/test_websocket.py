"""
Простой асинхронный клиент для тестирования WebSocket-эндпоинта.
"""

import asyncio
import base64
import json

import cv2
import numpy as np
import websockets


def create_blank_image_b64(width: int, height: int) -> str:
    """Создает черное изображение и кодирует его в base64."""
    # Создаем черный кадр (3 канала BGR)
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # Кодируем в JPEG формат
    _, buffer = cv2.imencode(".jpg", frame)
    # Кодируем в base64
    b64_string = base64.b64encode(buffer.tobytes()).decode("utf-8")
    return b64_string


async def test_websocket_connection() -> None:
    """
    Подключается к WebSocket-серверу, отправляет два сообщения
    с закодированными изображениями и проверяет ответ.
    """
    uri = "ws://localhost:8000/ws/analysis"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Подключено к {uri}")

            # Создаем фейковый кадр
            b64_frame = create_blank_image_b64(640, 480)

            # --- Сообщение 1 ---
            print("\n--- Отправка первого кадра ---")
            message_1 = {
                "type": "POSE_DATA",
                "payload": {"frame": b64_frame},
            }
            await websocket.send(json.dumps(message_1))
            print(f"> Отправлено сообщение типа: {message_1['type']}")
            response_1 = await websocket.recv()
            print(f"< Получено: {json.dumps(json.loads(response_1), indent=2)}")

            # --- Сообщение 2 ---
            print("\n--- Отправка второго кадра ---")
            message_2 = {
                "type": "POSE_DATA",
                "payload": {"frame": b64_frame},
            }
            await websocket.send(json.dumps(message_2))
            print(f"> Отправлено сообщение типа: {message_2['type']}")
            response_2 = await websocket.recv()
            print(f"< Получено: {json.dumps(json.loads(response_2), indent=2)}")

    except ConnectionRefusedError:
        print("Не удалось подключиться. Убедитесь, что сервер запущен.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
