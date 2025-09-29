"""
Модуль с математическими утилитами для анализа поз.

Содержит чистые функции для выполнения вычислений над координатами
ключевых точек (landmarks).
"""

import math

import numpy as np
from mediapipe.framework.formats import landmark_pb2


def calculate_angle(
    p1: landmark_pb2.NormalizedLandmark,
    p2: landmark_pb2.NormalizedLandmark,
    p3: landmark_pb2.NormalizedLandmark,
) -> float:
    """
    Вычисляет угол между тремя точками в 2D-пространстве.

    Угол вычисляется в точке p2. Например, для коленного сустава это будет
    (бедро, колено, лодыжка).

    Args:
        p1: Первая точка (например, бедро).
        p2: Вторая, центральная точка (например, колено).
        p3: Третья точка (например, лодыжка).

    Returns:
        Угол в градусах (от 0 до 180).
    """
    # Создаем векторы от центральной точки p2
    # Используем только x и y для 2D-анализа
    v1 = np.array([p1.x - p2.x, p1.y - p2.y])
    v2 = np.array([p3.x - p2.x, p3.y - p2.y])

    # Вычисляем угол между векторами с помощью скалярного произведения
    dot_product = np.dot(v1, v2)
    norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)

    # Предотвращаем деление на ноль, если точки совпадают
    if norm_product == 0:
        return 0.0

    # Ограничиваем значение косинуса в диапазоне [-1, 1] из-за ошибок округления
    cosine_angle = np.clip(dot_product / norm_product, -1.0, 1.0)

    # Переводим радианы в градусы
    angle_rad = math.acos(cosine_angle)
    angle_deg = math.degrees(angle_rad)

    return angle_deg
