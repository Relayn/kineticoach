# ======================
# 1. Этап: builder
# ======================
FROM python:3.11-slim AS builder

# Системные зависимости для СБОРКИ И КОМПИЛЯЦИИ (mediapipe/opencv)
# Добавляем cmake и build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry и плагин export
ENV POETRY_VERSION=2.2.1
RUN pip install --no-cache-dir poetry=="$POETRY_VERSION" poetry-plugin-export

WORKDIR /app

# Копируем только зависимости для кэша
COPY pyproject.toml poetry.lock ./

# Экспортируем зависимости в requirements.txt
RUN python -m poetry export -f requirements.txt --without-hashes --without dev -o requirements.txt

# Фильтруем: убираем nvidia-* пакеты (CPU-only)
RUN grep -v 'nvidia' requirements.txt > requirements-filtered.txt

# Устанавливаем зависимости, ПРИНУДИТЕЛЬНО СОБИРАЯ OPENCV ИЗ ИСХОДНИКОВ
RUN pip install \
    --no-cache-dir \
    --no-binary=opencv-python-headless \
    -r requirements-filtered.txt

# ======================
# 2. Этап: runtime
# ======================
FROM python:3.11-slim AS runtime

# Runtime зависимости (только то, что реально нужно приложению)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости из builder-а
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код
COPY src ./src

# Создаем непривилегированного пользователя и назначаем права
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid 1001 appuser && \
    chown -R appuser:appgroup /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Запуск FastAPI
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
