# Этап 1: Сборка статических файлов
FROM node:20-alpine AS builder

WORKDIR /app

# Копируем package.json и package-lock.json для кэширования зависимостей
COPY package*.json ./

# Устанавливаем зависимости, используя 'ci' для воспроизводимых сборок
RUN npm ci

# Копируем остальные исходные файлы
COPY . .

# --- Внедрение переменных окружения ---
# Объявляем аргумент, который мы будем получать из docker-compose.yml
ARG VITE_WS_URL_ARG
# Создаем .env.production файл, который Vite использует для production сборок
RUN echo "VITE_WS_URL=${VITE_WS_URL_ARG}" > .env.production

# Собираем production-версию приложения
RUN npm run build

# Этап 2: Обслуживание статики через Nginx
FROM nginx:1.27-alpine AS runtime

# Копируем собранные статические файлы из этапа 'builder'
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем кастомную конфигурацию Nginx для поддержки SPA-роутинга
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт 80
EXPOSE 80

# Запускаем Nginx в foreground режиме
CMD ["nginx", "-g", "daemon off;"]
