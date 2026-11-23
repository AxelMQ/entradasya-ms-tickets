# ==============================================================================
# Dockerfile: ms-tickets (Python 3.11 FastAPI - Slim Non-Root)
# ==============================================================================

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8005 \
    STORAGE_PATH=/app/storage/tickets

# Crear usuario y grupo no-root
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /bin/bash -m appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Crear directorio de tickets y asegurar permisos
RUN mkdir -p /app/storage/tickets && \
    chown -R appuser:appuser /app/storage

COPY app ./app
COPY main.py ./

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8005

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
