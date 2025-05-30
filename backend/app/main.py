from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from rich.logging import RichHandler
import sys
import asyncio
from datetime import datetime
import traceback
from app.models.repository import (
    Repository,
    Commit,
    FileChange,
    Technology,
    Pattern,
    PatternOccurrence,
    AnalysisSession,
    AIModel,
    AIAnalysisResult,
    ModelComparison,
    ModelBenchmark,
)
from app.core.database import create_tables, engine, get_db_info  # Legacy SQLAlchemy
from app.core.database2_enhanced import (
    get_enhanced_database_manager,
)  # Enhanced MongoDB
from app.core.middleware import (
    EnhancedCORSMiddleware,
    ConnectionLoggingMiddleware,
    RequestValidationMiddleware,
)
from app.api import auth, repositories, analysis
from app.api import repositories_mongodb  # New MongoDB-based API
from app.api import analysis_mongodb  # New MongoDB-based Analysis API
from app.core.config import settings
from app.api.multi_model_analysis import router as multi_model_router
from app.api.multi_model_test import router as test_router

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


def track_background_task(task):
    """Add task to tracking set and remove when done"""
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with proper task cleanup"""
    logger.info("🚀 Starting Code Evolution Tracker Backend...")

    try:
        # Initialize database
        create_tables()
        db_info = get_db_info()
        logger.info(f"📊 Database initialized: {db_info}")

        # Test all external connections
        from app.services.ai_service import AIService

        ai_service = AIService()
        ai_status = ai_service.get_status()
        logger.info(f"🤖 AI Service Status: {ai_status}")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        logger.info("🔄 Shutting down Code Evolution Tracker Backend...")

        # Cancel all background tasks
        if background_tasks:
            logger.info(f"⏹️  Cancelling {len(background_tasks)} background tasks...")
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
                    logger.info("✅ All background tasks cancelled successfully")
                except asyncio.TimeoutError:
                    logger.warning(
                        "⚠️  Some background tasks didn't cancel within timeout"
                    )
                except Exception as e:
                    logger.warning(f"⚠️  Error during task cancellation: {e}")

        logger.info("👋 Shutdown complete")


# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="Code Evolution Tracker API",
    description="AI-powered repository analysis and pattern detection",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure middleware in correct order
app.add_middleware(ConnectionLoggingMiddleware)
app.add_middleware(RequestValidationMiddleware)
EnhancedCORSMiddleware.configure(app)


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
            **({"error": str(exc)} if settings.DEBUG else {}),
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
            mongo_health = await db_manager.health_check()
            mongodb_status = {
                "connected": mongo_health.get("mongodb", {}).get("connected", False),
                "response_time": mongo_health.get("mongodb", {}).get(
                    "response_time", 0
                ),
                "collections": mongo_health.get("mongodb", {}).get("collections", 0),
            }
        except Exception as e:
            logger.warning(f"MongoDB health check failed: {e}")
            mongodb_status = {"connected": False, "error": str(e)}

        # Check AI service
        from app.services.ai_service import AIService

        ai_service = AIService()
        ai_status = ai_service.get_status()

        return {
            "status": "healthy",
            "timestamp": current_time,  # Dynamic timestamp
            "version": "1.0.0",
            "background_tasks": len(background_tasks),  # Track active tasks
            "services": {
                "database_legacy": {
                    "connected": db_info.get("table_count", 0) > 0,
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


# Include routers
app.include_router(auth.router)
app.include_router(
    repositories.router
)  # Keep old SQLAlchemy API for backward compatibility
app.include_router(repositories_mongodb.router, prefix="/api/v2")  # New MongoDB API
app.include_router(
    analysis.router
)  # Keep old SQLAlchemy API for backward compatibility
app.include_router(
    analysis_mongodb.router, prefix="/api/v2"
)  # New MongoDB Analysis API
app.include_router(multi_model_router)
app.include_router(test_router)


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
