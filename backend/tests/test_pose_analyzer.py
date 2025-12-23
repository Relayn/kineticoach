"""
Unit-тесты для PoseAnalyzer.
"""

from unittest.mock import patch

import pytest
from app.analysis.pose_analyzer import PoseAnalyzer


@pytest.fixture
def analyzer() -> PoseAnalyzer:
    """Фикстура, возвращающая новый экземпляр анализатора перед каждым тестом."""
    return PoseAnalyzer()


def test_good_rep_scenario(analyzer: PoseAnalyzer) -> None:
    """
    Сценарий: Пользователь делает одно идеальное повторение.
    Ожидаем: Смена состояний UP -> DOWN -> UP, счетчик = 1, Feedback = GOOD_REP.
    """
    # 1. Исходное состояние
    assert analyzer.state == "UP"
    assert analyzer.rep_counter == 0

    # 2. Начинаем опускаться (но еще не перешли порог)
    msg = analyzer.process_frame({"hipAngle": 170.0, "kneeAngle": 170.0})
    assert msg.payload["state"] == "UP"

    # 3. Переход в DOWN (угол колена < 140)
    msg = analyzer.process_frame({"hipAngle": 100.0, "kneeAngle": 130.0})
    assert msg.payload["state"] == "DOWN"

    # 4. В нижней точке (глубокий сед, все ок)
    msg = analyzer.process_frame(
        {
            "hipAngle": 80.0,
            "kneeAngle": 80.0,
            "kneeX": 0.5,
            "footX": 0.5,
            "shoulderWidth": 0.5,
        }
    )
    assert msg.payload["state"] == "DOWN"
    # Ошибок быть не должно
    assert not msg.payload["feedback"]

    # 5. Подъем обратно (переход порога вверх)
    # Порог = 170.0. Нужно > 170.
    msg = analyzer.process_frame({"hipAngle": 170.0, "kneeAngle": 175.0})
    assert msg.payload["state"] == "UP"
    assert msg.payload["rep_count"] == 1
    assert "GOOD_REP" in msg.payload["feedback"]


def test_bend_forward_error_scenario(analyzer: PoseAnalyzer) -> None:
    """
    Сценарий: Наклон корпуса вперед в нижней точке.
    """
    # Переход в DOWN
    analyzer.process_frame({"hipAngle": 100.0, "kneeAngle": 130.0})

    # Ошибка: Слишком острый угол таза (наклон вперед)
    msg = analyzer.process_frame(
        {
            "hipAngle": 40.0,  # < 75 (BODY_BEND_FORWARD_THRESHOLD)
            "kneeAngle": 90.0,
            "kneeX": 0.5,
            "footX": 0.5,
            "shoulderWidth": 0.5,
        }
    )
    assert "BEND_FORWARD" in msg.payload["feedback"]


def test_lower_your_hips_error_scenario(analyzer: PoseAnalyzer) -> None:
    """
    Сценарий: Недостаточная глубина седа.
    """
    # Переход в DOWN
    analyzer.process_frame({"hipAngle": 100.0, "kneeAngle": 130.0})

    # "Нижняя точка" недостаточно низкая (например, 100 градусов)
    # Порог MAX = 110.0. Нужно > 110.0, чтобы считалось ошибкой (недосед)?
    # Нет, rules.py: if self.min_knee_angle > rules.SQUAT_DEPTH_GOOD_MAX: error.
    # min_knee_angle обновляется в DOWN.
    # Пусть min будет 120.
    analyzer.process_frame(
        {
            "hipAngle": 100.0,
            "kneeAngle": 120.0,
            "kneeX": 0.5,
            "footX": 0.5,
            "shoulderWidth": 0.5,
        }
    )

    # Подъем > 170
    msg = analyzer.process_frame({"hipAngle": 170.0, "kneeAngle": 175.0})
    assert msg.payload["state"] == "UP"
    assert "LOWER_YOUR_HIPS" in msg.payload["feedback"]


def test_squat_too_deep_error_scenario(analyzer: PoseAnalyzer) -> None:
    """
    Сценарий: Слишком глубокий сед.
    """
    # Переход в DOWN
    analyzer.process_frame({"hipAngle": 100.0, "kneeAngle": 130.0})

    # Слишком глубоко
    analyzer.process_frame(
        {
            "hipAngle": 80.0,  # > 75, чтобы не триггерить BEND_FORWARD
            "kneeAngle": 30.0,  # < 75 (SQUAT_DEPTH_GOOD_MIN)
            "kneeX": 0.5,
            "footX": 0.5,
            "shoulderWidth": 0.5,
        }
    )

    # Подъем
    msg = analyzer.process_frame({"hipAngle": 170.0, "kneeAngle": 175.0})
    assert "SQUAT_TOO_DEEP" in msg.payload["feedback"]


def test_bend_backwards_error_scenario(analyzer: PoseAnalyzer) -> None:
    """
    Сценарий: Прогиб назад в верхней точке (в начале или конце).
    """
    # 1. DOWN
    analyzer.process_frame({"hipAngle": 100.0, "kneeAngle": 130.0})
    # 2. UP с прогибом (> 170 kneeAngle для перехода)
    # hipAngle > 175 для ошибки
    msg = analyzer.process_frame({"hipAngle": 180.0, "kneeAngle": 175.0})
    assert "BEND_BACKWARDS" in msg.payload["feedback"]


def test_knee_over_toe_error_scenario(analyzer: PoseAnalyzer) -> None:
    """
    Сценарий: Колени выходят за носки.
    """
    # Переход в DOWN
    analyzer.process_frame({"hipAngle": 100.0, "kneeAngle": 130.0})

    shoulder_width = 1.0
    # Порог = 1.0 * 0.45 = 0.45
    # Разница должна быть > 0.45
    # kneeX=0.5, footX=0.0 -> Diff=0.5 > 0.45
    msg = analyzer.process_frame(
        {
            "hipAngle": 80.0,
            "kneeAngle": 80.0,
            "kneeX": 0.5,
            "footX": 0.0,
            "shoulderWidth": shoulder_width,
        }
    )
    assert "KNEE_OVER_TOE" in msg.payload["feedback"]


def test_process_frame_missing_data(analyzer: PoseAnalyzer) -> None:
    """Тест обработки кадра с отсутствующими данными."""
    # Отправляем пустой словарь или словарь без ключевых углов
    msg = analyzer.process_frame({"someOtherData": 123})
    assert msg.type == "FEEDBACK"
    assert msg.payload["state"] == analyzer.state
    # Состояние не должно измениться


def test_process_frame_exception(analyzer: PoseAnalyzer) -> None:
    """Тест обработки исключения внутри process_frame."""

    with patch.object(analyzer, "_update_stats", side_effect=Exception("Test Error")):
        # Нужно дойти до вызова _update_stats (переход DOWN -> UP)
        analyzer.state = "DOWN"
        # kneeAngle > 170
        msg = analyzer.process_frame({"hipAngle": 170.0, "kneeAngle": 175.0})

        assert msg.type == "ERROR"
        assert msg.payload["message"] == "Internal processing error"
