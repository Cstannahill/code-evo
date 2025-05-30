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
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:5173",  # Vite default
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
        logger.info("✅ CORS configured for frontend connections")


class ConnectionLoggingMiddleware:
    """Middleware to log all connections and debug issues"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()

            # Log incoming request
            request = Request(scope, receive)
            logger.info(
                f"{request.method} {request.url.path} from {request.client.host}"
            )

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
