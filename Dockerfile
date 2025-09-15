# Базовый образ Python
FROM python:3.12-slim

# Рабочая директория внутри контейнера
WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение внутрь контейнера
COPY . .

# Команда запуска (перезаписывается в docker-compose.yml)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]