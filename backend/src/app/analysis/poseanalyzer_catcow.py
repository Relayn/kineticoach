"""PoseAnalyzer для упражнения Кошка-Корова (Cat-Cow Pose)."""

import logging
from collections import defaultdict
from typing import Any, Dict, List

from app.analysis import rules_catcow as rules
from app.schemas import ServerMessage

logger = logging.getLogger(__name__)


class CatCowAnalyzer:
    """Анализатор техники выполнения упражнения Кошка-Корова.

    Отслеживает переходы между позами CAT (спина дугой) и COW (спина прогнута).
    Клиент отправляет уже вычисленные углы позвоночника и положение головы.
    """

    def __init__(self) -> None:
        """Инициализация анализатора Cat-Cow."""
        self.transition_count: int = 0
        self.state: str = "NEUTRAL"  # NEUTRAL -> CAT -> COW -> CAT -> ...
        self.feedback: List[str] = []
        self.debug_data: Dict[str, float] = {}
        self.stats: Dict[str, int] = defaultdict(int)
        logger.info("CatCowAnalyzer initialized (Client-Side Logic).")

    def update_stats(self) -> None:
        """Обновление статистики на основе feedback."""
        if not self.feedback:
            return
        if rules.GOOD_TRANSITION in self.feedback:
            self.stats["good_transitions"] += 1
        else:
            for error in self.feedback:
                self.stats[error] += 1

    def check_errors_cat_phase(self, spine_angle: float, head_height: float) -> None:
        """Проверка ошибок в позе 'кошка' (CAT).

        Args:
            spine_angle: Угол позвоночника (нос-плечи-бедра).
            head_height: Высота головы относительно плеч (отрицательная = выше).
        """
        # Проверка прогиба спины
        if spine_angle > rules.SPINE_CAT_MAX:
            if rules.SPINE_NOT_ARCHED not in self.feedback:
                self.feedback.append(rules.SPINE_NOT_ARCHED)

        # Проверка опускания головы
        if head_height < rules.HEAD_LOWERED_THRESHOLD:
            if rules.HEAD_NOT_LOWERED not in self.feedback:
                self.feedback.append(rules.HEAD_NOT_LOWERED)

    def check_errors_cow_phase(self, spine_angle: float, head_height: float) -> None:
        """Проверка ошибок в позе 'корова' (COW).

        Args:
            spine_angle: Угол позвоночника (нос-плечи-бедра).
            head_height: Высота головы относительно плеч (отрицательная = выше).
        """
        # Проверка разгибания спины
        if spine_angle < rules.SPINE_COW_MIN:
            if rules.SPINE_NOT_EXTENDED not in self.feedback:
                self.feedback.append(rules.SPINE_NOT_EXTENDED)

        # Проверка поднятия головы
        if head_height > rules.HEAD_LIFTED_THRESHOLD:
            if rules.HEAD_NOT_LIFTED not in self.feedback:
                self.feedback.append(rules.HEAD_NOT_LIFTED)

    def _handle_neutral_state(
        self, current_phase: str, spine_angle: float, head_height: float
    ) -> None:
        """Обработка состояния NEUTRAL."""
        if current_phase == "CAT":
            self.state = "CAT"
            self.check_errors_cat_phase(spine_angle, head_height)
        elif current_phase == "COW":
            self.state = "COW"
            self.check_errors_cow_phase(spine_angle, head_height)

    def _handle_cat_state(
        self, current_phase: str, spine_angle: float, head_height: float
    ) -> None:
        """Обработка состояния CAT."""
        if current_phase == "COW":
            # Переход CAT -> COW
            self.state = "COW"
            self.transition_count += 1
            self.check_errors_cow_phase(spine_angle, head_height)
            if not self.feedback:
                self.feedback.append(rules.GOOD_TRANSITION)
            self.update_stats()
            logger.info(
                f"Transition {self.transition_count}: CAT -> COW, "
                f"feedback: {self.feedback}"
            )
        else:
            # Остаемся в фазе CAT (даже если угол временно в NEUTRAL)
            self.check_errors_cat_phase(spine_angle, head_height)

    def _handle_cow_state(
        self, current_phase: str, spine_angle: float, head_height: float
    ) -> None:
        """Обработка состояния COW."""
        if current_phase == "CAT":
            # Переход COW -> CAT
            self.state = "CAT"
            self.transition_count += 1
            self.check_errors_cat_phase(spine_angle, head_height)
            if not self.feedback:
                self.feedback.append(rules.GOOD_TRANSITION)
            self.update_stats()
            logger.info(
                f"Transition {self.transition_count}: COW -> CAT, "
                f"feedback: {self.feedback}"
            )
        else:
            # Остаемся в фазе COW
            self.check_errors_cow_phase(spine_angle, head_height)

    def analyze_pose(self, spine_angle: float, head_height: float) -> None:
        """Анализ текущей позы и определение переходов.

        Args:
            spine_angle: Угол позвоночника.
            head_height: Высота головы относительно плеч.
        """
        self.feedback = []  # Сброс feedback для нового кадра

        # Определение фазы на основе угла позвоночника
        if spine_angle <= rules.SPINE_CAT_MAX:
            current_phase = "CAT"
        elif spine_angle >= rules.SPINE_COW_MIN:
            current_phase = "COW"
        else:
            current_phase = "NEUTRAL"

        # Логика переходов между состояниями
        if self.state == "NEUTRAL":
            self._handle_neutral_state(current_phase, spine_angle, head_height)

        elif self.state == "CAT":
            self._handle_cat_state(current_phase, spine_angle, head_height)

        elif self.state == "COW":
            self._handle_cow_state(current_phase, spine_angle, head_height)

    def process_frame(self, data: Dict[str, Any]) -> ServerMessage:
        """Обработка кадра с данными от клиента.

        Args:
            data: Словарь с ключами spineAngle и headHeight.

        Returns:
            ServerMessage с результатами анализа.
        """
        try:
            spine_angle = data.get("spineAngle")
            head_height = data.get("headHeight")

            if spine_angle is None or head_height is None:
                return ServerMessage(
                    type="FEEDBACK",
                    payload={
                        "transitionCount": self.transition_count,
                        "feedback": self.feedback,
                        "state": self.state,
                        "debugData": self.debug_data,
                    },
                )

            self.debug_data = {
                "spineAngle": spine_angle,
                "headHeight": head_height,
            }

            # Анализ позы
            self.analyze_pose(spine_angle, head_height)

            payload = {
                "transitionCount": self.transition_count,
                "feedback": self.feedback,
                "state": self.state,
                "debugData": self.debug_data,
            }
            return ServerMessage(type="FEEDBACK", payload=payload)

        except Exception as e:
            logger.error(f"Error processing pose data: {e}")
            return ServerMessage(
                type="ERROR", payload={"message": "Internal processing error"}
            )

    def generate_report(self) -> ServerMessage:
        """Генерация финального отчета."""
        report_payload = {
            "totalTransitions": self.transition_count,
            "goodTransitions": self.stats.get("good_transitions", 0),
            "errors": {
                key: value
                for key, value in self.stats.items()
                if key != "good_transitions"
            },
        }
        return ServerMessage(type="REPORT", payload=report_payload)
