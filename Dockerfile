# Используем официальный легкий образ Python
FROM python:3.11-slim

# Устанавливаем переменные окружения
# PYTHONDONTWRITEBYTECODE: Запрещает Python писать .pyc файлы
# PYTHONUNBUFFERED: Гарантирует, что логи выводятся в консоль сразу
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
# Делаем это ДО копирования всего кода, чтобы использовать кэш Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта
COPY . .

# Открываем порт 5000
EXPOSE 5000

# Команда запуска
CMD ["python", "app.py"]
