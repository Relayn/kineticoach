"""
Модуль для управления конфигурацией приложения.

Использует Pydantic Settings для загрузки настроек из переменных окружения,
что позволяет безопасно управлять секретами и параметрами.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Определяет переменные окружения для приложения.
    """

    # Загружает переменные из файла .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Токен для Telegram Bot API, полученный от @BotFather
    TELEGRAM_BOT_TOKEN: str = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

    # Публичный URL, по которому будет доступен наш Frontend (Mini App)
    # Для локальной разработки можно использовать ngrok
    WEB_APP_URL: str = "https://your-domain.com"


# Создаем единственный экземпляр настроек,
# который будет использоваться во всем приложении
settings = Settings()
