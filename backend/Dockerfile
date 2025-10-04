# ======================
# 1. Этап: builder
# ======================
FROM python:3.11-slim AS builder

# Устанавливаем Poetry
ENV POETRY_VERSION=2.2.1
RUN pip install --no-cache-dir poetry=="$POETRY_VERSION"

# Говорим Poetry не создавать venv, а ставить пакеты в глобальный site-packages
RUN poetry config virtualenvs.create false

WORKDIR /app

# Копируем только файлы зависимостей для кэширования этого слоя
COPY pyproject.toml poetry.lock ./

# Устанавливаем только production-зависимости.
# Poetry автоматически использует CPU-источник для torch.
RUN poetry install --no-interaction --no-root --only main

# ======================
# 2. Этап: runtime
# ======================
FROM python:3.11-slim AS runtime

# Устанавливаем системные зависимости, необходимые для OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем установленные Python-пакеты из builder-а
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код
COPY src/ ./src

# Указываем Python, где искать наши модули
ENV PYTHONPATH=/app/src

# Устанавливаем переменную окружения для matplotlib
ENV MPLCONFIGDIR=/tmp

# Создаем и переключаемся на непривилегированного пользователя
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid 1001 appuser && \
    chown -R appuser:appgroup /app
USER appuser

# Запуск FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ws", "wsproto", "--log-level", "info"]
