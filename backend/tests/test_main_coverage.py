"""Интеграционные тесты для покрытия main.py."""

from unittest.mock import AsyncMock, patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check() -> None:
    """Тест эндпоинта /health."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_websocket_unknown_exercise_type() -> None:
    """Тест START_SESSION с неизвестным типом упражнения."""
    with client.websocket_connect("/ws/analysis") as websocket:
        websocket.send_json(
            {"type": "START_SESSION", "payload": {"exerciseType": "unknown_type"}}
        )
        response = websocket.receive_json()
        assert response["type"] == "ERROR"
        assert "Unknown exercise type" in response["payload"]["message"]


def test_websocket_posedata_without_session() -> None:
    """Тест отправки POSEDATA без старта сессии."""
    with client.websocket_connect("/ws/analysis") as websocket:
        websocket.send_json({"type": "POSEDATA", "payload": {}})
        response = websocket.receive_json()
        assert response["type"] == "ERROR"
        assert "Session not started" in response["payload"]["message"]


def test_websocket_endsession_without_session() -> None:
    """Тест отправки END_SESSION без старта сессии."""
    with client.websocket_connect("/ws/analysis") as websocket:
        websocket.send_json({"type": "END_SESSION", "payload": {}})
        response = websocket.receive_json()
        assert response["type"] == "ERROR"
        assert "No active session" in response["payload"]["message"]


def test_websocket_cat_cow_session() -> None:
    """Тест сессии Cat-Cow."""
    with client.websocket_connect("/ws/analysis") as websocket:
        # Start Session
        websocket.send_json(
            {"type": "START_SESSION", "payload": {"exerciseType": "cat-cow"}}
        )
        response = websocket.receive_json()
        assert response["type"] == "INFO"
        assert "started for cat-cow" in response["payload"]["message"]

        # Send Data
        websocket.send_json(
            {"type": "POSEDATA", "payload": {"spineAngle": 150.0, "headHeight": 0.1}}
        )
        response = websocket.receive_json()
        assert response["type"] == "FEEDBACK"

        # End Session
        websocket.send_json({"type": "END_SESSION", "payload": {}})
        response = websocket.receive_json()
        assert response["type"] == "REPORT"


def test_websocket_tts_integration() -> None:
    """Тест интеграции TTS в WebSocket."""
    # Мокаем generate_voice_feedback чтобы он возвращал путь
    # Patch where it is used (app.main) because it is imported at top level
    with patch("app.main.generate_voice_feedback", new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = "/path/to/audio.mp3"

        with client.websocket_connect("/ws/analysis") as websocket:
            websocket.send_json(
                {"type": "START_SESSION", "payload": {"exerciseType": "squat"}}
            )
            websocket.receive_json()  # INFO

            # Отправляем данные с ошибкой (чтобы сработал TTS)
            # 1. DOWN
            websocket.send_json(
                {"type": "POSEDATA", "payload": {"hipAngle": 100.0, "kneeAngle": 130.0}}
            )
            websocket.receive_json()

            # 2. Ошибка BEND_FORWARD
            websocket.send_json(
                {
                    "type": "POSEDATA",
                    "payload": {
                        "hipAngle": 40.0,
                        "kneeAngle": 90.0,
                        "kneeX": 0.5,
                        "footX": 0.5,
                        "shoulderWidth": 0.5,
                    },
                }
            )
            response = websocket.receive_json()

            assert response["type"] == "FEEDBACK"
            assert "audioPath" in response["payload"]
            assert response["payload"]["audioPath"] == "/path/to/audio.mp3"


def test_websocket_exception_handling() -> None:
    """Тест обработки исключений в WebSocket."""
    # Мокаем analyzer.process_frame чтобы вызвать ошибку
    with patch(
        "app.analysis.pose_analyzer.PoseAnalyzer.process_frame",
        side_effect=Exception("Unexpected Error"),
    ):
        with client.websocket_connect("/ws/analysis") as websocket:
            websocket.send_json(
                {"type": "START_SESSION", "payload": {"exerciseType": "squat"}}
            )
            websocket.receive_json()

            websocket.send_json({"type": "POSEDATA", "payload": {}})

            # Сервер должен закрыть соединение или отправить ошибку.
            # В нашем коде: await websocket.send_json({"type": "ERROR" ...})
            # внутри except Exception
            # НО! Внутри `try...except Exception` в main.py есть еще один
            # `try...except`?
            # Смотрим код main.py:
            # except Exception as e:
            #     logger.error(f"WebSocket error: {e}")
            #     try: await websocket.send_json(...) except: pass

            # Поскольку мы мокаем process_frame, исключение вылетит внутри цикла while.
            # Оно будет поймано внешним try-except.

            response = websocket.receive_json()
            assert response["type"] == "ERROR"
            assert "Internal server error" in response["payload"]["message"]
