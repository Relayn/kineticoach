"""Unit-тесты для модуля TTS."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.analysis.tts import AUDIO_DIR, generate_voice_feedback


@pytest.mark.asyncio
async def test_generate_voice_feedback_empty_codes() -> None:
    """Тест: пустой список кодов ошибок."""
    result = await generate_voice_feedback([])
    assert result is None


@pytest.mark.asyncio
async def test_generate_voice_feedback_success() -> None:
    """Тест: успешная генерация аудио."""
    feedback_codes = ["BEND_FORWARD"]
    audio_filename = "BEND_FORWARD.mp3"
    expected_path = AUDIO_DIR / audio_filename

    # Мокаем client.audio.speech.create
    mock_response = MagicMock()
    mock_response.content = b"fake_audio_content"

    with patch(
        "app.analysis.tts.client.audio.speech.create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response

        # Мокаем работу с файловой системой, чтобы не писать реальные файлы
        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("pathlib.Path.write_bytes") as mock_write,
        ):
            result = await generate_voice_feedback(feedback_codes)

            # Проверки
            assert result == str(expected_path)
            mock_create.assert_called_once()
            mock_write.assert_called_once_with(b"fake_audio_content")


@pytest.mark.asyncio
async def test_generate_voice_feedback_cached() -> None:
    """Тест: использование кэшированного файла."""
    feedback_codes = ["BEND_FORWARD"]
    audio_filename = "BEND_FORWARD.mp3"
    expected_path = AUDIO_DIR / audio_filename

    with patch(
        "app.analysis.tts.client.audio.speech.create", new_callable=AsyncMock
    ) as mock_create:
        # Мокаем exists = True
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.write_bytes") as mock_write,
        ):
            result = await generate_voice_feedback(feedback_codes)

            assert result == str(expected_path)
            # API не должен вызываться
            mock_create.assert_not_called()
            # Запись не должна происходить
            mock_write.assert_not_called()


@pytest.mark.asyncio
async def test_generate_voice_feedback_error() -> None:
    """Тест: ошибка при генерации."""
    feedback_codes = ["BEND_FORWARD"]

    with patch(
        "app.analysis.tts.client.audio.speech.create",
        side_effect=Exception("API Error"),
    ):
        result = await generate_voice_feedback(feedback_codes)
        assert result is None
