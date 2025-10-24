from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
import logging
from rich.logging import RichHandler
import sys
import asyncio
from datetime import datetime
import traceback
import json
from bson import ObjectId
import os
from app.models.repository import (
    RepositorySQL,
    CommitSQL,
    FileChangeSQL,
    TechnologySQL,
    PatternSQL,
    PatternOccurrenceSQL,
    AnalysisSessionSQL,
    AIModelSQL,
    AIAnalysisResultSQL,
    ModelBenchmarkSQL,
    UserSQL,
    APIKeySQL,
    UserRepositorySQL,
)
from app.core.database import (
    create_tables,
    engine,
    get_db_info,
    get_enhanced_database_manager,
)  # Unified database module
from app.core.middleware import (
    EnhancedCORSMiddleware,
    ConnectionLoggingMiddleware,
    RequestValidationMiddleware,
)
from app.api import auth, repositories, analysis, tunnel
from app.core.config import settings

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # let Rich do the level coloring
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("code_evolution_tracker")

# Global set to track background tasks
background_tasks = set()


# Custom JSON encoder for MongoDB ObjectId
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        # Match base class signature (parameter named 'o') to avoid
        # incompatible override warnings from type checkers.
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


# Custom JSON response that handles ObjectId
def custom_jsonable_encoder(obj, **kwargs):
    if isinstance(obj, dict):
        return {key: custom_jsonable_encoder(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [custom_jsonable_encoder(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return jsonable_encoder(obj, **kwargs)


def track_background_task(task):
    """Add task to tracking set and remove when done"""
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with proper task cleanup"""
    logger.info(
        "🚀 [LIFESPAN] Starting Code Evolution Tracker Backend... (PID: %s)",
        str(os.getpid()),
    )
    startup_time = datetime.utcnow().isoformat()
    logger.info(f"[LIFESPAN] Startup initiated at {startup_time}")

    try:
        # Initialize database

        logger.info("[LIFESPAN] Creating SQL tables...")
        try:
            create_tables()
            db_info = get_db_info()
            logger.info(f"📊 Database initialized: {db_info}")
        except Exception as e:
            logger.error(f"[LIFESPAN] ❌ Error initializing SQL DB: {e}")
            logger.error(traceback.format_exc())
            raise

        # Initialize enhanced MongoDB system (optional)

        logger.info("[LIFESPAN] Initializing enhanced MongoDB system...")
        try:
            from app.core.database import initialize_enhanced_database

            mongo_result = await initialize_enhanced_database()
            logger.info(
                f"🍃 MongoDB initialized: {mongo_result.get('mongodb_connected', False)}"
            )
        except Exception as e:
            logger.warning(f"[LIFESPAN] ⚠️  MongoDB initialization failed: {e}")
            logger.warning(
                "⚠️  The application will continue with SQLite only. Some features may be limited."
            )
            # Don't raise the exception - continue with SQLite only

        # Test all external connections

        logger.info("[LIFESPAN] Initializing AIService...")
        try:
            from app.core.service_manager import get_ai_service

            ai_service = get_ai_service()
            ai_status = ai_service.get_status()
            logger.info(f"🤖 AI Service Status: {ai_status}")
        except Exception as e:
            logger.error(f"[LIFESPAN] ❌ Error initializing AIService: {e}")
            logger.error(traceback.format_exc())
            raise

        # Schedule non-blocking Ollama discovery unless explicitly disabled
        try:
            # Disable Ollama discovery by default in environments where Ollama
            # is not available (CI, simple dev runs). Set DISABLE_OLLAMA_DISCOVERY=0
            # or 'false' to enable discovery explicitly.
            disable_ollama = os.getenv("DISABLE_OLLAMA_DISCOVERY", "1").lower() in (
                "1",
                "true",
                "yes",
            )
            if not disable_ollama:
                # Note: Multi-model service removed - using single model analysis only
                pass
                logger.info(
                    "🔁 Scheduled background Ollama discovery task (non-blocking startup)"
                )
            else:
                logger.info("🔕 Ollama discovery disabled via DISABLE_OLLAMA_DISCOVERY")
        except Exception as e:
            logger.warning(f"⚠️ Could not schedule Ollama discovery: {e}")
            logger.debug(traceback.format_exc())

        yield

    except Exception as e:
        logger.error(f"[LIFESPAN] ❌ Startup failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        shutdown_time = datetime.utcnow().isoformat()
        logger.info(
            f"[LIFESPAN] 🔄 Shutting down Code Evolution Tracker Backend... (PID: %s)",
            str(os.getpid()),
        )
        logger.info(f"[LIFESPAN] Shutdown initiated at {shutdown_time}")

        # Close enhanced database connections
        try:
            from app.core.database import close_enhanced_connections

            await close_enhanced_connections()
            logger.info("[LIFESPAN] ✅ Database connections closed")
        except Exception as e:
            logger.warning(f"[LIFESPAN] ⚠️ Error closing database connections: {e}")
            logger.warning(traceback.format_exc())

        # Cancel all background tasks
        if background_tasks:
            logger.info(
                f"[LIFESPAN] ⏹️  Cancelling {len(background_tasks)} background tasks..."
            )
            for task in background_tasks.copy():
                if not task.done():
                    task.cancel()

            # Wait for tasks to finish cancelling (with timeout)
            if background_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*background_tasks, return_exceptions=True),
                        timeout=10.0,
                    )
                    logger.info(
                        "[LIFESPAN] ✅ All background tasks cancelled successfully"
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "[LIFESPAN] ⚠️  Some background tasks didn't cancel within timeout"
                    )
                except Exception as e:
                    logger.warning(f"[LIFESPAN] ⚠️  Error during task cancellation: {e}")
                    logger.warning(traceback.format_exc())

        logger.info("[LIFESPAN] 👋 Shutdown complete")


# Create FastAPI app with enhanced configuration
disable_openapi = os.getenv("DISABLE_OPENAPI", "0") in ("1", "true", "True")

app = FastAPI(
    title="Code Evolution Tracker API",
    description="AI-powered repository analysis and pattern detection",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if disable_openapi else "/docs",
    redoc_url=None if disable_openapi else "/redoc",
    openapi_url=None if disable_openapi else "/openapi.json",
    # Disable automatic trailing slash redirects for consistency
    redirect_slashes=False,
)

# Set custom JSON encoder for ObjectId handling
import uvicorn
from fastapi.responses import JSONResponse


# Override the default JSON encoder to handle ObjectId
@app.middleware("http")
async def add_json_encoder(request, call_next):
    response = await call_next(request)
    return response


# Set the custom JSON encoder
import fastapi.encoders as fastapi_encoders

fastapi_encoders.jsonable_encoder = custom_jsonable_encoder

# Configure middleware in correct order
app.add_middleware(ConnectionLoggingMiddleware)
app.add_middleware(RequestValidationMiddleware)
EnhancedCORSMiddleware.configure(app)


# Manual CORS handler for additional safety
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        response = JSONResponse(content={})
        # Echo the request Origin when present instead of using a wildcard.
        # When Access-Control-Allow-Credentials is true the Origin must be
        # an explicit origin value (not '*').
        origin = request.headers.get("origin")
        response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
        )
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

    try:
        response = await call_next(request)
    except Exception as e:
        # Handle errors and still add CORS headers
        logger.error(f"CORS middleware caught error: {e}")
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)},
        )

    # Add CORS headers to all responses (including error responses)
    # Echo the Origin header when present so credentialed requests are allowed.
    origin = request.headers.get("origin")
    response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    )
    response.headers["Access-Control-Allow-Headers"] = (
        "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
    )
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Expose-Headers"] = "*"

    return response


# Global exception handler with detailed error info
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"💥 Unhandled exception: {type(exc).__name__}: {str(exc)}")
    logger.error(f"🌐 Request: {request.method} {request.url}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error occurred",
            "type": type(exc).__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
            "method": request.method,
            # Include error details in development
            **({"error": str(exc)} if getattr(settings, "DEBUG", False) else {}),
        },
    )


# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check with service status"""
    try:
        # Get current timestamp (Fix #2: Static timestamps)
        current_time = datetime.utcnow().isoformat()

        # Check legacy database
        db_info = get_db_info()

        # Check enhanced MongoDB database
        try:
            db_manager = get_enhanced_database_manager()
            if db_manager:
                mongo_health = await db_manager.health_check()
                mongodb_status = {
                    "connected": mongo_health.get("is_connected", False),
                    "response_time": mongo_health.get("response_time_ms", 0),
                    "collections": mongo_health.get("collections_count", 0),
                }
            else:
                mongodb_status = {
                    "connected": False,
                    "available": False,
                    "reason": "Not initialized",
                }
        except Exception as e:
            logger.warning(f"MongoDB health check failed: {e}")
            mongodb_status = {"connected": False, "error": str(e), "available": False}

        # Check AI service
        from app.core.service_manager import get_ai_service

        ai_service = get_ai_service()
        ai_status = ai_service.get_status()

        # In Railway environment, don't require Ollama to be available
        is_railway = os.getenv("RAILWAY_ENVIRONMENT")
        if is_railway and not ai_status.get("ollama_available", False):
            logger.info(
                "⚠️  Railway environment: Ollama not available, continuing without it"
            )

        return {
            "status": "healthy",
            "timestamp": current_time,  # Dynamic timestamp
            "version": "1.0.0",
            "background_tasks": len(background_tasks),  # Track active tasks
            "services": {
                "database_legacy": {
                    "connected": isinstance(db_info.get("table_count", 0), int)
                    and int(db_info.get("table_count", 0)) > 0,
                    "type": db_info.get("database_type", "Unknown"),
                    "tables": db_info.get("table_count", 0),
                },
                "database_mongodb": mongodb_status,
                "ai": {
                    "available": ai_status["ollama_available"],
                    "model": ai_status.get("ollama_model", "None"),
                },
                "cache": {
                    "type": db_info.get("cache_type", "Unknown"),
                    "connected": db_info.get("redis_connected", False),
                },
                "vector_db": {
                    "type": db_info.get("vector_db", "Unknown"),
                    "connected": db_info.get("chroma_connected", False),
                },
            },
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            },
        )


# Connection test endpoint
@app.get("/api/connection-test")
async def connection_test(request: Request):
    """Test endpoint to debug connection issues"""
    return {
        "message": "Connection successful",
        "timestamp": datetime.utcnow().isoformat(),
        "client": {
            "host": request.client.host if request.client else "unknown",
            "port": request.client.port if request.client else "unknown",
        },
        "headers": dict(request.headers),
    }


# IP detection endpoint for Railway
@app.get("/api/ip-check")
async def ip_check():
    """Get the outbound IP address for Railway deployment"""
    import requests

    try:
        # Use a service to get the outbound IP
        response = requests.get("https://api.ipify.org?format=json", timeout=10)
        if response.status_code == 200:
            ip_data = response.json()
            return {
                "outbound_ip": ip_data.get("ip"),
                "service": "ipify.org",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Use this IP in MongoDB Atlas Network Access",
            }
        else:
            return {"error": "Failed to get IP", "status_code": response.status_code}
    except Exception as e:
        return {"error": str(e), "message": "Failed to detect outbound IP"}


# Include routers
app.include_router(auth.router)
app.include_router(repositories.router)
app.include_router(analysis.router)
app.include_router(tunnel.router)  # Secure tunnel management


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Code Evolution Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
        access_log=True,
    )
