"""
Содержит класс PoseAnalyzer, отвечающий за обработку данных о позе
и управление состоянием сессии анализа.
"""

import base64
import logging
from typing import Any, Dict, List, TypeAlias, cast

import cv2
import numpy as np
from app.analysis import rules
from app.analysis.math_utils import calculate_angle
from app.analysis.pose_processor import PoseProcessor
from app.schemas import ServerMessage
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

# Псевдонимы типов для наглядности
NDArrayU8: TypeAlias = NDArray[np.uint8]
Landmarks: TypeAlias = List[Any]  # Any, т.к. mediapipe использует кастомный тип


class PoseAnalyzer:
    """
    Управляет состоянием и логикой анализа для одной сессии.
    Реализует конечный автомат для отслеживания фаз приседания.
    """

    def __init__(self) -> None:
        """Инициализирует анализатор для новой сессии."""
        self.processor = PoseProcessor()
        self.rep_counter: int = 0
        self.state: str = "UP"
        self.min_knee_angle: float = 180.0
        self.feedback: List[str] = []
        self.debug_data: Dict[str, float] = {}  # Словарь для отладочных данных
        logger.info("Экземпляр PoseAnalyzer создан и инициализирован.")

    def _decode_frame(self, base64_str: str) -> NDArrayU8 | None:
        """Декодирует строку base64 в кадр OpenCV (numpy array)."""
        try:
            if "," in base64_str:
                base64_str = base64_str.split(",")[1]
            img_bytes = base64.b64decode(base64_str)
            img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            return cast(NDArrayU8, frame)
        except Exception as e:
            logger.error(f"Ошибка декодирования base64 кадра: {e}")
            return None

    def _check_errors(self, hip_angle: float) -> None:
        """Централизованно проверяет ошибки техники в фазе DOWN."""
        if hip_angle < rules.BODY_BEND_FORWARD_THRESHOLD:
            if "BEND_FORWARD" not in self.feedback:
                self.feedback.append("BEND_FORWARD")
        # Сюда в будущем будут добавляться другие проверки

    def _handle_state_up(self, knee_angle: float, hip_angle: float) -> None:
        """Обрабатывает логику для состояния 'UP'."""
        if knee_angle < rules.REP_TRANSITION_ANGLE:
            self.state = "DOWN"
            self.min_knee_angle = knee_angle
            self.feedback = []
            # Сразу проверяем ошибки на кадре, где началось движение
            self._check_errors(hip_angle)

    def _handle_state_down(self, knee_angle: float, hip_angle: float) -> None:
        """Обрабатывает логику для состояния 'DOWN'."""
        # Сначала проверяем, не завершилось ли повторение
        if knee_angle > rules.REP_TRANSITION_ANGLE:
            self.state = "UP"
            self.rep_counter += 1

            # Финальный анализ на основе всего, что мы собрали в фазе DOWN
            if self.min_knee_angle > rules.SQUAT_DEPTH_GOOD_MAX:
                self.feedback.append("LOWER_YOUR_HIPS")

            if not self.feedback:
                self.feedback.append("GOOD_REP")

            logger.info(
                f"Повторение {self.rep_counter} завершено. Результат: {self.feedback}"
            )
        else:
            # Если повторение продолжается, обновляем метрики и проверяем ошибки
            self.min_knee_angle = min(self.min_knee_angle, knee_angle)
            self._check_errors(hip_angle)

    def _analyze_pose(self, landmarks: Landmarks) -> None:
        """Диспетчер, который вызывает обработчик для текущего состояния."""
        LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE, LEFT_ANKLE = 11, 23, 25, 27

        shoulder = landmarks[LEFT_SHOULDER]
        hip = landmarks[LEFT_HIP]
        knee = landmarks[LEFT_KNEE]
        ankle = landmarks[LEFT_ANKLE]

        # --- Проверка видимости ключевых точек ---
        # Если мы не уверены в положении ног и таза, пропускаем анализ кадра.
        if (
            hip.visibility < rules.MIN_VISIBILITY_THRESHOLD
            or knee.visibility < rules.MIN_VISIBILITY_THRESHOLD
            or ankle.visibility < rules.MIN_VISIBILITY_THRESHOLD
        ):
            self.debug_data = {}  # Очищаем отладочные данные, если поза невалидна
            return

        knee_angle = calculate_angle(hip, knee, ankle)
        hip_angle = calculate_angle(shoulder, hip, knee)

        # Сохраняем вычисленные углы для отладки
        self.debug_data = {"knee_angle": knee_angle, "hip_angle": hip_angle}

        if self.state == "UP":
            self._handle_state_up(knee_angle, hip_angle)
        elif self.state == "DOWN":
            self._handle_state_down(knee_angle, hip_angle)

    def process_data(self, data: Dict[str, Any]) -> ServerMessage:
        """Обрабатывает входящие данные, запускает анализ и возвращает результат."""
        frame_b64 = data.get("frame")
        if not frame_b64 or not isinstance(frame_b64, str):
            return ServerMessage(type="ERROR", payload={"message": "Frame is missing."})

        frame = self._decode_frame(frame_b64)
        if frame is None:
            return ServerMessage(
                type="ERROR", payload={"message": "Frame decode error."}
            )

        landmarks = self.processor.get_landmarks(frame)
        has_landmarks = landmarks is not None

        feedback_to_send = []
        if landmarks is not None:
            state_before_analysis = self.state
            self._analyze_pose(landmarks)
            if state_before_analysis == "DOWN" and self.state == "UP":
                feedback_to_send = self.feedback
        else:
            self.debug_data = {}  # Очищаем данные, если человек не найден

        payload = {
            "rep_count": self.rep_counter,
            "has_landmarks": has_landmarks,
            "feedback": feedback_to_send,
            "state": self.state,
            "debug_data": self.debug_data,  # Добавляем отладочные данные
        }
        return ServerMessage(type="FEEDBACK", payload=payload)
