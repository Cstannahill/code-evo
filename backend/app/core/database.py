# app/core/database.py - Fixed with Redis + ChromaDB support
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os
import redis
import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

# SQLite setup (keeping this simple)
DATABASE_PATH = "code_evolution.db"
SQLITE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup (re-enabled!)
try:
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis connected successfully")
except Exception as e:
    logger.warning(f"⚠️  Redis not available: {e}")
    redis_client = None

# ChromaDB setup (fixed!)
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


class CacheService:
    """Unified cache service that prefers Redis but falls back to memory"""

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


# Dependencies
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
        logger.warning("ChromaDB not available")
        return None

    try:
        return chroma_client.get_or_create_collection(
            name=name, metadata={"description": f"Collection for {name}"}
        )
    except Exception as e:
        logger.error(f"Error creating collection {name}: {e}")
        return None


# Database initialization
def create_tables():
    """Create all database tables"""
    try:
        logger.info(
            f"Initializing SQLite database at: {os.path.abspath(DATABASE_PATH)}"
        )
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")

        # Log database info
        db_size = os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0
        logger.info(f"📊 Database size: {db_size} bytes")

        # Test services
        logger.info(f"🗄️  Cache service: {'Redis' if redis_client else 'Memory'}")
        logger.info(f"🔍 Vector DB: {'ChromaDB' if chroma_client else 'Disabled'}")

    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise


def get_db_info():
    """Get database information for debugging"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
            )
            table_count = result.scalar()

            return {
                "database_path": os.path.abspath(DATABASE_PATH),
                "database_size": (
                    os.path.getsize(DATABASE_PATH)
                    if os.path.exists(DATABASE_PATH)
                    else 0
                ),
                "table_count": table_count,
                "database_type": "SQLite",
                "cache_type": "Redis" if redis_client else "Memory",
                "vector_db": "ChromaDB" if chroma_client else "Disabled",
                "redis_connected": bool(redis_client),
                "chroma_connected": bool(chroma_client),
            }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {"error": str(e)}
