FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DB_PATH=/data/reminders.db

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY run.py .

RUN useradd -r -u 1000 app && mkdir -p /data && chown -R app:app /data
USER app

CMD ["python", "run.py"]