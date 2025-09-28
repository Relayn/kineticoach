"""
Основной файл приложения FastAPI для KinetiCoach.
Определяет точки входа API и основную конфигурацию.
"""

from fastapi import FastAPI

app = FastAPI(
    title="KinetiCoach API",
    description="API для анализа техники приседаний в реальном времени.",
    version="0.1.0",
)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Проверяет, что сервис запущен и работает."""
    return {"status": "ok"}
