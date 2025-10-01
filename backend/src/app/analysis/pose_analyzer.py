"""
Содержит класс PoseAnalyzer, отвечающий за обработку данных о позе
и управление состоянием сессии анализа.
"""

import base64
import logging
from collections import defaultdict
from typing import Any, Dict, List, TypeAlias, cast

import cv2
import numpy as np
from app.analysis import rules
from app.analysis.math_utils import calculate_angle
from app.analysis.pose_processor import PoseProcessor
from app.schemas import ServerMessage
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

NDArrayU8: TypeAlias = NDArray[np.uint8]
Landmarks: TypeAlias = List[Any]


class PoseAnalyzer:
    """
    Управляет состоянием и логикой анализа для одной сессии.
    Реализует конечный автомат для отслеживания фаз приседания.
    """

    def __init__(self) -> None:
        self.processor = PoseProcessor()
        self.rep_counter: int = 0
        self.state: str = "UP"
        self.min_knee_angle: float = 180.0
        self.max_hip_angle_at_top: float = 0.0
        self.feedback: List[str] = []
        self.debug_data: Dict[str, float] = {}
        self.stats: Dict[str, int] = defaultdict(int)
        logger.info("Экземпляр PoseAnalyzer создан и инициализирован.")

    def _decode_frame(self, base64_str: str) -> NDArrayU8 | None:
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

    def _update_stats(self) -> None:
        if not self.feedback:
            return
        if "GOOD_REP" in self.feedback:
            self.stats["good_reps"] += 1
        else:
            for error in self.feedback:
                self.stats[error] += 1

    def _check_errors_down_phase(
        self, hip_angle: float, knee_x: float, ankle_x: float, shoulder_width: float
    ) -> None:
        if hip_angle < rules.BODY_BEND_FORWARD_THRESHOLD:
            if "BEND_FORWARD" not in self.feedback:
                self.feedback.append("BEND_FORWARD")
        if abs(knee_x - ankle_x) > (shoulder_width * rules.KNEE_OVER_TOE_THRESHOLD):
            if "KNEE_OVER_TOE" not in self.feedback:
                self.feedback.append("KNEE_OVER_TOE")

    def _check_errors_up_phase(self) -> None:
        if self.min_knee_angle > rules.SQUAT_DEPTH_GOOD_MAX:
            self.feedback.append("LOWER_YOUR_HIPS")
        if self.min_knee_angle < rules.SQUAT_DEPTH_GOOD_MIN:
            self.feedback.append("SQUAT_TOO_DEEP")
        if self.max_hip_angle_at_top > rules.BODY_BEND_BACKWARDS_THRESHOLD:
            self.feedback.append("BEND_BACKWARDS")

    def _analyze_pose(self, landmarks: Landmarks) -> None:
        """
        Основной метод анализа, реализующий логику конечного автомата
        с "проваливанием" (fall-through).
        """
        (
            LEFT_SHOULDER,
            RIGHT_SHOULDER,
            LEFT_HIP,
            LEFT_KNEE,
            LEFT_ANKLE,
            LEFT_FOOT_INDEX,
        ) = (11, 12, 23, 25, 27, 31)

        shoulder_l, shoulder_r = landmarks[LEFT_SHOULDER], landmarks[RIGHT_SHOULDER]
        hip, knee = landmarks[LEFT_HIP], landmarks[LEFT_KNEE]
        ankle, foot = landmarks[LEFT_ANKLE], landmarks[LEFT_FOOT_INDEX]

        if any(
            lm.visibility < rules.MIN_VISIBILITY_THRESHOLD
            for lm in [shoulder_l, shoulder_r, hip, knee, ankle, foot]
        ):
            self.debug_data = {}
            return

        knee_angle = calculate_angle(hip, knee, ankle)
        hip_angle = calculate_angle(shoulder_l, hip, knee)
        shoulder_width = abs(shoulder_l.x - shoulder_r.x)

        self.debug_data = {
            "knee_angle": knee_angle,
            "hip_angle": hip_angle,
            "knee_foot_diff": knee.x - foot.x,
            "knee_threshold": shoulder_width * rules.KNEE_OVER_TOE_THRESHOLD,
        }

        # --- Логика конечного автомата ---

        if self.state == "UP":
            self.max_hip_angle_at_top = max(self.max_hip_angle_at_top, hip_angle)
            if knee_angle < rules.REP_TRANSITION_ANGLE:
                # НАЧАЛО ПОВТОРЕНИЯ: Переход UP -> DOWN
                self.state = "DOWN"
                self.min_knee_angle = knee_angle
                self.feedback = []
                # Важно: после смены состояния, этот же кадр СРАЗУ обрабатывается
                # как кадр в состоянии DOWN (логика "проваливания").

        if self.state == "DOWN":
            # ОБРАБОТКА ФАЗЫ ПРИСЕДА
            self.min_knee_angle = min(self.min_knee_angle, knee_angle)
            self._check_errors_down_phase(hip_angle, knee.x, foot.x, shoulder_width)

            if knee_angle > rules.REP_TRANSITION_ANGLE:
                # ЗАВЕРШЕНИЕ ПОВТОРЕНИЯ: Переход DOWN -> UP
                self.state = "UP"
                self.rep_counter += 1
                self._check_errors_up_phase()
                if not self.feedback:
                    self.feedback.append("GOOD_REP")
                self._update_stats()
                logger.info(f"Повторение {self.rep_counter} завершено: {self.feedback}")
                self.max_hip_angle_at_top = 0.0

    def generate_report(self) -> ServerMessage:
        report_payload = {
            "total_reps": self.rep_counter,
            "good_reps": self.stats["good_reps"],
            "errors": {
                key: value for key, value in self.stats.items() if key != "good_reps"
            },
        }
        return ServerMessage(type="REPORT", payload=report_payload)

    def process_frame(self, data: Dict[str, Any]) -> ServerMessage:
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
        serializable_landmarks = []

        if landmarks is not None:
            state_before = self.state
            self._analyze_pose(landmarks)
            if state_before == "DOWN" and self.state == "UP":
                feedback_to_send = self.feedback
            serializable_landmarks = [
                {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                for lm in landmarks
            ]
        else:
            self.debug_data = {}

        payload = {
            "rep_count": self.rep_counter,
            "has_landmarks": has_landmarks,
            "feedback": feedback_to_send,
            "state": self.state,
            "debug_data": self.debug_data,
            "landmarks": serializable_landmarks,
        }
        return ServerMessage(type="FEEDBACK", payload=payload)
