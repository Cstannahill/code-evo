# app/core/database.py - Redis + ChromaDB support with emoji logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
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
# SQLite setup (keeping this simple)
DATABASE_PATH = "code_evolution.db"
SQLITE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
load_dotenv(dotenv_path=env_path)
MONGODB_URL = os.getenv("MONGODB_URL", "your-cluster-connection-string")
mongodb_client = AsyncIOMotorClient(MONGODB_URL)
mongodb_db = mongodb_client.code_evolution_ai
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
try:
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    redis_client.ping()
    logger.info("✅ Redis connected successfully")
except Exception as e:
    logger.warning(f"⚠️  Redis not available: {e}")
    redis_client = None

# ChromaDB setup
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
    try:
        await mongodb_client.admin.command("ping")
        print("✅ MongoDB Atlas connection successful!")

        # Test insert
        test_doc = {"test": "multi-model-ai", "timestamp": datetime.utcnow()}
        result = await mongodb_db.test_collection.insert_one(test_doc)
        print(f"✅ Test document inserted: {result.inserted_id}")

        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
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


# Initialize CacheService
cache_service = CacheService()


# Dependency overrides
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cache():
    return cache_service


def get_chroma():
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


# Database lifecycle
def create_tables():
    """Create all database tables and log status"""
    try:
        logger.info(
            f"🚀 Initializing SQLite database at: {os.path.abspath(DATABASE_PATH)}"
        )

        # Import all models to ensure they're registered with Base
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

        # Now create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")

        # List all tables created
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"📊 Created tables: {', '.join(tables)}")

        db_size = os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0
        logger.info(f"📊 Database size: {db_size} bytes")

        cache_type = "Redis" if redis_client else "Memory"
        vector_db = "ChromaDB" if chroma_client else "Disabled"
        logger.info(f"🗄️  Cache service: {cache_type}")
        logger.info(f"🔍 Vector DB: {vector_db}")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise


def get_db_info():
    """Return database diagnostics"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            )
            table_count = result.scalar()
            cache_type = "Redis" if redis_client else "Memory"
            vector_db = "ChromaDB" if chroma_client else "Disabled"

        return {
            "database_path": os.path.abspath(DATABASE_PATH),
            "database_size": (
                os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0
            ),
            "table_count": table_count,
            "database_type": "SQLite",
            "cache_type": cache_type,
            "vector_db": vector_db,
            "redis_connected": bool(redis_client),
            "chroma_connected": bool(chroma_client),
        }
    except Exception as e:
        logger.error(f"❌ Error getting database info: {e}")
        return {"error": str(e)}
