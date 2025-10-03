from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Callable
import time
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedCORSMiddleware:
    """Enhanced CORS middleware with detailed logging"""

    @staticmethod
    def configure(app):
        # Allow override via environment variable CORS_ORIGINS (comma-separated)
        import os

        raw = os.getenv("CORS_ORIGINS")
        if raw:
            origins = [o.strip() for o in raw.split(",") if o.strip()]
        else:
            origins = [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:5173",  # Vite default
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://127.0.0.1:5173",
                "https://localhost:3000",
                "https://localhost:3001",
                "https://localhost:5173",
                "https://127.0.0.1:3000",
                "https://127.0.0.1:3001",
                "https://127.0.0.1:5173",
                "https://code-evo-frontend-z2cx.vercel.app",
            ]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=[
                "Accept",
                "Accept-Language",
                "Content-Language",
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "Origin",
                "Access-Control-Request-Method",
                "Access-Control-Request-Headers",
            ],
            expose_headers=["*"],
        )
        logger.info(f"✅ CORS configured for frontend connections: {origins}")


class ConnectionLoggingMiddleware:
    """Middleware to log all connections and debug issues"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()

            # Log incoming request
            request = Request(scope, receive)
            client_host = request.client.host if request.client else "unknown"
            logger.info(f"{request.method} {request.url.path} from {client_host}")

            # Track response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = time.time() - start_time
                    status = message["status"]
                    logger.info(f"Response: {status} in {duration:.3f}s")
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


class RequestValidationMiddleware:
    """Ensure request/response integrity"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Store original body for validation
            body = b""

            async def receive_wrapper():
                nonlocal body
                message = await receive()
                if message["type"] == "http.request":
                    body += message.get("body", b"")
                return message

            # Create new scope with body
            scope["body"] = body

            await self.app(scope, receive_wrapper, send)
        else:
            await self.app(scope, receive, send)
