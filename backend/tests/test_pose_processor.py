"""Тесты для модуля-обертки над MediaPipe."""

from typing import Iterator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from app.analysis.pose_processor import PoseProcessor


class MockLandmark:
    """Класс-заглушка для имитации объекта NormalizedLandmark."""

    def __init__(self, visibility: float = 1.0) -> None:
        self.x = 0.5
        self.y = 0.5
        self.z = 0.5
        self.visibility = visibility


class MockDetectionResult:
    """Класс-заглушка для имитации результата детекции MediaPipe."""

    def __init__(self, landmarks: list[list[MockLandmark]] | None = None) -> None:
        self.pose_landmarks = landmarks


@pytest.fixture
def mock_mediapipe() -> Iterator[MagicMock]:
    """Фикстура для мокинга модуля MediaPipe."""
    # Создаем мок для класса PoseLandmarker
    mock_landmarker = MagicMock()

    # Мокаем статический метод create_from_options, чтобы он возвращал наш мок
    with patch(
        "mediapipe.tasks.python.vision.PoseLandmarker.create_from_options",
        return_value=mock_landmarker,
    ):
        yield mock_landmarker


def test_get_landmarks_success(mock_mediapipe: MagicMock) -> None:
    """
    Тест: get_landmarks успешно возвращает точки, когда они обнаружены.
    """
    # Arrange: Настраиваем мок, чтобы он возвращал результат с точками
    mock_landmarks = [[MockLandmark(visibility=0.9)]]
    mock_mediapipe.detect.return_value = MockDetectionResult(landmarks=mock_landmarks)

    processor = PoseProcessor()
    blank_frame = np.zeros((100, 100, 3), dtype=np.uint8)

    # Act: Вызываем тестируемый метод
    result = processor.get_landmarks(blank_frame)

    # Assert: Проверяем, что результат соответствует ожиданиям
    assert result is not None
    assert len(result) > 0
    assert result[0].visibility == pytest.approx(0.9)
    mock_mediapipe.detect.assert_called_once()


def test_get_landmarks_no_pose_detected(mock_mediapipe: MagicMock) -> None:
    """
    Тест: get_landmarks возвращает None, когда поза не обнаружена.
    """
    # Arrange: Настраиваем мок, чтобы он возвращал пустой результат
    mock_mediapipe.detect.return_value = MockDetectionResult(landmarks=None)

    processor = PoseProcessor()
    blank_frame = np.zeros((100, 100, 3), dtype=np.uint8)

    # Act: Вызываем тестируемый метод
    result = processor.get_landmarks(blank_frame)

    # Assert: Проверяем, что результат - None
    assert result is None
    mock_mediapipe.detect.assert_called_once()


def test_get_landmarks_low_visibility(mock_mediapipe: MagicMock) -> None:
    """
    Тест: get_landmarks возвращает точки даже с низкой видимостью.
    (Проверка видимости - ответственность PoseAnalyzer).
    """
    # Arrange: Настраиваем мок, чтобы он возвращал точки с низкой видимостью
    mock_landmarks = [[MockLandmark(visibility=0.2)]]
    mock_mediapipe.detect.return_value = MockDetectionResult(landmarks=mock_landmarks)

    processor = PoseProcessor()
    blank_frame = np.zeros((100, 100, 3), dtype=np.uint8)

    # Act: Вызываем тестируемый метод
    result = processor.get_landmarks(blank_frame)

    # Assert: Проверяем, что точки все равно вернулись
    assert result is not None
    assert result[0].visibility == pytest.approx(0.2)
