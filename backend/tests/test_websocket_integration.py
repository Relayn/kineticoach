"""Интеграционные тесты для WebSocket-эндпоинта (Client-Side logic)."""

from typing import Iterator

import pytest
from app.main import app
from starlette.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Фикстура, создающая тестовый клиент для FastAPI-приложения."""
    with TestClient(app) as client:
        yield client


def test_good_rep_integration_scenario(client: TestClient) -> None:
    """
    Тестирует полный цикл: подключение, выполнение одного правильного
    повторения, получение отчета и отключение.
    """
    with client.websocket_connect("/ws/analysis") as websocket:
        # 0. Start Session
        websocket.send_json(
            {"type": "START_SESSION", "payload": {"exerciseType": "squat"}}
        )
        response = websocket.receive_json()
        assert response["type"] == "INFO"
        assert "started" in response["payload"]["message"]

        # 1. UP
        websocket.send_json(
            {
                "type": "POSE_DATA",
                "payload": {
                    "hipAngle": 170.0,
                    "kneeAngle": 175.0,
                    "kneeX": 0.5,
                    "footX": 0.5,
                    "shoulderWidth": 0.5,
                },
            }
        )
        response = websocket.receive_json()
        assert response["type"] == "FEEDBACK"
        assert response["payload"]["state"] == "UP"

        # 2. DOWN
        websocket.send_json(
            {
                "type": "POSE_DATA",
                "payload": {
                    "hipAngle": 90.0,
                    "kneeAngle": 90.0,
                    "kneeX": 0.5,
                    "footX": 0.5,
                    "shoulderWidth": 0.5,
                },
            }
        )
        response = websocket.receive_json()
        assert response["type"] == "FEEDBACK"
        assert response["payload"]["state"] == "DOWN"

        # 3. UP (Complete Rep)
        websocket.send_json(
            {
                "type": "POSE_DATA",
                "payload": {
                    "hipAngle": 170.0,
                    "kneeAngle": 175.0,
                    "kneeX": 0.5,
                    "footX": 0.5,
                    "shoulderWidth": 0.5,
                },
            }
        )
        response = websocket.receive_json()
        assert response["type"] == "FEEDBACK"
        assert response["payload"]["rep_count"] == 1
        assert "GOOD_REP" in response["payload"]["feedback"]

        # 4. End Session
        websocket.send_json({"type": "END_SESSION", "payload": {}})
        report = websocket.receive_json()
        assert report["type"] == "REPORT"
        assert report["payload"]["total_reps"] == 1
        assert report["payload"]["good_reps"] == 1
