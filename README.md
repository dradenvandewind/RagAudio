# Dailymotion RAG — yt-dlp + Whisper + LlamaIndex + FastAPI

Complete pipeline: provide a Dailymotion URL, the API downloads the video,
extracts the audio, transcribes it with Whisper (+ generates a `.srt`), then
indexes the text in LlamaIndex to be able to ask questions about it
(RAG) on one or multiple videos.

```
Dailymotion URL
   │  yt-dlp -x --audio-format mp3  (drives ffmpeg)
   ▼
audio.mp3
   │  whisper.transcribe()
   ▼
text + segments ──► .srt (subtitles)
   │
   ▼
LlamaIndex (VectorStoreIndex) ──► /ask (RAG)
```

## 1. System Requirements

- Python 3.10+
- **ffmpeg** installed and in PATH (used internally by yt-dlp):
  ```bash
  # Ubuntu/Debian
  sudo apt install ffmpeg
  # macOS
  brew install ffmpeg
  ```
- **Ollama** installed and running (for the LLM + RAG embeddings, 100% local, no API key):
  ```bash
  # https://ollama.com/download
  ollama serve &
  ollama pull llama3.1
  ollama pull nomic-embed-text
  ```

## 2. Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Launch the API

```bash
uvicorn app.main:app --reload
```

Interactive documentation: http://localhost:8000/docs

## 4. Usage

### a) Ingest a Dailymotion video

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
        "url": "https://www.dailymotion.com/video/xxxxxxx",
        "language": "fr",
        "whisper_model": "small"
      }'
```

curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
        "url": "https://www.dailymotion.com/player/metadata/video/xanzev6",
        "language": "fr",
        "whisper_model": "small"
      }'


Response:
```json
{"job_id": "3f2a...", "status": "queued"}
```

Processing (download → transcription → indexing) is done in
the background (`BackgroundTasks`). The choice of Whisper model
(`tiny`, `base`, `small`, `medium`, `large-v3`) allows to balance between
speed (CPU) and quality (GPU).

### b) Track progress

```bash
curl http://localhost:8000/status/3f2a...
```

Possible statuses: `queued`, `downloading`, `transcribing`, `indexing`,
`done`, `error`.

### c) Retrieve subtitles

```bash
curl -O http://localhost:8000/srt/3f2a...
```

### d) Query the content (RAG)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "resume ", "top_k": 4}'
```

Response:
```json
{
  "answer": "...",
  "sources": ["https://www.dailymotion.com/video/xxxxxxx"]
}
```



# Translate

curl "http://<serveur>:8000/srt/<job_id>/translate?target_lang=en"


## 5. Launch with Docker

```bash
docker compose up --build
```


The API is then available at http://localhost:8000/docs.



## Project Structure


```
dailymotion-rag/
RagAudioExtractToSrt
├── app
│   ├── api
│   │   ├── deps.py
│   │   └── routes
│   │       ├── ask.py
│   │       ├── ingest.py
│   │       └── jobs.py
│   ├── core
│   │   ├── config.py
│   │   └── logging.py
│   ├── __init__.py
│   ├── main.py
│   ├── models
│   │   └── job.py
│   ├── schemas.py
│   └── services
│       ├── downloader.py
│       ├── __init__.py
│       ├── job_store.py
│       ├── pipeline.py
│       ├── rag_engine.py
│       ├── transcriber.py
│       └── translator.py
├── data
│   ├── audio
│   ├── index
│   │   ├── default__vector_store.json
│   │   ├── docstore.json
│   │   ├── graph_store.json
│   │   ├── image__vector_store.json
│   │   └── index_store.json
│   └── srt
├── docker-compose.yml
├── Dockerfile
├── IAC
│   ├── ansible
│   │   ├── ansible.cfg
│   │   ├── inventori.ini
│   │   ├── inventori.tpl
│   │   ├── memo.txt
│   │   ├── playbooks
│   │   │   └── setup_gpu.yml
│   │   ├── requirements.yml
│   │   ├── roles
│   │   │   ├── app
│   │   │   │   ├── defaults
│   │   │   │   │   └── main.yml
│   │   │   │   ├── handlers
│   │   │   │   │   └── main.yml
│   │   │   │   ├── tasks
│   │   │   │   │   └── main.yml
│   │   │   │   └── templates
│   │   │   │       ├── docker-compose.override.yml.j2
│   │   │   │       ├── env.j2
│   │   │   │       └── rag-api.service.j2
│   │   │   ├── docker
│   │   │   │   ├── handlers
│   │   │   │   │   └── main.yml
│   │   │   │   └── tasks
│   │   │   │       └── main.yml
│   │   │   ├── handlers
│   │   │   │   └── main.yml
│   │   │   ├── nvidia_gpu
│   │   │   │   ├── handlers
│   │   │   │   │   └── main.yml
│   │   │   │   └── tasks
│   │   │   │       └── main.yml
│   │   │   └── system
│   │   │       ├── handlers
│   │   │       │   └── main.yml
│   │   │       └── tasks
│   │   │           └── main.yml
│   │   ├── site.yml
│   │   ├── vars
│   │   │   └── main.yml
│   │   └── {vars,roles
│   │       └── {system
│   │           └── tasks,docker
│   │               └── tasks,app
│   │                   └── tasks,app
│   │                       └── templates}}
│   ├── apply_policy_all.sh
│   ├── apply_policy.sh
│   ├── apply_spot_policy.sh
│   ├── myREADME.md
│   ├── policy
│   │   ├── apply_aws_spot_policy.sh
│   │   ├── aws_spot_terraform-policy.json
│   │   ├── policy.json
│   │   ├── quota_policy.json
│   │   ├── spot_policy.json
│   │   └── ssm_policy.json
│   ├── README.md
│   ├── terraform
│   │   ├── cookies.txt
│   │   ├── inventory.tpl
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfstate
│   │   ├── terraform.tfstate.backup
│   │   ├── terraform.tfvars
│   │   ├── terraform.tfvars.example
│   │   ├── usage.txt
│   │   └── variables.tf
│   ├── {terraform,ansible
│   │   └── roles
│   │       └── {docker
│   │           └── tasks,app
│   │               └── tasks}}
│   ├── TODO.txt
│   └── Tools
│       ├── aws_spot_price_finder.py
│       ├── configuration_service_quota.txt
│       ├── get_quota_instance.sh
│       └── usage.txt
├── README.md
└── requirements.txt
```
