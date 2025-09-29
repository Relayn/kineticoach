"""
Содержит класс PoseAnalyzer, отвечающий за обработку данных о позе
и управление состоянием сессии анализа.
"""

import base64
import logging
from typing import Any, Dict, TypeAlias, cast

import cv2
import numpy as np
from app.analysis.pose_processor import PoseProcessor
from app.schemas import ServerMessage
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

# Создаем псевдоним типа для наглядности: массив NumPy с 8-битными целыми числами
# Явно указываем, что это TypeAlias для mypy в строгом режиме.
NDArrayU8: TypeAlias = NDArray[np.uint8]


class PoseAnalyzer:
    """
    Управляет состоянием и логикой анализа для одной сессии
    (одного WebSocket-соединения).
    """

    def __init__(self) -> None:
        """Инициализирует анализатор для новой сессии."""
        self.rep_counter: int = 0
        self.processor = PoseProcessor()
        logger.info("Экземпляр PoseAnalyzer создан и инициализирован с PoseProcessor.")

    def _decode_frame(self, base64_str: str) -> NDArrayU8 | None:
        """Декодирует строку base64 в кадр OpenCV (numpy array)."""
        try:
            # Строка может содержать префикс data:image/jpeg;base64,
            if "," in base64_str:
                base64_str = base64_str.split(",")[1]

            img_bytes = base64.b64decode(base64_str)
            img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
            # cv2.IMREAD_COLOR гарантирует, что это 3-канальное BGR изображение
            frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            # Явно "приводим" тип, т.к. mypy не доверяет типам из cv2
            return cast(NDArrayU8, frame)
        except Exception as e:
            logger.error(f"Ошибка декодирования base64 кадра: {e}")
            return None

    def process_data(self, data: Dict[str, Any]) -> ServerMessage:
        """
        Обрабатывает входящие данные о позе.

        Args:
            data: Словарь с данными от клиента. Ожидается ключ 'frame'
                  со строкой base64, представляющей кадр видео.

        Returns:
            Сообщение сервера с результатом анализа.
        """
        frame_b64 = data.get("frame")
        if not frame_b64 or not isinstance(frame_b64, str):
            return ServerMessage(
                type="ERROR",
                payload={
                    "message": "Ключ 'frame' отсутствует или имеет неверный формат."
                },
            )

        frame = self._decode_frame(frame_b64)
        if frame is None:
            return ServerMessage(
                type="ERROR",
                payload={"message": "Не удалось декодировать кадр из base64."},
            )

        landmarks = self.processor.get_landmarks(frame)

        if landmarks:
            # --- Логика-заглушка ---
            # В будущем здесь будет сложный анализ углов.
            self.rep_counter += 1
            logger.info(f"Обнаружены ключевые точки. Счетчик: {self.rep_counter}")
            payload = {
                "message": "Ключевые точки успешно обнаружены.",
                "rep_count": self.rep_counter,
                "has_landmarks": True,
            }
            return ServerMessage(type="FEEDBACK", payload=payload)
        else:
            logger.info("Ключевые точки не обнаружены на кадре.")
            payload = {
                "message": "Человек не обнаружен на кадре.",
                "rep_count": self.rep_counter,
                "has_landmarks": False,
            }
            return ServerMessage(type="FEEDBACK", payload=payload)
