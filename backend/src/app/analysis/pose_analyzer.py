"""
Содержит класс PoseAnalyzer, отвечающий за обработку данных о позе
и управление состоянием сессии анализа.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List

from app.analysis import rules
from app.schemas import ServerMessage

logger = logging.getLogger(__name__)


class PoseAnalyzer:
    """
    Управляет состоянием и логикой анализа для одной сессии.
    Реализует конечный автомат для отслеживания фаз приседания.
    Работает с уже вычисленными углами, полученными от клиента.
    """

    def __init__(self) -> None:
        self.rep_counter: int = 0
        self.state: str = "UP"
        self.min_knee_angle: float = 180.0
        self.feedback: List[str] = []
        self.debug_data: Dict[str, float] = {}
        self.stats: Dict[str, int] = defaultdict(int)
        logger.info("Экземпляр PoseAnalyzer (Client-Side Logic) создан.")

    def _update_stats(self) -> None:
        if not self.feedback:
            return
        if "GOOD_REP" in self.feedback:
            self.stats["good_reps"] += 1
        else:
            for error in self.feedback:
                self.stats[error] += 1

    def _check_errors_down_phase(
        self, hip_angle: float, knee_x: float, foot_x: float, shoulder_width: float
    ) -> None:
        if hip_angle < rules.BODY_BEND_FORWARD_THRESHOLD:
            if "BEND_FORWARD" not in self.feedback:
                self.feedback.append("BEND_FORWARD")

        # Сравниваем смещение колена относительно носка
        # Если shoulder_width не передан (0), пропускаем проверку.
        if shoulder_width > 0:
            if abs(knee_x - foot_x) > (shoulder_width * rules.KNEE_OVER_TOE_THRESHOLD):
                if "KNEE_OVER_TOE" not in self.feedback:
                    self.feedback.append("KNEE_OVER_TOE")

    def _check_errors_up_phase(self, hip_angle_at_top: float) -> None:
        if self.min_knee_angle > rules.SQUAT_DEPTH_GOOD_MAX:
            if "LOWER_YOUR_HIPS" not in self.feedback:
                self.feedback.append("LOWER_YOUR_HIPS")
        elif self.min_knee_angle < rules.SQUAT_DEPTH_GOOD_MIN:
            if "SQUAT_TOO_DEEP" not in self.feedback:
                self.feedback.append("SQUAT_TOO_DEEP")

        if hip_angle_at_top > rules.BODY_BEND_BACKWARDS_THRESHOLD:
            if "BEND_BACKWARDS" not in self.feedback:
                self.feedback.append("BEND_BACKWARDS")

    def process_frame(self, data: Dict[str, Any]) -> ServerMessage:
        """
        Обрабатывает кадр данных (углы), полученный от клиента.
        """
        try:
            hip_angle = data.get("hipAngle")
            knee_angle = data.get("kneeAngle")
            knee_x = data.get("kneeX")
            foot_x = data.get("footX")
            shoulder_width = data.get("shoulderWidth", 0.0)

            # Если критические данные отсутствуют, возвращаем текущее состояние
            if hip_angle is None or knee_angle is None:
                return ServerMessage(
                    type="FEEDBACK",
                    payload={
                        "rep_count": self.rep_counter,
                        "feedback": self.feedback,
                        "state": self.state,
                        "debug_data": self.debug_data,
                    },
                )

            self.debug_data = {
                "knee_angle": knee_angle,
                "hip_angle": hip_angle,
                "knee_foot_diff": abs(knee_x - foot_x)
                if (knee_x is not None and foot_x is not None)
                else 0,
                "knee_threshold": shoulder_width * rules.KNEE_OVER_TOE_THRESHOLD,
            }

            # --- Логика конечного автомата ---

            if self.state == "UP":
                if knee_angle < rules.REP_TRANSITION_ANGLE:
                    # НАЧАЛО ПОВТОРЕНИЯ: Переход UP -> DOWN
                    self.state = "DOWN"
                    self.min_knee_angle = knee_angle
                    self.feedback = []

            if self.state == "DOWN":
                # ОБРАБОТКА ФАЗЫ ПРИСЕДА
                self.min_knee_angle = min(self.min_knee_angle, knee_angle)

                if knee_x is not None and foot_x is not None:
                    self._check_errors_down_phase(
                        hip_angle, knee_x, foot_x, shoulder_width
                    )

                if knee_angle > rules.REP_TRANSITION_ANGLE:
                    # ЗАВЕРШЕНИЕ ПОВТОРЕНИЯ: Переход DOWN -> UP
                    self.state = "UP"
                    self.rep_counter += 1
                    self._check_errors_up_phase(hip_angle)

                    if not self.feedback:
                        self.feedback.append("GOOD_REP")

                    self._update_stats()
                    logger.info(
                        f"Повторение {self.rep_counter} завершено: {self.feedback}"
                    )

            return ServerMessage(
                type="FEEDBACK",
                payload={
                    "rep_count": self.rep_counter,
                    "feedback": self.feedback,
                    "state": self.state,
                    "debug_data": self.debug_data,
                },
            )

        except Exception as e:
            logger.error(f"Error processing pose data: {e}")
            return ServerMessage(
                type="ERROR", payload={"message": "Internal processing error"}
            )

    def generate_report(self) -> ServerMessage:
        report_payload = {
            "total_reps": self.rep_counter,
            "good_reps": self.stats["good_reps"],
            "errors": {
                key: value for key, value in self.stats.items() if key != "good_reps"
            },
        }
        return ServerMessage(type="REPORT", payload=report_payload)
