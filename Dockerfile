FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/frontend/static /app/backend /uploads && chmod 777 /uploads

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
