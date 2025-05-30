"""
Enhanced MongoDB Database Configuration
Production-ready MongoDB setup with comprehensive monitoring, indexing, and error handling.
Uses the new MongoDB configuration system with health checks and performance monitoring.
"""

import logging
import os
import redis
import chromadb
from chromadb.config import Settings as ChromaSettings
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Dict, Any

# Import enhanced MongoDB components
from .mongodb_config import (
    MongoDBManager,
    MongoDBConfig,
    initialize_mongodb,
    get_mongodb_manager,
)
from .mongodb_indexes import MongoDBIndexManager
from .mongodb_monitoring import MongoDBMonitor, HealthCheckResult

logger = logging.getLogger(__name__)
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# Global MongoDB components
mongodb_manager: Optional[MongoDBManager] = None
index_manager: Optional[MongoDBIndexManager] = None
monitor: Optional[MongoDBMonitor] = None

# Redis setup (caching)
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD") or None,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
    )
    redis_client.ping()
    logger.info("✅ Redis connected successfully")
except Exception as e:
    logger.warning(f"⚠️  Redis not available: {e}")
    redis_client = None

# ChromaDB setup (vector database)
try:
    chroma_db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    chroma_client = chromadb.PersistentClient(
        path=chroma_db_path,
        settings=ChromaSettings(
            anonymized_telemetry=os.getenv(
                "CHROMA_ANONYMIZED_TELEMETRY", "false"
            ).lower()
            == "true",
            allow_reset=True,
        ),
    )
    logger.info("✅ ChromaDB initialized successfully")
except Exception as e:
    logger.warning(f"⚠️  ChromaDB not available: {e}")
    chroma_client = None

# Fallback in-memory cache
_memory_cache = {}


class CacheService:
    """Unified cache service: Redis preferred, memory fallback"""

    def __init__(self):
        self.redis = redis_client
        self.memory = _memory_cache

    def get(self, key: str):
        if self.redis:
            try:
                return self.redis.get(key)
            except Exception:
                pass
        return self.memory.get(key)

    def set(self, key: str, value: str, ttl: int = 3600):
        if self.redis:
            try:
                self.redis.setex(key, ttl, value)
                return
            except Exception:
                pass
        self.memory[key] = value

    def delete(self, key: str):
        if self.redis:
            try:
                self.redis.delete(key)
            except Exception:
                pass
        self.memory.pop(key, None)

    def ping(self):
        if self.redis:
            try:
                return self.redis.ping()
            except Exception:
                pass
        return True


# Initialize services
cache_service = CacheService()


# Database dependency functions for FastAPI
async def get_mongodb():
    """Get MongoDB database instance"""
    global mongodb_manager
    if mongodb_manager is None:
        mongodb_manager = await initialize_mongodb()
    return mongodb_manager.get_database()


async def get_engine():
    """Get ODMantic engine for document operations"""
    global mongodb_manager
    if mongodb_manager is None:
        mongodb_manager = await initialize_mongodb()
    return mongodb_manager.get_engine()


def get_cache():
    """Get cache service instance"""
    return cache_service


def get_chroma():
    """Get ChromaDB client"""
    return chroma_client


def get_collection(name: str):
    """Get or create a ChromaDB collection"""
    if not chroma_client:
        logger.warning("⚠️  ChromaDB not available")
        return None
    try:
        return chroma_client.get_or_create_collection(
            name=name, metadata={"description": f"Collection for {name}"}
        )
    except Exception as e:
        logger.error(f"❌ Error creating collection '{name}': {e}")
        return None


# Enhanced database initialization and management
async def initialize_enhanced_database() -> Dict[str, Any]:
    """
    Initialize enhanced MongoDB system with comprehensive setup

    Returns:
        Dict with initialization results and status
    """
    global mongodb_manager, index_manager, monitor

    initialization_result = {
        "mongodb_connected": False,
        "indexes_created": False,
        "monitoring_started": False,
        "errors": [],
        "components": {},
        "health_check": None,
    }

    try:
        logger.info("🚀 Starting enhanced MongoDB initialization...")

        # 1. Initialize MongoDB manager
        mongodb_manager = await initialize_mongodb()
        initialization_result["mongodb_connected"] = True
        logger.info("✅ MongoDB manager initialized")

        # 2. Initialize index manager and create indexes
        database = mongodb_manager.get_database()
        index_manager = MongoDBIndexManager(database)

        index_results = await index_manager.create_all_indexes()
        initialization_result["indexes_created"] = (
            index_results["successful_indexes"] > 0
        )
        initialization_result["index_results"] = index_results
        logger.info(
            f"✅ Created {index_results['successful_indexes']}/{index_results['total_indexes']} indexes"
        )

        # 3. Initialize monitoring system
        monitor = MongoDBMonitor(database)
        await monitor.start_continuous_monitoring(
            interval_seconds=int(os.getenv("HEALTH_CHECK_INTERVAL_SECONDS", "60"))
        )
        initialization_result["monitoring_started"] = True
        logger.info("✅ MongoDB monitoring started")

        # 4. Perform initial health check
        health_result = await monitor.comprehensive_health_check()
        initialization_result["health_check"] = health_result.to_dict()
        logger.info(
            f"✅ Initial health check completed: {health_result.overall_status.value}"
        )

        # 5. Log system status
        status = await mongodb_manager.get_status()
        initialization_result["components"] = {
            "mongodb": status,
            "redis": {"connected": bool(redis_client)},
            "chromadb": {"connected": bool(chroma_client)},
            "cache_service": {"type": "Redis" if redis_client else "Memory"},
        }

        logger.info("🗄️  Enhanced MongoDB system initialized successfully")
        logger.info(f"📊 Database: {status['config']['database_name']}")
        logger.info(f"🔍 Monitoring: {status['config']['monitoring_enabled']}")
        logger.info(f"💾 Cache: {'Redis' if redis_client else 'Memory'}")
        logger.info(f"🔍 Vector DB: {'ChromaDB' if chroma_client else 'Disabled'}")

    except Exception as e:
        error_msg = f"Enhanced database initialization failed: {e}"
        logger.error(f"❌ {error_msg}")
        initialization_result["errors"].append(error_msg)
        raise

    return initialization_result


async def get_database_health() -> Dict[str, Any]:
    """
    Get comprehensive database health status

    Returns:
        Dict with health information across all database components
    """
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "unknown",
        "components": {},
        "errors": [],
    }

    try:
        # MongoDB health check
        if monitor:
            mongodb_health = await monitor.comprehensive_health_check()
            health_status["components"]["mongodb"] = mongodb_health.to_dict()
            health_status["overall_status"] = mongodb_health.overall_status.value
        else:
            health_status["components"]["mongodb"] = {"status": "not_initialized"}
            health_status["errors"].append("MongoDB monitor not initialized")

        # Redis health check
        redis_status = "healthy" if cache_service.ping() else "unhealthy"
        health_status["components"]["redis"] = {
            "status": redis_status,
            "type": "Redis" if redis_client else "Memory fallback",
        }

        # ChromaDB health check
        chromadb_status = "healthy" if chroma_client else "disabled"
        health_status["components"]["chromadb"] = {"status": chromadb_status}

        # Index manager status
        if index_manager:
            index_status = await index_manager.get_index_status()
            health_status["components"]["indexes"] = {
                "total_collections": index_status["total_collections"],
                "total_indexes": index_status["total_indexes"],
                "missing_indexes": len(index_status["missing_indexes"]),
                "extra_indexes": len(index_status["extra_indexes"]),
            }

    except Exception as e:
        error_msg = f"Health check failed: {e}"
        health_status["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")

    return health_status


async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get database performance metrics

    Returns:
        Dict with performance data
    """
    if not monitor:
        return {"error": "MongoDB monitor not initialized"}

    try:
        return monitor.get_performance_summary(minutes=30)
    except Exception as e:
        logger.error(f"❌ Failed to get performance metrics: {e}")
        return {"error": str(e)}


async def rebuild_indexes() -> Dict[str, Any]:
    """
    Rebuild all MongoDB indexes

    Returns:
        Dict with rebuild results
    """
    if not index_manager:
        return {"error": "Index manager not initialized"}

    try:
        logger.info("🔄 Starting index rebuild...")

        # Drop existing indexes
        drop_results = await index_manager.drop_all_indexes(confirm=True)

        # Recreate indexes
        create_results = await index_manager.create_all_indexes()

        return {
            "drop_results": drop_results,
            "create_results": create_results,
            "success": create_results["successful_indexes"] > 0,
        }

    except Exception as e:
        error_msg = f"Index rebuild failed: {e}"
        logger.error(f"❌ {error_msg}")
        return {"error": error_msg}


async def export_health_report() -> Dict[str, Any]:
    """
    Export comprehensive health and performance report

    Returns:
        Dict with complete system report
    """
    report = {
        "report_timestamp": datetime.utcnow().isoformat(),
        "system_health": await get_database_health(),
        "performance_metrics": await get_performance_metrics(),
        "errors": [],
    }

    try:
        if monitor:
            detailed_report = await monitor.export_health_report(include_history=True)
            report["detailed_monitoring"] = detailed_report

        if index_manager:
            index_status = await index_manager.get_index_status()
            report["index_status"] = index_status

        if mongodb_manager:
            connection_status = await mongodb_manager.get_status()
            report["connection_status"] = connection_status

    except Exception as e:
        error_msg = f"Report generation failed: {e}"
        report["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")

    return report


async def close_enhanced_connections():
    """Close all enhanced database connections gracefully"""
    global mongodb_manager, monitor

    try:
        # Stop monitoring
        if monitor:
            await monitor.stop_continuous_monitoring()
            logger.info("✅ MongoDB monitoring stopped")

        # Close MongoDB connections
        if mongodb_manager:
            await mongodb_manager.disconnect()
            logger.info("✅ MongoDB connections closed")

        # Close Redis connection
        if redis_client:
            redis_client.close()
            logger.info("✅ Redis connection closed")

        # Reset globals
        mongodb_manager = None
        monitor = None

    except Exception as e:
        logger.error(f"❌ Error closing enhanced connections: {e}")


# Backward compatibility functions (for existing code)
async def test_mongodb_connection():
    """Test MongoDB connection (backward compatibility)"""
    try:
        if mongodb_manager:
            health_result = (
                await monitor.comprehensive_health_check() if monitor else None
            )
            return health_result and health_result.overall_status.value in [
                "healthy",
                "warning",
            ]
        return False
    except Exception as e:
        logger.error(f"❌ MongoDB connection test failed: {e}")
        return False


async def create_indexes():
    """Create MongoDB indexes (backward compatibility)"""
    if index_manager:
        results = await index_manager.create_all_indexes()
        return results["successful_indexes"] > 0
    return False


async def get_db_info():
    """Return database diagnostics (backward compatibility)"""
    try:
        health_status = await get_database_health()

        # Convert to old format for compatibility
        return {
            "database_name": (
                mongodb_manager.config.database_name if mongodb_manager else "unknown"
            ),
            "database_type": "MongoDB Enhanced",
            "cache_type": "Redis" if redis_client else "Memory",
            "vector_db": "ChromaDB" if chroma_client else "Disabled",
            "mongodb_connected": health_status["components"]
            .get("mongodb", {})
            .get("overall_status")
            == "healthy",
            "redis_connected": bool(redis_client),
            "chroma_connected": bool(chroma_client),
            "health_status": health_status,
        }
    except Exception as e:
        logger.error(f"❌ Error getting database info: {e}")
        return {"error": str(e), "mongodb_connected": False}


async def close_connections():
    """Close all database connections gracefully (backward compatibility)"""
    await close_enhanced_connections()


# Use enhanced initialization as the default
async def initialize_database():
    """Initialize database with enhanced system (backward compatibility)"""
    return await initialize_enhanced_database()
