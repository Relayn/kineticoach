"""Unit-тесты для Client-Side Cat-Cow logic."""

from unittest.mock import patch

import pytest
from app.analysis.poseanalyzer_catcow import CatCowAnalyzer


@pytest.fixture
def analyzer() -> CatCowAnalyzer:
    """Фикстура: новый экземпляр анализатора."""
    return CatCowAnalyzer()


def test_good_transition_cat_to_cow(analyzer: CatCowAnalyzer) -> None:
    """Тест: правильный переход из кошки в корову."""
    # 1. Переход в CAT
    analyzer.process_frame({"spineAngle": 150.0, "headHeight": 0.1})
    assert analyzer.state == "CAT"

    # 2. Переход в COW
    result = analyzer.process_frame({"spineAngle": 190.0, "headHeight": -0.1})
    assert result.payload["transitionCount"] == 1
    assert "GOOD_TRANSITION" in result.payload["feedback"]


def test_spine_not_arched_error(analyzer: CatCowAnalyzer) -> None:
    """Тест: ошибка - недостаточный прогиб спины в кошке."""
    # Сначала входим в состояние CAT
    analyzer.process_frame({"spineAngle": 150.0, "headHeight": 0.1})
    assert analyzer.state == "CAT"

    # Теперь симулируем недостаточный прогиб (угол > MAX)
    result = analyzer.process_frame({"spineAngle": 165.0, "headHeight": 0.1})
    assert "SPINE_NOT_ARCHED" in result.payload["feedback"]


def test_spine_not_extended_error(analyzer: CatCowAnalyzer) -> None:
    """Тест: ошибка - недостаточное разгибание спины в корове."""
    # Сначала входим в состояние COW
    analyzer.process_frame({"spineAngle": 190.0, "headHeight": -0.1})
    assert analyzer.state == "COW"

    # Теперь симулируем недостаточное разгибание (угол < MIN)
    result = analyzer.process_frame({"spineAngle": 175.0, "headHeight": -0.1})
    assert "SPINE_NOT_EXTENDED" in result.payload["feedback"]


def test_multiple_transitions(analyzer: CatCowAnalyzer) -> None:
    """Тест: несколько корректных переходов."""
    # CAT -> COW -> CAT -> COW
    analyzer.process_frame({"spineAngle": 150.0, "headHeight": 0.1})
    analyzer.process_frame({"spineAngle": 190.0, "headHeight": -0.1})
    analyzer.process_frame({"spineAngle": 150.0, "headHeight": 0.1})
    result = analyzer.process_frame({"spineAngle": 190.0, "headHeight": -0.1})

    assert result.payload["transitionCount"] == 3


def test_generate_report(analyzer: CatCowAnalyzer) -> None:
    """Тест: генерация финального отчета."""
    analyzer.process_frame({"spineAngle": 150.0, "headHeight": 0.1})
    analyzer.process_frame({"spineAngle": 190.0, "headHeight": -0.1})

    report = analyzer.generate_report()
    assert report.type == "REPORT"
    assert report.payload["totalTransitions"] == 1
    assert report.payload["goodTransitions"] == 1


def test_process_frame_missing_data(analyzer: CatCowAnalyzer) -> None:
    """Тест обработки кадра с отсутствующими данными."""
    msg = analyzer.process_frame({"someOtherData": 123})
    assert msg.type == "FEEDBACK"
    assert msg.payload["state"] == analyzer.state


def test_process_frame_exception(analyzer: CatCowAnalyzer) -> None:
    """Тест обработки исключения внутри process_frame."""
    with patch.object(analyzer, "analyze_pose", side_effect=Exception("Test Error")):
        msg = analyzer.process_frame({"spineAngle": 150.0, "headHeight": 0.1})
        assert msg.type == "ERROR"
        assert msg.payload["message"] == "Internal processing error"


def test_update_stats_empty_feedback(analyzer: CatCowAnalyzer) -> None:
    """Тест update_stats с пустым feedback."""
    analyzer.feedback = []
    analyzer.update_stats()
    assert not analyzer.stats


def test_update_stats_mixed_feedback(analyzer: CatCowAnalyzer) -> None:
    """Тест update_stats с ошибками."""
    analyzer.feedback = ["SOME_ERROR", "ANOTHER_ERROR"]
    analyzer.update_stats()
    assert analyzer.stats["SOME_ERROR"] == 1
    assert analyzer.stats["ANOTHER_ERROR"] == 1
    assert "good_transitions" not in analyzer.stats


def test_check_errors_cat_phase_duplicate(analyzer: CatCowAnalyzer) -> None:
    """Тест на отсутствие дублирования ошибок в фазе CAT."""
    analyzer.feedback = ["HEAD_NOT_LOWERED"]
    # Вызываем с параметрами, которые снова вызовут ошибку
    analyzer.check_errors_cat_phase(150.0, 0.0)  # headHeight < 0.05 -> ошибка
    assert analyzer.feedback.count("HEAD_NOT_LOWERED") == 1


def test_check_errors_cow_phase_duplicate(analyzer: CatCowAnalyzer) -> None:
    """Тест на отсутствие дублирования ошибок в фазе COW."""
    analyzer.feedback = ["HEAD_NOT_LIFTED"]
    # Вызываем с параметрами, которые снова вызовут ошибку
    analyzer.check_errors_cow_phase(
        190.0, 0.0
    )  # headHeight > -0.05 -> ошибка (0.0 > -0.05)
    assert analyzer.feedback.count("HEAD_NOT_LIFTED") == 1
