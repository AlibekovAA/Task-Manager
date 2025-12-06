FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/frontend/static /app/backend /uploads && \
    chown -R appuser:appuser /app /uploads

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY main.py .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/docs').read()" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
