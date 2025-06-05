"""
MongoDB Configuration and Connection Management
Provides production-ready MongoDB setup with comprehensive error handling,
connection pooling, and monitoring capabilities.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from odmantic import AIOEngine
import asyncio
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


@dataclass
class MongoDBConfig:
    """MongoDB configuration settings with validation"""

    # Connection settings
    connection_string: str = field(default_factory=lambda: os.getenv("MONGODB_URL", ""))
    database_name: str = field(
        default_factory=lambda: os.getenv("MONGODB_DATABASE", "code_evolution_ai")
    )

    # Connection pool settings
    max_pool_size: int = field(
        default_factory=lambda: int(os.getenv("MONGODB_MAX_POOL_SIZE", "10"))
    )
    min_pool_size: int = field(
        default_factory=lambda: int(os.getenv("MONGODB_MIN_POOL_SIZE", "5"))
    )
    max_idle_time_ms: int = field(
        default_factory=lambda: int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "30000"))
    )

    # Timeout settings
    server_selection_timeout_ms: int = field(
        default_factory=lambda: int(
            os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
        )
    )
    connect_timeout_ms: int = field(
        default_factory=lambda: int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "10000"))
    )
    socket_timeout_ms: int = field(
        default_factory=lambda: int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "30000"))
    )

    # Write concern
    write_concern: str = field(
        default_factory=lambda: os.getenv("MONGODB_WRITE_CONCERN", "majority")
    )
    read_preference: str = field(
        default_factory=lambda: os.getenv("MONGODB_READ_PREFERENCE", "primary")
    )

    # Monitoring
    heartbeat_frequency_ms: int = field(
        default_factory=lambda: int(
            os.getenv("MONGODB_HEARTBEAT_FREQUENCY_MS", "10000")
        )
    )
    enable_monitoring: bool = field(
        default_factory=lambda: os.getenv("MONGODB_ENABLE_MONITORING", "true").lower()
        == "true"
    )

    def __post_init__(self) -> None:
        """Validate configuration after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate MongoDB configuration settings"""
        errors: List[str] = []

        if not self.connection_string:
            errors.append("MONGODB_URL is required")

        if not self.database_name:
            errors.append("MONGODB_DATABASE is required")

        if self.max_pool_size < self.min_pool_size:
            errors.append("max_pool_size must be >= min_pool_size")

        if self.server_selection_timeout_ms <= 0:
            errors.append("server_selection_timeout_ms must be positive")

        if self.connect_timeout_ms <= 0:
            errors.append("connect_timeout_ms must be positive")

        if errors:
            raise ValueError(f"MongoDB configuration errors: {'; '.join(errors)}")

    def get_client_options(self) -> Dict[str, Any]:
        """Get client connection options dictionary"""
        return {
            "maxPoolSize": self.max_pool_size,
            "minPoolSize": self.min_pool_size,
            "maxIdleTimeMS": self.max_idle_time_ms,
            "serverSelectionTimeoutMS": self.server_selection_timeout_ms,
            "connectTimeoutMS": self.connect_timeout_ms,
            "socketTimeoutMS": self.socket_timeout_ms,
            "w": self.write_concern,
            "readPreference": self.read_preference,
            "heartbeatFrequencyMS": self.heartbeat_frequency_ms,
            "retryWrites": True,
            "retryReads": True,
        }


@dataclass
class ConnectionStatus:
    """MongoDB connection status tracking"""

    is_connected: bool = False
    last_ping: Optional[datetime] = None
    connection_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    uptime: Optional[timedelta] = None
    server_info: Optional[Dict[str, Any]] = None


class MongoDBManager:
    """
    Enhanced MongoDB connection manager with health monitoring,
    automatic reconnection, and comprehensive error handling.
    """

    def __init__(self, config: Optional[MongoDBConfig] = None) -> None:
        """Initialize MongoDB manager with configuration"""
        self.config: MongoDBConfig = config or MongoDBConfig()
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.engine: Optional[AIOEngine] = None
        self.status: ConnectionStatus = ConnectionStatus()
        self._initialization_time: Optional[datetime] = None
        self._monitoring_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establish MongoDB connection with comprehensive error handling"""
        try:
            logger.info("🔄 Connecting to MongoDB...")

            # Create client with configured options
            client_options = self.config.get_client_options()
            self.client = AsyncIOMotorClient(
                self.config.connection_string, **client_options
            )

            # Test connection
            await self._test_connection()

            # Set up database and engine
            self.database = self.client[self.config.database_name]
            # Fixed: Use client parameter instead of motor_client for newer ODMantic versions
            self.engine = AIOEngine(
                client=self.client, database=self.config.database_name
            )

            # Update status
            self.status.is_connected = True
            self.status.connection_count += 1
            self.status.last_ping = datetime.utcnow()
            self._initialization_time = datetime.utcnow()

            # Start monitoring if enabled
            if self.config.enable_monitoring:
                await self._start_monitoring()

            logger.info("✅ MongoDB connected successfully")

        except Exception as e:
            self.status.error_count += 1
            self.status.last_error = str(e)
            self.status.last_error_time = datetime.utcnow()
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise ConnectionError(f"Failed to connect to MongoDB: {e}") from e

    async def _test_connection(self) -> None:
        """Test MongoDB connection and gather server information"""
        if not self.client:
            raise ConnectionError("MongoDB client not initialized")

        try:
            # Ping server
            await self.client.admin.command("ping")

            # Get server information
            server_info = await self.client.admin.command("buildInfo")
            self.status.server_info = {
                "version": server_info.get("version"),
                "gitVersion": server_info.get("gitVersion"),
                "platform": server_info.get("platform"),
                "maxBsonObjectSize": server_info.get("maxBsonObjectSize"),
            }

            logger.info(f"📊 MongoDB Server Version: {server_info.get('version')}")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            raise ConnectionError(f"MongoDB connection test failed: {e}") from e

    async def _start_monitoring(self) -> None:
        """Start background monitoring task"""
        if self._monitoring_task and not self._monitoring_task.done():
            return

        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🔍 MongoDB monitoring started")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for connection health"""
        while self.status.is_connected:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"⚠️  MongoDB monitoring error: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive MongoDB health check"""
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "is_connected": False,
            "ping_success": False,
            "response_time_ms": None,
            "database_accessible": False,
            "collections_count": 0,
            "server_status": {},
            "connection_pool": {},
            "error": None,
        }

        if not self.client or not self.database:
            health_data["error"] = "Client or database not initialized"
            return health_data

        try:
            # Measure ping response time
            start_time = datetime.utcnow()
            await self.client.admin.command("ping")
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            health_data.update(
                {
                    "is_connected": True,
                    "ping_success": True,
                    "response_time_ms": round(response_time, 2),
                }
            )

            # Test database access
            collections = await self.database.list_collection_names()
            health_data.update(
                {
                    "database_accessible": True,
                    "collections_count": len(collections),
                }
            )

            # Get server status
            server_status = await self.database.command("serverStatus")
            health_data["server_status"] = {
                "uptime": server_status.get("uptime"),
                "connections": server_status.get("connections", {}),
                "memory": server_status.get("mem", {}),
                "network": server_status.get("network", {}),
            }

            # Update internal status
            self.status.last_ping = datetime.utcnow()
            if self._initialization_time:
                self.status.uptime = datetime.utcnow() - self._initialization_time

            logger.debug(f"🔍 MongoDB health check successful - {response_time:.2f}ms")

        except Exception as e:
            health_data["error"] = str(e)
            self.status.error_count += 1
            self.status.last_error = str(e)
            self.status.last_error_time = datetime.utcnow()
            logger.warning(f"⚠️  MongoDB health check failed: {e}")

        return health_data

    async def get_status(self) -> Dict[str, Any]:
        """Get detailed connection status information"""
        return {
            "is_connected": self.status.is_connected,
            "last_ping": (
                self.status.last_ping.isoformat() if self.status.last_ping else None
            ),
            "connection_count": self.status.connection_count,
            "error_count": self.status.error_count,
            "last_error": self.status.last_error,
            "last_error_time": (
                self.status.last_error_time.isoformat()
                if self.status.last_error_time
                else None
            ),
            "uptime_seconds": (
                self.status.uptime.total_seconds() if self.status.uptime else None
            ),
            "server_info": self.status.server_info,
            "config": {
                "database_name": self.config.database_name,
                "max_pool_size": self.config.max_pool_size,
                "min_pool_size": self.config.min_pool_size,
                "monitoring_enabled": self.config.enable_monitoring,
            },
        }

    async def disconnect(self) -> None:
        """Gracefully disconnect from MongoDB"""
        try:
            # Stop monitoring
            if self._monitoring_task and not self._monitoring_task.done():
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass

            # Close client connection
            if self.client:
                self.client.close()
                await asyncio.sleep(0.1)  # Allow cleanup

            # Reset state
            self.status.is_connected = False
            self.client = None
            self.database = None
            self.engine = None

            logger.info("✅ MongoDB disconnected successfully")

        except Exception as e:
            logger.error(f"❌ Error during MongoDB disconnection: {e}")

    def get_database(self) -> AsyncIOMotorDatabase:
        """Get MongoDB database instance"""
        if self.database is None:
            raise ConnectionError("MongoDB database not available")
        return self.database

    def get_engine(self) -> AIOEngine:
        """Get ODMantic engine instance"""
        if self.engine is None:
            raise ConnectionError("ODMantic engine not available")
        return self.engine

    def get_client(self) -> AsyncIOMotorClient:
        """Get MongoDB client instance"""
        if self.client is None:
            raise ConnectionError("MongoDB client not available")
        return self.client

    @property
    def cache(self):
        """Get cache service instance"""
        from .database import get_cache

        return get_cache()


# Global MongoDB manager instance
mongodb_manager: Optional[MongoDBManager] = None


async def initialize_mongodb() -> MongoDBManager:
    """Initialize global MongoDB manager"""
    global mongodb_manager

    if mongodb_manager is None:
        config = MongoDBConfig()
        mongodb_manager = MongoDBManager(config)
        await mongodb_manager.connect()

    return mongodb_manager


async def get_mongodb_manager() -> MongoDBManager:
    """Get initialized MongoDB manager"""
    if mongodb_manager is None:
        raise ConnectionError(
            "MongoDB manager not initialized. Call initialize_mongodb() first."
        )
    return mongodb_manager


# Dependency functions for FastAPI
async def get_mongodb_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency: Get MongoDB database"""
    manager = await get_mongodb_manager()
    return manager.get_database()


async def get_odmantic_engine() -> AIOEngine:
    """FastAPI dependency: Get ODMantic engine"""
    manager = await get_mongodb_manager()
    return manager.get_engine()


async def cleanup_mongodb() -> None:
    """Cleanup MongoDB connections on application shutdown"""
    global mongodb_manager

    if mongodb_manager:
        await mongodb_manager.disconnect()
        mongodb_manager = None
