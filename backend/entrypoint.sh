#!/usr/bin/env bash
set -euo pipefail

# Entrypoint runs wait_for_services.sh, optionally runs alembic migrations if DATABASE_URL is set,
# then execs the provided command as the non-root app user.

# Default hosts (can be overridden via env)
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
CHROMA_HOST="${CHROMA_HOST:-chromadb}"
CHROMA_PORT="${CHROMA_PORT:-8000}"

# Run waiting checks (reuse existing script)
if [ -x "/app/backend/wait_for_services.sh" ]; then
  /app/backend/wait_for_services.sh &
  WAIT_PID=$!
else
  echo "wait_for_services.sh not found or not executable; skipping wait"
fi

# If DATABASE_URL is provided, run alembic upgrade head to apply migrations
if [ -n "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL present; running alembic migrations"
  if [ -x "$(command -v alembic)" ]; then
    alembic upgrade head || echo "Alembic migrations failed; continuing"
  else
    echo "Alembic not installed in environment; ensure migrations are applied in CI/CD"
  fi
fi

# Wait for wait script to finish backgrounded checks (if present)
if [ -n "${WAIT_PID:-}" ]; then
  # Give wait script a short headstart then kill it (we don't want to block forever)
  sleep 1
  kill "${WAIT_PID}" 2>/dev/null || true
fi

# Exec the command (should be run as the CMD -> uvicorn). Use exec so signals pass through.
exec "$@"
