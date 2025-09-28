"""
Содержит класс PoseAnalyzer, отвечающий за обработку данных о позе
и управление состоянием сессии анализа.
"""

import logging
from typing import Any, Dict

from app.schemas import ServerMessage

logger = logging.getLogger(__name__)


class PoseAnalyzer:
    """
    Управляет состоянием и логикой анализа для одной сессии
    (одного WebSocket-соединения).
    """

    def __init__(self) -> None:
        """Инициализирует анализатор для новой сессии."""
        self.rep_counter: int = 0
        logger.info("Экземпляр PoseAnalyzer создан и инициализирован.")

    def process_data(self, data: Dict[str, Any]) -> ServerMessage:
        """
        Обрабатывает входящие данные о позе.

        Args:
            data: Словарь с данными от клиента (например, координаты).

        Returns:
            Сообщение сервера с результатом анализа.
        """
        # --- Логика-заглушка ---
        # В будущем здесь будет сложный анализ углов и состояний.
        # Сейчас мы просто увеличиваем счетчик при каждом вызове,
        # чтобы продемонстрировать сохранение состояния.
        self.rep_counter += 1
        logger.info(f"Обработка данных. Счетчик повторений: {self.rep_counter}")

        payload = {
            "message": "Данные успешно обработаны анализатором.",
            "rep_count": self.rep_counter,
            "received_payload": data,
        }
        return ServerMessage(type="FEEDBACK", payload=payload)
