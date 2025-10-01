"""Тесты для основного класса-анализатора поз."""

import base64
from typing import Iterator, Tuple
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from app.analysis.pose_analyzer import PoseAnalyzer


def create_blank_image_b64(width: int, height: int) -> str:
    """Создает черное изображение и кодирует его в base64."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", frame)
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


VALID_B64_FRAME = create_blank_image_b64(100, 100)


class MockLandmark:
    """
    Класс-заглушка для имитации объекта NormalizedLandmark из MediaPipe
    в целях тестирования.
    """

    def __init__(
        self, x: float, y: float, z: float = 0.0, visibility: float = 1.0
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility


# --- Тестовые данные: имитация координат для разных поз ---
LANDMARKS_UP = [MockLandmark(0, 0)] * 33
LANDMARKS_UP[11] = MockLandmark(0.5, 1)
LANDMARKS_UP[12] = MockLandmark(0.6, 1)
LANDMARKS_UP[23] = MockLandmark(0.5, 2)
LANDMARKS_UP[25] = MockLandmark(0.5, 3)
LANDMARKS_UP[27] = MockLandmark(0.5, 4)
LANDMARKS_UP[31] = MockLandmark(0.5, 5)

LANDMARKS_DOWN_GOOD = [MockLandmark(0, 0)] * 33
LANDMARKS_DOWN_GOOD[11] = MockLandmark(0.5, 1)
LANDMARKS_DOWN_GOOD[12] = MockLandmark(0.6, 1)
LANDMARKS_DOWN_GOOD[23] = MockLandmark(0.5, 2)
LANDMARKS_DOWN_GOOD[25] = MockLandmark(1.0, 2)
LANDMARKS_DOWN_GOOD[27] = MockLandmark(1.0, 3)
LANDMARKS_DOWN_GOOD[31] = MockLandmark(1.0, 4)

LANDMARKS_DOWN_BEND_FORWARD = [MockLandmark(0, 0)] * 33
LANDMARKS_DOWN_BEND_FORWARD[11] = MockLandmark(1.5, 1.8)
LANDMARKS_DOWN_BEND_FORWARD[12] = MockLandmark(1.6, 1.8)
LANDMARKS_DOWN_BEND_FORWARD[23] = MockLandmark(0.5, 2)
LANDMARKS_DOWN_BEND_FORWARD[25] = MockLandmark(1.0, 2)
LANDMARKS_DOWN_BEND_FORWARD[27] = MockLandmark(1.0, 3)
LANDMARKS_DOWN_BEND_FORWARD[31] = MockLandmark(1.0, 4)


@pytest.fixture
def patched_analyzer() -> Iterator[Tuple[PoseAnalyzer, MagicMock]]:
    with patch("app.analysis.pose_analyzer.PoseProcessor") as mock_processor_class:
        mock_processor_instance = MagicMock()
        mock_processor_class.return_value = mock_processor_instance
        analyzer = PoseAnalyzer()
        yield analyzer, mock_processor_instance


def test_good_rep_scenario(patched_analyzer: Tuple[PoseAnalyzer, MagicMock]) -> None:
    analyzer, mock_processor = patched_analyzer

    mock_processor.get_landmarks.return_value = LANDMARKS_UP
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})
    assert result.payload["state"] == "UP"
    assert result.payload["rep_count"] == 0

    mock_processor.get_landmarks.return_value = LANDMARKS_DOWN_GOOD
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})
    assert result.payload["state"] == "DOWN"
    assert not result.payload["feedback"]

    mock_processor.get_landmarks.return_value = LANDMARKS_UP
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})
    assert result.payload["state"] == "UP"
    assert result.payload["rep_count"] == 1
    assert "GOOD_REP" in result.payload["feedback"]


def test_bend_forward_error_scenario(
    patched_analyzer: Tuple[PoseAnalyzer, MagicMock],
) -> None:
    analyzer, mock_processor = patched_analyzer

    mock_processor.get_landmarks.return_value = LANDMARKS_DOWN_BEND_FORWARD
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})
    assert result.payload["state"] == "DOWN"

    mock_processor.get_landmarks.return_value = LANDMARKS_UP
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})
    assert result.payload["rep_count"] == 1
    assert "BEND_FORWARD" in result.payload["feedback"]
    assert "GOOD_REP" not in result.payload["feedback"]


def test_no_landmarks_detected(
    patched_analyzer: Tuple[PoseAnalyzer, MagicMock],
) -> None:
    analyzer, mock_processor = patched_analyzer
    mock_processor.get_landmarks.return_value = None

    result = analyzer.process_frame({"frame": VALID_B64_FRAME})
    assert result.payload["has_landmarks"] is False
    assert result.payload["rep_count"] == 0


def test_invalid_b64_frame(patched_analyzer: Tuple[PoseAnalyzer, MagicMock]) -> None:
    analyzer, _ = patched_analyzer
    result = analyzer.process_frame({"frame": "this-is-not-base64"})
    assert result.type == "ERROR"
    assert "message" in result.payload
