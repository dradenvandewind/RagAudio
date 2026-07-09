# --- Image de base -----------------------------------------------------
FROM python:3.11-slim

# ffmpeg est requis par yt-dlp (extraction/conversion audio) et par whisper
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Dépendances Python -------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Code de l'application ----------------------------------------------
COPY app ./app

# Dossiers de travail (audio, srt, index) — montés en volume via docker-compose
RUN mkdir -p /app/data/audio /app/data/srt /app/data/index

EXPOSE 8000

# Un seul worker : les modèles Whisper sont volumineux et mis en cache par process.
# Pour scaler horizontalement, préférez plusieurs conteneurs plutôt que --workers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
