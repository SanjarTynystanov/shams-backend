FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запускаем миграции при сборке контейнера
RUN python manage.py migrate --noinput

CMD ["gunicorn", "shams_backend.wsgi:application", "--bind", "0.0.0.0:10000"]