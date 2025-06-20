FROM python:3.10-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Espongo la porta (opzionale, per chiarezza)
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
