# Deployment notes for Railway and Docker

This document explains how to run Code-Evo locally with Docker Compose and how to prepare the project for deployment to Railway.

## Key points

- Ollama is optional. The app will try to detect and use Ollama if `OLLAMA_HOST` is set and reachable. If Ollama can't be reached, the service falls back to API models (OpenAI/Anthropic) if credentials are provided.
- For local development we provide Redis, ChromaDB, and an optional Ollama and Postgres in `docker-compose.yaml`.
- Railway containers are ephemeral. Use a managed DB (Postgres) instead of SQLite in production.

## Local dev (recommended)

1. Start Ollama locally (if using local models):

   - Install Ollama: https://ollama.com
   - Pull models (example): `ollama pull codellama:7b`
   - Start Ollama server: `ollama serve`

2. Start services using Docker Compose:

```bash
# Build backend image and start services
docker compose up --build
```

3. Access the API at: `http://localhost:8080`

4. If Ollama is running on the host and you're on macOS/Windows, `docker-compose.yaml` defaults `OLLAMA_HOST` to `host.docker.internal`. On Linux you may need to set `OLLAMA_HOST` to the host's IP address or run Ollama inside Docker (see Optional Ollama service below).

## Railway deployment guidance

Railway typically runs a single container and provides managed Postgres and Redis. Ollama is not typically available in Railway.

- Use a managed Postgres DB instead of SQLite. Add the `DATABASE_URL` env var in Railway to point to the Postgres connection.
- Configure environment variables in Railway:
  - `OPENAI_API_KEY` (if using OpenAI)
  - `ANTHROPIC_API_KEY` (if using Anthropic)
  - `REDIS_URL` or set `REDIS_HOST`/`REDIS_PORT` to point to Railway's Redis
  - `OLLAMA_HOST` only if you have a reachable Ollama instance (not common on Railway)

The app will attempt to detect Ollama at startup if `OLLAMA_HOST` is set. If it can't connect, it will continue to run and prefer API models when API keys are available.

### Railway Docker Image

Railway will build and deploy the `backend` Docker image. Ensure `Dockerfile` in `backend/` is up-to-date and that `CMD`/`ENTRYPOINT` starts uvicorn.

### Recommended Production Steps

1. Use Postgres in Railway and set `DATABASE_URL`.
2. Use managed Redis (set `REDIS_HOST`/`REDIS_PORT` accordingly).
3. Configure `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` for cloud models.
4. Do not rely on Ollama in Railway unless you host Ollama separately and set `OLLAMA_HOST` to that reachable address.

## Optional: Containerized Ollama

`docker-compose.yaml` includes an optional `ollama` service (may require an official image). If you run `ollama` inside Docker, set the backend `OLLAMA_HOST=ollama`.

## Migration: SQLite -> Postgres

- Local development uses SQLite (file `code_evolution.db`). Production should use Postgres.

1. Add `psycopg2-binary` or `asyncpg` and set `DATABASE_URL` in environment.
2. Update `app/core/database.py` to parse `DATABASE_URL` and prefer it over SQLite.
3. Run migrations (Alembic) to create tables in Postgres:

```bash
alembic upgrade head
```

4. Optionally export SQLite to Postgres by dumping data and importing with a script.

## Quick checklist for Railway-ready deployment

- [ ] Add `DATABASE_URL` to Railway (managed Postgres)
- [ ] Add `REDIS_HOST`/`REDIS_PORT` or `REDIS_URL` for managed Redis
- [ ] Add `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` if using cloud models
- [ ] Do not expect Ollama on Railway; configure `OLLAMA_HOST` only if you run it externally

**_ End of Railway deployment notes _**
