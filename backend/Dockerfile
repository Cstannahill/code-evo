# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    netcat-openbsd \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure wait script is executable
RUN chmod +x /app/wait_for_services.sh

# Expose port used by the FastAPI app (default 8080, can be overridden by $PORT)
EXPOSE 8080

# Liveness check — use $PORT when provided (shell form allows env expansion)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD sh -c 'curl -fsS http://127.0.0.1:${PORT:-8080}/health || exit 1'

# Default command: wait for dependencies then start uvicorn (respect $PORT and enable proxy headers)
ENTRYPOINT ["/app/wait_for_services.sh"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers"]