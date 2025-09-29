# backend/Dockerfile

# --- Этап 1: Builder ---
# На этом этапе мы устанавливаем все зависимости, включая dev, с помощью Poetry.
FROM python:3.11-slim AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем Poetry
RUN pip install poetry

# Конфигурируем Poetry, чтобы он не создавал виртуальное окружение внутри проекта
RUN poetry config virtualenvs.create false

# Копируем файлы зависимостей и устанавливаем их.
# Этот слой будет кэшироваться Docker, если файлы не изменятся.
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-root --only main

# --- Этап 2: Runtime ---
# На этом этапе мы создаем чистый образ только с необходимыми для запуска зависимостями.
FROM python:3.11-slim AS runtime

# Устанавливаем рабочую директорию и добавляем ее в PYTHONPATH
WORKDIR /app
ENV PYTHONPATH=/app

# Создаем пользователя с ограниченными правами для запуска приложения
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid 1001 appuser

# Копируем установленные зависимости из этапа "builder"
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код нашего приложения
# Теперь мы копируем содержимое папки src в корень /app
COPY src/ .

# Меняем владельца всех файлов на нашего непривилегированного пользователя
RUN chown -R appuser:appgroup /app

# Указываем matplotlib использовать временную папку для кэша
ENV MPLCONFIGDIR=/tmp/matplotlib

# Переключаемся на этого пользователя
USER appuser

# Открываем порт, на котором будет работать Uvicorn
EXPOSE 8000

# Команда для запуска приложения
# Теперь Python сможет найти модуль 'app'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
