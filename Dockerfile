FROM python:3.10-slim

# Crea una directory di lavoro
WORKDIR /app

# Copia i requirements
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice sorgente
COPY . .

# Espone la porta (opzionale, per chiarezza)
EXPOSE 8000

# Comando per avviare l'app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
