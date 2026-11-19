FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FORSYTH_DATA_DIR=/data

WORKDIR /app

COPY backend ./backend
COPY frontend ./frontend
COPY data/resources.json ./data/resources.json

EXPOSE 8000

CMD ["sh", "-c", "exec python3 backend/server.py --host 0.0.0.0 --port ${PORT:-8000} --workers 128"]
