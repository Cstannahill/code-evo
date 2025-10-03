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

    # Railway-specific settings
    is_railway_env: bool = field(
        default_factory=lambda: os.getenv("RAILWAY_ENVIRONMENT") is not None
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

    # TLS/SSL configuration
    tls_enabled: bool = field(
        default_factory=lambda: os.getenv("MONGODB_TLS", "false").lower() == "true"
    )
    tls_allow_invalid_certificates: bool = field(
        default_factory=lambda: os.getenv(
            "MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", "false"
        ).lower()
        == "true"
    )
    tls_ca_file: Optional[str] = field(
        default_factory=lambda: os.getenv("MONGODB_TLS_CA_FILE")
    )
    tls_disable_ocsp_endpoint_check: bool = field(
        default_factory=lambda: os.getenv("MONGODB_TLS_DISABLE_OCSP", "false").lower()
        in {"1", "true", "yes"}
    )
    app_name: Optional[str] = field(
        default_factory=lambda: os.getenv("MONGODB_APP_NAME")
    )

    def __post_init__(self) -> None:
        """Validate configuration after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate MongoDB configuration settings"""
        errors: List[str] = []

        # Only validate if connection_string is provided
        if self.connection_string and not self.database_name:
            errors.append("MONGODB_DATABASE is required when MONGODB_URL is provided")

        if self.max_pool_size < self.min_pool_size:
            errors.append("max_pool_size must be >= min_pool_size")

        if self.server_selection_timeout_ms <= 0:
            errors.append("server_selection_timeout_ms must be positive")

        if self.connect_timeout_ms <= 0:
            errors.append("connect_timeout_ms must be positive")

        if (
            self.tls_enabled
            and self.tls_allow_invalid_certificates
            and self.tls_ca_file
        ):
            errors.append(
                "tls_allow_invalid_certificates should not be combined with tls_ca_file; remove one of the settings"
            )

        if self.tls_enabled and self.tls_ca_file:
            ca_path = Path(self.tls_ca_file)
            if not ca_path.is_file():
                errors.append(
                    f"TLS CA file not found at '{self.tls_ca_file}'. Ensure the certificate bundle is present before starting the service."
                )

        if errors:
            raise ValueError(f"MongoDB configuration errors: {'; '.join(errors)}")

    def get_client_options(self) -> Dict[str, Any]:
        """Compile optional PyMongo client keyword arguments based on configuration."""
        options: Dict[str, Any] = {}

        if self.tls_enabled:
            options["tls"] = True

        if self.tls_allow_invalid_certificates:
            options["tlsAllowInvalidCertificates"] = True

        if self.tls_ca_file:
            options["tlsCAFile"] = self.tls_ca_file

        if self.tls_disable_ocsp_endpoint_check:
            options["tlsDisableOCSPEndpointCheck"] = True

        if self.app_name:
            options["appname"] = self.app_name

        # Propagate timeout and pool configuration to the Motor client so that
        # pymongo surfaces detailed server selection errors instead of silent cancellations.
        options["serverSelectionTimeoutMS"] = self.server_selection_timeout_ms
        options["connectTimeoutMS"] = self.connect_timeout_ms
        options["socketTimeoutMS"] = self.socket_timeout_ms
        options["maxPoolSize"] = self.max_pool_size
        options["minPoolSize"] = self.min_pool_size
        options["maxIdleTimeMS"] = self.max_idle_time_ms

        return options


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
            # Check if connection string is provided
            if (
                not self.config.connection_string
                or self.config.connection_string.strip() == ""
            ):
                logger.warning(
                    "⚠️  MongoDB connection string not provided, skipping MongoDB initialization"
                )
                self.client = None
                self.database = None
                self.engine = None
                return

            logger.info("🔄 Connecting to MongoDB...")
            sanitized_uri = self._sanitize_connection_string(
                self.config.connection_string
            )
            logger.info("🔗 MongoDB URI (sanitized): %s", sanitized_uri)

            # Log Railway environment detection
            if self.config.is_railway_env:
                logger.info(
                    "🚂 Railway environment detected - using Railway-optimized connection settings"
                )

            # Create client with configured options
            client_options = self.config.get_client_options()
            if client_options:
                sanitized_options = {
                    key: ("<hidden>" if "password" in key.lower() else value)
                    for key, value in client_options.items()
                }
                logger.info("🔐 Applying MongoDB client options: %s", sanitized_options)

            # Standard single attempt using only the connection string.
            def create_client() -> AsyncIOMotorClient:
                return AsyncIOMotorClient(
                    self.config.connection_string, **client_options
                )

            connection_attempts = [create_client]

            connection_successful = False
            last_error = None

            for i, attempt in enumerate(connection_attempts):
                try:
                    logger.info(
                        f"🔄 Attempting MongoDB connection (strategy {i+1}/{len(connection_attempts)})..."
                    )
                    self.client = attempt()

                    # Test connection; rely on PyMongo timeouts so any
                    # ServerSelectionTimeoutError surfaces with diagnostic details.
                    await self._test_connection()
                    connection_successful = True
                    logger.info(
                        f"✅ MongoDB connected successfully with strategy {i+1}"
                    )
                    break

                except Exception as e:
                    last_error = e
                    logger.warning(f"⚠️  Connection strategy {i+1} failed: {e}")
                    if self.client:
                        try:
                            self.client.close()
                        except:
                            pass
                        self.client = None
                    continue

            if not connection_successful:
                raise last_error or ConnectionError("All connection strategies failed")

            # Set up database and engine
            if self.client is None:
                raise ConnectionError(
                    "MongoDB client not initialized after successful connection"
                )
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
            self.status.last_error = repr(e)
            self.status.last_error_time = datetime.utcnow()
            logger.exception("❌ MongoDB connection failed: %s", e)

            if isinstance(e, ServerSelectionTimeoutError):
                if getattr(e, "args", None):
                    logger.error("❌ Server selection args: %s", e.args)
                details = getattr(e, "details", None)
                if details:
                    logger.error("❌ Server selection details: %s", details)
                if self.client:
                    try:
                        logger.error(
                            "❌ Known MongoDB nodes at failure: %s", self.client.nodes
                        )
                    except Exception as node_err:  # pragma: no cover - diagnostic aid
                        logger.debug(
                            "ℹ️ Unable to read MongoDB nodes during failure: %s",
                            node_err,
                        )

            # For SSL/TLS errors, provide more helpful error message
            if "SSL" in str(e) or "TLS" in str(e) or "handshake" in str(e).lower():
                logger.error(
                    "💡 SSL/TLS connection issue detected. This is common with MongoDB Atlas in Railway."
                )
                logger.error(
                    "💡 Consider checking your MongoDB connection string and network access settings."
                )

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

        if self.client is None or self.database is None:
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

    def get_database(self) -> Optional[AsyncIOMotorDatabase]:
        """Get MongoDB database instance"""
        if self.database is None:
            logger.warning("⚠️  MongoDB database not available (MongoDB not configured)")
            return None
        return self.database

    def get_engine(self) -> Optional[AIOEngine]:
        """Get ODMantic engine instance"""
        if self.engine is None:
            logger.warning("⚠️  ODMantic engine not available (MongoDB not configured)")
            return None
        return self.engine

    def get_client(self) -> Optional[AsyncIOMotorClient]:
        """Get MongoDB client instance"""
        if self.client is None:
            logger.warning("⚠️  MongoDB client not available (MongoDB not configured)")
            return None
        return self.client

    @property
    def cache(self):
        """Get cache service instance"""
        from .database import get_cache

        return get_cache()

    @staticmethod
    def _sanitize_connection_string(uri: str) -> str:
        """Hide credentials in MongoDB connection URI for safe logging."""
        if not uri or "://" not in uri:
            return uri

        scheme, rest = uri.split("://", 1)
        if "@" not in rest:
            return uri

        _, host_part = rest.split("@", 1)
        return f"{scheme}://<credentials-hidden>@{host_part}"


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
    db = manager.get_database()
    if db is None:
        raise ConnectionError("MongoDB database not available")
    return db


async def get_odmantic_engine() -> AIOEngine:
    """FastAPI dependency: Get ODMantic engine"""
    manager = await get_mongodb_manager()
    engine = manager.get_engine()
    if engine is None:
        raise ConnectionError("ODMantic engine not available")
    return engine


async def cleanup_mongodb() -> None:
    """Cleanup MongoDB connections on application shutdown"""
    global mongodb_manager

    if mongodb_manager:
        await mongodb_manager.disconnect()
        mongodb_manager = None
