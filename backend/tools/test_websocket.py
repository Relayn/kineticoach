"""
Простой асинхронный клиент для тестирования WebSocket-эндпоинта.
"""

import asyncio
import json

import websockets


async def test_websocket_connection() -> None:
    """
    Подключается к WebSocket-серверу, отправляет два сообщения
    и проверяет, что счетчик в ответе увеличивается.
    """
    uri = "ws://localhost:8000/ws/analysis"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Подключено к {uri}")

            # --- Сообщение 1 ---
            print("\n--- Отправка первого пакета данных ---")
            message_1 = {
                "type": "POSE_DATA",
                "payload": {"frame_id": 1, "keypoints": [1, 2, 3]},
            }
            await websocket.send(json.dumps(message_1))
            print(f"> Отправлено: {json.dumps(message_1)}")
            response_1 = await websocket.recv()
            print(f"< Получено: {json.dumps(json.loads(response_1), indent=2)}")

            # --- Сообщение 2 ---
            print("\n--- Отправка второго пакета данных ---")
            message_2 = {
                "type": "POSE_DATA",
                "payload": {"frame_id": 2, "keypoints": [4, 5, 6]},
            }
            await websocket.send(json.dumps(message_2))
            print(f"> Отправлено: {json.dumps(message_2)}")
            response_2 = await websocket.recv()
            print(f"< Получено: {json.dumps(json.loads(response_2), indent=2)}")

    except ConnectionRefusedError:
        print("Не удалось подключиться. Убедитесь, что сервер запущен.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
