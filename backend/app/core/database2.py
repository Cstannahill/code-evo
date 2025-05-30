from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
import logging
import os
import redis
import chromadb
from chromadb.config import Settings as ChromaSettings
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# MongoDB setup (primary database)
MONGODB_URL = os.getenv("MONGODB_URL", "your-cluster-connection-string")
mongodb_client = AsyncIOMotorClient(MONGODB_URL)
mongodb_db = mongodb_client.code_evolution_ai

# ODMantic engine for document modeling (optional - provides Pydantic-like models)
engine = AIOEngine(motor_client=mongodb_client, database="code_evolution_ai")

# Redis setup (caching)
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    redis_client.ping()
    logger.info("✅ Redis connected successfully")
except Exception as e:
    logger.warning(f"⚠️  Redis not available: {e}")
    redis_client = None

# ChromaDB setup (vector database)
try:
    chroma_client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
    )
    logger.info("✅ ChromaDB initialized successfully")
except Exception as e:
    logger.warning(f"⚠️  ChromaDB not available: {e}")
    chroma_client = None

# Fallback in-memory cache
_memory_cache = {}


async def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    try:
        await mongodb_client.admin.command("ping")
        logger.info("✅ MongoDB Atlas connection successful!")

        # Test insert
        test_doc = {"test": "multi-model-ai", "timestamp": datetime.utcnow()}
        result = await mongodb_db.test_collection.insert_one(test_doc)
        logger.info(f"✅ Test document inserted: {result.inserted_id}")

        # Clean up test document
        await mongodb_db.test_collection.delete_one({"_id": result.inserted_id})

        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return False


class CacheService:
    """Unified cache service: Redis preferred, memory fallback"""

    def __init__(self):
        self.redis = redis_client
        self.memory = _memory_cache

    def get(self, key: str):
        if self.redis:
            try:
                return self.redis.get(key)
            except:
                pass
        return self.memory.get(key)

    def set(self, key: str, value: str, ttl: int = 3600):
        if self.redis:
            try:
                self.redis.setex(key, ttl, value)
                return
            except:
                pass
        self.memory[key] = value

    def delete(self, key: str):
        if self.redis:
            try:
                self.redis.delete(key)
            except:
                pass
        self.memory.pop(key, None)

    def ping(self):
        if self.redis:
            try:
                return self.redis.ping()
            except:
                pass
        return True


# Initialize services
cache_service = CacheService()


# Database dependency functions
async def get_mongodb():
    """Get MongoDB database instance"""
    return mongodb_db


async def get_engine():
    """Get ODMantic engine for document operations"""
    return engine


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


# Database lifecycle functions
async def create_indexes():
    """Create MongoDB indexes for better performance"""
    try:
        logger.info("🚀 Creating MongoDB indexes...")

        # Example indexes - adjust based on your models
        await mongodb_db.repositories.create_index("url", unique=True)
        await mongodb_db.repositories.create_index([("owner", 1), ("name", 1)])
        await mongodb_db.commits.create_index("repository_id")
        await mongodb_db.commits.create_index("timestamp")
        await mongodb_db.file_changes.create_index("commit_id")
        await mongodb_db.analysis_sessions.create_index("created_at")
        await mongodb_db.ai_analysis_results.create_index("session_id")

        logger.info("✅ MongoDB indexes created successfully")

    except Exception as e:
        logger.error(f"❌ Error creating MongoDB indexes: {e}")
        raise


async def get_db_info():
    """Return database diagnostics"""
    try:
        # Get MongoDB stats
        stats = await mongodb_db.command("dbStats")
        collections = await mongodb_db.list_collection_names()

        cache_type = "Redis" if redis_client else "Memory"
        vector_db = "ChromaDB" if chroma_client else "Disabled"

        return {
            "database_name": mongodb_db.name,
            "database_size": stats.get("dataSize", 0),
            "collection_count": len(collections),
            "collections": collections,
            "database_type": "MongoDB",
            "cache_type": cache_type,
            "vector_db": vector_db,
            "redis_connected": bool(redis_client),
            "chroma_connected": bool(chroma_client),
            "mongodb_connected": True,
        }
    except Exception as e:
        logger.error(f"❌ Error getting database info: {e}")
        return {"error": str(e), "mongodb_connected": False}


async def close_connections():
    """Close all database connections gracefully"""
    try:
        if mongodb_client:
            mongodb_client.close()
            logger.info("✅ MongoDB connection closed")

        if redis_client:
            redis_client.close()
            logger.info("✅ Redis connection closed")

    except Exception as e:
        logger.error(f"❌ Error closing connections: {e}")


# Initialize database on import
async def initialize_database():
    """Initialize database with indexes and test connections"""
    try:
        # Test MongoDB connection
        success = await test_mongodb_connection()
        if not success:
            raise Exception("MongoDB connection failed")

        # Create indexes
        await create_indexes()

        # Log system status
        cache_type = "Redis" if redis_client else "Memory"
        vector_db = "ChromaDB" if chroma_client else "Disabled"
        logger.info(f"🗄️  Primary DB: MongoDB")
        logger.info(f"🗄️  Cache service: {cache_type}")
        logger.info(f"🔍 Vector DB: {vector_db}")

    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise
