# Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY .env /app/.env

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаём папку для базы
RUN mkdir -p data

# Копируем уже заполненную базу
COPY data/compendium.db /app/data/compendium.db
COPY config.py /app/config.py

# Копируем исходный код
COPY src/ /app/src/
COPY main.py /app/

# Убедимся, что у БД есть права на запись (на случай, если API будет писать)
RUN chmod -R 755 data/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
