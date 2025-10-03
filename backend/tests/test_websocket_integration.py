"""Интеграционные тесты для WebSocket-эндпоинта."""

from typing import Iterator
from unittest.mock import patch

import pytest
from app.main import app
from starlette.testclient import TestClient

# Импортируем моки и тестовые данные из другого файла
from .test_pose_analyzer import (
    LANDMARKS_DOWN_GOOD,
    LANDMARKS_UP,
    VALID_B64_FRAME,
)


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
    # Мокаем PoseProcessor, чтобы он возвращал предопределенные landmarks
    mock_landmarks_sequence = [
        LANDMARKS_UP,  # 1. Стоим
        LANDMARKS_DOWN_GOOD,  # 2. Приседаем
        LANDMARKS_UP,  # 3. Встаем (завершение повторения)
    ]

    with patch(
        "app.analysis.pose_analyzer.PoseProcessor.get_landmarks",
        side_effect=mock_landmarks_sequence,
    ) as mock_get_landmarks:
        with client.websocket_connect("/ws/analysis") as websocket:
            # --- Фаза 1: Выполнение повторения ---
            for i in range(len(mock_landmarks_sequence)):
                # Отправляем кадр на сервер
                websocket.send_json(
                    {"type": "POSE_DATA", "payload": {"frame": VALID_B64_FRAME}}
                )
                response = websocket.receive_json()

                # Проверяем ответ только на последнем кадре
                if i == len(mock_landmarks_sequence) - 1:
                    assert response["type"] == "FEEDBACK"
                    payload = response["payload"]
                    assert payload["rep_count"] == 1
                    assert payload["feedback"] == ["GOOD_REP"]
                    assert payload["state"] == "UP"

            # --- Фаза 2: Завершение сессии и получение отчета ---
            websocket.send_json({"type": "END_SESSION", "payload": {}})
            report_response = websocket.receive_json()

            assert report_response["type"] == "REPORT"
            report_payload = report_response["payload"]
            assert report_payload["total_reps"] == 1
            assert report_payload["good_reps"] == 1
            assert not report_payload["errors"]  # Словарь ошибок должен быть пустым

        # Проверяем, что get_landmarks был вызван нужное количество раз
        assert mock_get_landmarks.call_count == len(mock_landmarks_sequence)
