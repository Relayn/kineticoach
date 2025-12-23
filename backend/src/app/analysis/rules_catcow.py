"""Правила анализа упражнения Кошка-Корова (Cat-Cow Pose)."""

# Углы позвоночника (spine angle: нос - середина плеч - середина бедер)
SPINE_CAT_MIN: float = 140.0  # Минимальный угол в позе "кошка" (спина дугой вверх)
SPINE_CAT_MAX: float = 160.0  # Максимальный угол в позе "кошка"
SPINE_COW_MIN: float = 180.0  # Минимальный угол в позе "корова" (спина прогнута вниз)
SPINE_COW_MAX: float = 200.0  # Максимальный угол в позе "корова"
SPINE_NEUTRAL: float = 170.0  # Нейтральная позиция

# Положение головы (head_height: y-координата носа относительно плеч)
HEAD_LIFTED_THRESHOLD: float = -0.05  # Голова должна быть выше плеч в "корове"
HEAD_LOWERED_THRESHOLD: float = 0.05  # Голова должна быть ниже плеч в "кошке"

# Пороги для переходов
TRANSITION_ANGLE_THRESHOLD: float = (
    10.0  # Минимальное изменение угла для засчитывания перехода
)

# Ошибки (feedback messages)
SPINE_NOT_ARCHED: str = "SPINE_NOT_ARCHED"  # Недостаточный прогиб спины в "кошке"
SPINE_NOT_EXTENDED: str = (
    "SPINE_NOT_EXTENDED"  # Недостаточное разгибание спины в "корове"
)
HEAD_NOT_LIFTED: str = "HEAD_NOT_LIFTED"  # Голова не поднята в "корове"
HEAD_NOT_LOWERED: str = "HEAD_NOT_LOWERED"  # Голова не опущена в "кошке"
GOOD_TRANSITION: str = "GOOD_TRANSITION"  # Правильный переход
