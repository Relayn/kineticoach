"""Тесты для модуля с математическими утилитами."""

import pytest
from app.analysis.math_utils import calculate_angle


class MockLandmark:
    """
    Класс-заглушка для имитации объекта NormalizedLandmark из MediaPipe
    в целях тестирования.
    """

    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


def test_calculate_angle_right_angle() -> None:
    """Тестирует вычисление прямого угла (90 градусов)."""
    p1 = MockLandmark(0, 1)
    p2 = MockLandmark(0, 0)
    p3 = MockLandmark(1, 0)
    angle = calculate_angle(p1, p2, p3)
    assert angle == pytest.approx(90.0)


def test_calculate_angle_straight_line() -> None:
    """Тестирует вычисление развернутого угла (180 градусов)."""
    p1 = MockLandmark(-1, 0)
    p2 = MockLandmark(0, 0)
    p3 = MockLandmark(1, 0)
    angle = calculate_angle(p1, p2, p3)
    assert angle == pytest.approx(180.0)


def test_calculate_angle_acute_angle() -> None:
    """Тестирует вычисление острого угла (45 градусов)."""
    p1 = MockLandmark(0, 1)
    p2 = MockLandmark(0, 0)
    p3 = MockLandmark(1, 1)
    angle = calculate_angle(p1, p2, p3)
    assert angle == pytest.approx(45.0)


def test_calculate_angle_collinear_points() -> None:
    """Тестирует случай, когда все точки на одной линии (угол 0)."""
    p1 = MockLandmark(0, 0)
    p2 = MockLandmark(0, 0)
    p3 = MockLandmark(0, 0)
    angle = calculate_angle(p1, p2, p3)
    assert angle == pytest.approx(0.0)
