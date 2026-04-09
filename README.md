# Yargi GPT Actions Adapter

This repo exposes `yargi-mcp` tools through an OpenAPI HTTP service so they can be used from ChatGPT Custom GPT Actions.

## What it does

- runs a FastAPI adapter around `yargi-mcp`
- exposes `/openapi.json` for ChatGPT Actions
- exposes `/health` for Railway health checks
- can be deployed as a 7/24 cloud service

## Files

- `app/main.py`: FastAPI adapter
- `requirements.txt`: Python dependencies
- `railway.json`: Railway deployment settings
- `custom_gpt_instructions.md`: starter prompt for the Custom GPT

## Local run

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/openapi.json`

## Deploy

This project is ready for Railway. Railway will install `yargi-mcp` from PyPI and run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Custom GPT

After Railway deploys successfully, use this URL inside the GPT Actions schema field:

```text
https://YOUR-RAILWAY-DOMAIN/openapi.json
```
