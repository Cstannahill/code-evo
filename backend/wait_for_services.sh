#!/usr/bin/env bash
set -euo pipefail

# Wait for a TCP host/port to be available
wait_for_host() {
  local host="$1"; local port="$2"; local retry=0; local max=60
  echo "Waiting for ${host}:${port}..."
  until nc -z "$host" "$port"; do
    retry=$((retry+1))
    if [ "$retry" -ge "$max" ]; then
      echo "Timed out waiting for ${host}:${port}" >&2
      return 1
    fi
    sleep 1
  done
  echo "${host}:${port} is available"
}

echo "Starting service wait script"

# Default hosts (can be overridden via env)
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
CHROMA_HOST="${CHROMA_HOST:-chromadb}"
CHROMA_PORT="${CHROMA_PORT:-8000}"

# Wait for Redis and Chroma
wait_for_host "$REDIS_HOST" "$REDIS_PORT"
wait_for_host "$CHROMA_HOST" "$CHROMA_PORT"

# Optionally check Ollama if configured
if [ -n "${OLLAMA_HOST:-}" ]; then
  echo "Checking Ollama at ${OLLAMA_HOST}:${OLLAMA_PORT:-11434}"
  wait_for_host "$OLLAMA_HOST" "${OLLAMA_PORT:-11434}" || echo "Ollama not available; continuing without it"
fi

# Exec the main command
exec "$@"
