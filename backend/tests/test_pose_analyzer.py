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


# --- ФИНАЛЬНЫЕ, СКОНСТРУИРОВАННЫЕ ТЕСТОВЫЕ ДАННЫЕ ---

# Состояние: Стойка (UP). Угол в колене > 170°.
LANDMARKS_UP = [MockLandmark(0, 0)] * 33
LANDMARKS_UP[11] = MockLandmark(0.6, 1.0)  # Плечо
LANDMARKS_UP[12] = MockLandmark(0.7, 1.0)
LANDMARKS_UP[23] = MockLandmark(0.5, 2.0)  # Бедро
LANDMARKS_UP[25] = MockLandmark(0.5, 3.0)  # Колено
LANDMARKS_UP[27] = MockLandmark(0.5, 4.0)  # Лодыжка
LANDMARKS_UP[31] = MockLandmark(0.5, 5.0)  # Стопа

# Состояние: Идеальный присед (DOWN). Угол в колене ~90°.
LANDMARKS_DOWN_GOOD = [MockLandmark(0, 0)] * 33
LANDMARKS_DOWN_GOOD[11] = MockLandmark(0.5, 1.0)
LANDMARKS_DOWN_GOOD[12] = MockLandmark(0.6, 1.0)
LANDMARKS_DOWN_GOOD[23] = MockLandmark(0.5, 2.0)
LANDMARKS_DOWN_GOOD[25] = MockLandmark(1.0, 2.0)
LANDMARKS_DOWN_GOOD[27] = MockLandmark(1.0, 3.0)
LANDMARKS_DOWN_GOOD[31] = MockLandmark(1.0, 4.0)

# Ошибка: Наклон вперед. Плечо находится прямо перед коленом.
LANDMARKS_DOWN_BEND_FORWARD = [MockLandmark(0, 0)] * 33
LANDMARKS_DOWN_BEND_FORWARD[11] = MockLandmark(1.0, 2.0)
LANDMARKS_DOWN_BEND_FORWARD[12] = MockLandmark(1.1, 2.0)
LANDMARKS_DOWN_BEND_FORWARD[23] = MockLandmark(0.5, 2.0)
LANDMARKS_DOWN_BEND_FORWARD[25] = MockLandmark(1.0, 2.0)
LANDMARKS_DOWN_BEND_FORWARD[27] = MockLandmark(1.0, 3.0)
LANDMARKS_DOWN_BEND_FORWARD[31] = MockLandmark(1.0, 4.0)

# Ошибка: Недостаточная глубина. Угол в колене ~135°, что > 110°.
LANDMARKS_DOWN_SHALLOW = [MockLandmark(0, 0)] * 33
LANDMARKS_DOWN_SHALLOW[11] = MockLandmark(0.5, 1.0)
LANDMARKS_DOWN_SHALLOW[12] = MockLandmark(0.6, 1.0)
LANDMARKS_DOWN_SHALLOW[23] = MockLandmark(0.5, 2.0)
LANDMARKS_DOWN_SHALLOW[25] = MockLandmark(1.0, 2.5)
LANDMARKS_DOWN_SHALLOW[27] = MockLandmark(1.0, 3.5)
LANDMARKS_DOWN_SHALLOW[31] = MockLandmark(1.0, 4.5)

# Ошибка: Избыточная глубина. Угол в колене ~45°, что < 75°.
LANDMARKS_DOWN_TOO_DEEP = [MockLandmark(0, 0)] * 33
LANDMARKS_DOWN_TOO_DEEP[11] = MockLandmark(0.5, 1.0)
LANDMARKS_DOWN_TOO_DEEP[12] = MockLandmark(0.6, 1.0)
LANDMARKS_DOWN_TOO_DEEP[23] = MockLandmark(0.5, 2.5)
LANDMARKS_DOWN_TOO_DEEP[25] = MockLandmark(1.0, 2.0)
LANDMARKS_DOWN_TOO_DEEP[27] = MockLandmark(1.0, 3.0)
LANDMARKS_DOWN_TOO_DEEP[31] = MockLandmark(1.0, 4.0)

# Ошибка: Прогиб назад. Угол в бедре в верхней точке ~180°, что > 175°.
LANDMARKS_UP_BEND_BACK = [MockLandmark(0, 0)] * 33
LANDMARKS_UP_BEND_BACK[11] = MockLandmark(0.5, 1.0)
LANDMARKS_UP_BEND_BACK[12] = MockLandmark(0.6, 1.0)
LANDMARKS_UP_BEND_BACK[23] = MockLandmark(0.5, 2.0)
LANDMARKS_UP_BEND_BACK[25] = MockLandmark(0.5, 3.0)
LANDMARKS_UP_BEND_BACK[27] = MockLandmark(0.5, 4.0)
LANDMARKS_UP_BEND_BACK[31] = MockLandmark(0.5, 5.0)

# Ошибка: Выход коленей за носки.
LANDMARKS_DOWN_KNEE_OVER_TOE = [MockLandmark(0, 0)] * 33
LANDMARKS_DOWN_KNEE_OVER_TOE[11] = MockLandmark(0.5, 1.0)
LANDMARKS_DOWN_KNEE_OVER_TOE[12] = MockLandmark(1.0, 1.0)  # Ширина плеч = 0.5
LANDMARKS_DOWN_KNEE_OVER_TOE[23] = MockLandmark(0.5, 2.0)
LANDMARKS_DOWN_KNEE_OVER_TOE[25] = MockLandmark(1.0, 3.0)  # Колено x=1.0
LANDMARKS_DOWN_KNEE_OVER_TOE[27] = MockLandmark(1.0, 4.0)
LANDMARKS_DOWN_KNEE_OVER_TOE[31] = MockLandmark(0.7, 5.0)  # Стопа x=0.7
# Разница |1.0 - 0.7| = 0.3. Порог = 0.5 * 0.45 = 0.225. 0.3 > 0.225 -> ошибка


@pytest.fixture
def patched_analyzer() -> Iterator[Tuple[PoseAnalyzer, MagicMock]]:
    """Фикстура, которая создает анализатор с "замоканным" PoseProcessor."""
    with patch("app.analysis.pose_analyzer.PoseProcessor") as mock_processor_class:
        mock_processor_instance = MagicMock()
        mock_processor_class.return_value = mock_processor_instance
        analyzer = PoseAnalyzer()
        yield analyzer, mock_processor_instance


def test_good_rep_scenario(patched_analyzer: Tuple[PoseAnalyzer, MagicMock]) -> None:
    """Тестирует сценарий идеального повторения."""
    analyzer, mock_processor = patched_analyzer

    # 1. Атлет стоит прямо
    mock_processor.get_landmarks.return_value = LANDMARKS_UP
    analyzer.process_frame({"frame": VALID_B64_FRAME})
    assert analyzer.state == "UP"

    # 2. Опускается вниз (идеальный присед)
    mock_processor.get_landmarks.return_value = LANDMARKS_DOWN_GOOD
    analyzer.process_frame({"frame": VALID_B64_FRAME})
    assert analyzer.state == "DOWN"

    # 3. Встаёт обратно
    mock_processor.get_landmarks.return_value = LANDMARKS_UP
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})

    assert result.payload["rep_count"] == 1
    assert "GOOD_REP" in result.payload["feedback"]
    assert len(result.payload["feedback"]) == 1


def test_bend_forward_error_scenario(
    patched_analyzer: Tuple[PoseAnalyzer, MagicMock],
) -> None:
    """Тестирует ошибку: сильный наклон корпуса вперед."""
    analyzer, mock_processor = patched_analyzer

    mock_processor.get_landmarks.return_value = LANDMARKS_DOWN_BEND_FORWARD
    analyzer.process_frame({"frame": VALID_B64_FRAME})
    mock_processor.get_landmarks.return_value = LANDMARKS_UP
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})

    assert result.payload["rep_count"] == 1
    assert "BEND_FORWARD" in result.payload["feedback"]
    assert "GOOD_REP" not in result.payload["feedback"]


def test_lower_your_hips_error_scenario(
    patched_analyzer: Tuple[PoseAnalyzer, MagicMock],
) -> None:
    """Тестирует ошибку: недостаточная глубина приседа."""
    analyzer, mock_processor = patched_analyzer

    mock_processor.get_landmarks.return_value = LANDMARKS_DOWN_SHALLOW
    analyzer.process_frame({"frame": VALID_B64_FRAME})
    mock_processor.get_landmarks.return_value = LANDMARKS_UP
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})

    assert result.payload["rep_count"] == 1
    assert "LOWER_YOUR_HIPS" in result.payload["feedback"]


def test_squat_too_deep_error_scenario(
    patched_analyzer: Tuple[PoseAnalyzer, MagicMock],
) -> None:
    """Тестирует ошибку: избыточная глубина приседа."""
    analyzer, mock_processor = patched_analyzer

    mock_processor.get_landmarks.return_value = LANDMARKS_DOWN_TOO_DEEP
    analyzer.process_frame({"frame": VALID_B64_FRAME})
    mock_processor.get_landmarks.return_value = LANDMARKS_UP
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})

    assert result.payload["rep_count"] == 1
    assert "SQUAT_TOO_DEEP" in result.payload["feedback"]


def test_bend_backwards_error_scenario(
    patched_analyzer: Tuple[PoseAnalyzer, MagicMock],
) -> None:
    """Тестирует ошибку: прогиб назад в верхней точке."""
    analyzer, mock_processor = patched_analyzer

    mock_processor.get_landmarks.return_value = LANDMARKS_DOWN_GOOD
    analyzer.process_frame({"frame": VALID_B64_FRAME})
    # Встаем в позу с избыточным прогибом
    mock_processor.get_landmarks.return_value = LANDMARKS_UP_BEND_BACK
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})

    assert result.payload["rep_count"] == 1
    assert "BEND_BACKWARDS" in result.payload["feedback"]


def test_knee_over_toe_error_scenario(
    patched_analyzer: Tuple[PoseAnalyzer, MagicMock],
) -> None:
    """Тестирует ошибку: выход коленей за носки."""
    analyzer, mock_processor = patched_analyzer

    mock_processor.get_landmarks.return_value = LANDMARKS_DOWN_KNEE_OVER_TOE
    analyzer.process_frame({"frame": VALID_B64_FRAME})
    mock_processor.get_landmarks.return_value = LANDMARKS_UP
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})

    assert result.payload["rep_count"] == 1
    assert "KNEE_OVER_TOE" in result.payload["feedback"]


def test_multiple_errors_scenario(
    patched_analyzer: Tuple[PoseAnalyzer, MagicMock],
) -> None:
    """Тестирует случай, когда в одном повторении несколько ошибок."""
    analyzer, mock_processor = patched_analyzer

    # Приседаем слишком глубоко и с наклоном вперед
    mock_processor.get_landmarks.side_effect = [
        LANDMARKS_DOWN_BEND_FORWARD,
        LANDMARKS_DOWN_TOO_DEEP,
        LANDMARKS_UP,
    ]
    analyzer.process_frame({"frame": VALID_B64_FRAME})  # Наклон
    analyzer.process_frame({"frame": VALID_B64_FRAME})  # Слишком глубоко
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})  # Встаем

    assert result.payload["rep_count"] == 1
    feedback = result.payload["feedback"]
    assert "BEND_FORWARD" in feedback
    assert "SQUAT_TOO_DEEP" in feedback
    assert "GOOD_REP" not in feedback


def test_no_landmarks_detected(
    patched_analyzer: Tuple[PoseAnalyzer, MagicMock],
) -> None:
    """Тестирует случай, когда PoseProcessor не находит ключевых точек."""
    analyzer, mock_processor = patched_analyzer
    mock_processor.get_landmarks.return_value = None
    result = analyzer.process_frame({"frame": VALID_B64_FRAME})
    assert result.payload["has_landmarks"] is False
    assert result.payload["rep_count"] == 0


def test_invalid_b64_frame(patched_analyzer: Tuple[PoseAnalyzer, MagicMock]) -> None:
    """Тестирует отправку некорректного base64-кадра."""
    analyzer, _ = patched_analyzer
    result = analyzer.process_frame({"frame": "this-is-not-base64"})
    assert result.type == "ERROR"
    assert "message" in result.payload
