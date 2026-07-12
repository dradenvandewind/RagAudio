# --- Base image -----------------------------------------------------
FROM python:3.12-slim
ENV PATH="/opt/venv/bin:$PATH"
# ffmpeg is required by yt-dlp (audio extraction/conversion) and Whisper
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    unzip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- uv installation --------------------------------------------------
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# --- Python dependencies -------------------------------------------------
COPY requirements.txt .
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python --no-cache -r requirements.txt && \
    uv pip install --python /opt/venv/bin/python --no-cache cython

# --- Deno installation ------------------------------------------------
RUN curl -fsSL https://deno.land/install.sh | sh && \
    ln -s /root/.deno/bin/deno /usr/local/bin/deno

# --- Application code ----------------------------------------------
COPY app ./app

# Working directories (audio, srt, index) — mounted as volumes via docker-compose
RUN mkdir -p /app/data/audio /app/data/srt /app/data/index
EXPOSE 8000

# Un seul worker : les modèles Whisper sont volumineux et mis en cache par process.
# Pour scaler horizontalement, préférez plusieurs conteneurs plutôt que --workers.
# uvloop + httptools accélèrent la boucle d'événements et le parsing HTTP ;
# --limit-concurrency et --backlog augmentent le nombre de connexions simultanées
# acceptées avant mise en file d'attente / rejet (défauts uvicorn: pas de limite
# explicite mais un backlog socket assez bas).
CMD ["/opt/venv/bin/uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--loop", "uvloop", "--http", "httptools", \
     "--limit-concurrency", "1000", \
     "--backlog", "2048", \
     "--timeout-keep-alive", "30"]