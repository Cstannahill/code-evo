"""
Comprehensive MongoDB Indexing Strategy
Defines and manages all database indexes for optimal query performance.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure

logger = logging.getLogger(__name__)


class IndexDefinition:
    """MongoDB index definition with metadata"""

    def __init__(
        self,
        name: str,
        keys: List[Tuple[str, int]],
        unique: bool = False,
        sparse: bool = False,
        background: bool = True,
        partial_filter: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None,
        description: str = "",
    ):
        """
        Initialize index definition

        Args:
            name: Index name
            keys: Index key specification [(field, direction), ...]
            unique: Whether index should enforce uniqueness
            sparse: Whether to skip documents missing indexed fields
            background: Whether to build index in background
            partial_filter: Partial filter expression
            ttl_seconds: TTL for automatic document expiration
            description: Human-readable description
        """
        self.name = name
        self.keys = keys
        self.unique = unique
        self.sparse = sparse
        self.background = background
        self.partial_filter = partial_filter
        self.ttl_seconds = ttl_seconds
        self.description = description

    def to_index_model(self) -> IndexModel:
        """Convert to pymongo IndexModel"""
        options = {
            "name": self.name,
            "unique": self.unique,
            "sparse": self.sparse,
            "background": self.background,
        }

        if self.partial_filter:
            options["partialFilterExpression"] = self.partial_filter

        if self.ttl_seconds:
            options["expireAfterSeconds"] = self.ttl_seconds

        return IndexModel(self.keys, **options)


class CollectionIndexes:
    """Index definitions for a specific collection"""

    def __init__(self, collection_name: str, indexes: List[IndexDefinition]):
        """
        Initialize collection indexes

        Args:
            collection_name: Name of the collection
            indexes: List of index definitions
        """
        self.collection_name = collection_name
        self.indexes = indexes

    def get_index_models(self) -> List[IndexModel]:
        """Get list of IndexModel objects"""
        return [index.to_index_model() for index in self.indexes]


class MongoDBIndexManager:
    """
    MongoDB index management with comprehensive strategy for
    the Code Evolution Tracker application.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """Initialize index manager with database instance"""
        self.database = database
        self._index_definitions = self._define_all_indexes()

    def _define_all_indexes(self) -> Dict[str, CollectionIndexes]:
        """Define comprehensive indexing strategy for all collections"""

        return {
            # Repository indexes
            "repositories": CollectionIndexes(
                "repositories",
                [
                    IndexDefinition(
                        name="url_unique",
                        keys=[("url", ASCENDING)],
                        unique=True,
                        description="Unique index on repository URL",
                    ),
                    IndexDefinition(
                        name="owner_name_compound",
                        keys=[("owner", ASCENDING), ("name", ASCENDING)],
                        unique=True,
                        description="Compound unique index on owner and repository name",
                    ),
                    IndexDefinition(
                        name="created_at_desc",
                        keys=[("created_at", DESCENDING)],
                        description="Index for recent repositories queries",
                    ),
                    IndexDefinition(
                        name="last_updated_desc",
                        keys=[("last_updated", DESCENDING)],
                        description="Index for recently updated repositories",
                    ),
                    IndexDefinition(
                        name="status_active",
                        keys=[("status", ASCENDING)],
                        partial_filter={"status": {"$in": ["active", "analyzing"]}},
                        description="Partial index for active repositories",
                    ),
                    IndexDefinition(
                        name="language_main",
                        keys=[("language", ASCENDING)],
                        sparse=True,
                        description="Index on primary programming language",
                    ),
                    IndexDefinition(
                        name="text_search",
                        keys=[("name", TEXT), ("description", TEXT)],
                        description="Text search index for repository search",
                    ),
                ],
            ),
            # Commit indexes
            "commits": CollectionIndexes(
                "commits",
                [
                    IndexDefinition(
                        name="repository_id_timestamp",
                        keys=[("repository_id", ASCENDING), ("timestamp", DESCENDING)],
                        description="Compound index for repository commit history",
                    ),
                    IndexDefinition(
                        name="sha_unique",
                        keys=[("sha", ASCENDING)],
                        unique=True,
                        description="Unique index on commit SHA",
                    ),
                    IndexDefinition(
                        name="author_email",
                        keys=[("author_email", ASCENDING)],
                        description="Index for author-based queries",
                    ),
                    IndexDefinition(
                        name="timestamp_desc",
                        keys=[("timestamp", DESCENDING)],
                        description="Index for chronological commit queries",
                    ),
                    IndexDefinition(
                        name="branch_commits",
                        keys=[
                            ("repository_id", ASCENDING),
                            ("branch", ASCENDING),
                            ("timestamp", DESCENDING),
                        ],
                        description="Compound index for branch-specific commit history",
                    ),
                    IndexDefinition(
                        name="commit_text_search",
                        keys=[("message", TEXT)],
                        description="Text search index for commit messages",
                    ),
                ],
            ),
            # File changes indexes
            "file_changes": CollectionIndexes(
                "file_changes",
                [
                    IndexDefinition(
                        name="commit_id_path",
                        keys=[("commit_id", ASCENDING), ("file_path", ASCENDING)],
                        description="Compound index for commit file changes",
                    ),
                    IndexDefinition(
                        name="repository_file_path",
                        keys=[("repository_id", ASCENDING), ("file_path", ASCENDING)],
                        description="Index for file history across repository",
                    ),
                    IndexDefinition(
                        name="change_type",
                        keys=[("change_type", ASCENDING)],
                        description="Index for filtering by change type (added, modified, deleted)",
                    ),
                    IndexDefinition(
                        name="file_extension",
                        keys=[("file_extension", ASCENDING)],
                        sparse=True,
                        description="Index for language/extension-based queries",
                    ),
                    IndexDefinition(
                        name="lines_changed_desc",
                        keys=[
                            ("lines_added", DESCENDING),
                            ("lines_deleted", DESCENDING),
                        ],
                        description="Index for large change detection",
                    ),
                ],
            ),
            # Analysis session indexes
            "analysis_sessions": CollectionIndexes(
                "analysis_sessions",
                [
                    IndexDefinition(
                        name="repository_id_created",
                        keys=[("repository_id", ASCENDING), ("created_at", DESCENDING)],
                        description="Compound index for repository analysis history",
                    ),
                    IndexDefinition(
                        name="status_active",
                        keys=[("status", ASCENDING)],
                        partial_filter={"status": {"$in": ["running", "queued"]}},
                        description="Partial index for active analysis sessions",
                    ),
                    IndexDefinition(
                        name="created_at_desc",
                        keys=[("created_at", DESCENDING)],
                        description="Index for recent analysis sessions",
                    ),
                    IndexDefinition(
                        name="analysis_type",
                        keys=[("analysis_type", ASCENDING)],
                        description="Index for filtering by analysis type",
                    ),
                    IndexDefinition(
                        name="duration_performance",
                        keys=[("duration_seconds", DESCENDING)],
                        sparse=True,
                        description="Index for performance analysis",
                    ),
                ],
            ),
            # AI analysis results indexes
            "ai_analysis_results": CollectionIndexes(
                "ai_analysis_results",
                [
                    IndexDefinition(
                        name="session_id_timestamp",
                        keys=[("session_id", ASCENDING), ("created_at", DESCENDING)],
                        description="Compound index for session results",
                    ),
                    IndexDefinition(
                        name="analysis_type_confidence",
                        keys=[
                            ("analysis_type", ASCENDING),
                            ("confidence_score", DESCENDING),
                        ],
                        description="Index for high-confidence results by type",
                    ),
                    IndexDefinition(
                        name="repository_id_type",
                        keys=[
                            ("repository_id", ASCENDING),
                            ("analysis_type", ASCENDING),
                        ],
                        description="Repository analysis results by type",
                    ),
                    IndexDefinition(
                        name="tags_array",
                        keys=[("tags", ASCENDING)],
                        description="Index for tag-based queries",
                    ),
                    IndexDefinition(
                        name="text_search_results",
                        keys=[("summary", TEXT), ("insights", TEXT)],
                        description="Text search for analysis content",
                    ),
                ],
            ),
            # Code metrics indexes
            "code_metrics": CollectionIndexes(
                "code_metrics",
                [
                    IndexDefinition(
                        name="repository_commit_compound",
                        keys=[("repository_id", ASCENDING), ("commit_id", ASCENDING)],
                        description="Compound index for repository metrics by commit",
                    ),
                    IndexDefinition(
                        name="complexity_desc",
                        keys=[("complexity_score", DESCENDING)],
                        description="Index for high complexity code identification",
                    ),
                    IndexDefinition(
                        name="language_metrics",
                        keys=[("language", ASCENDING), ("lines_of_code", DESCENDING)],
                        description="Language-specific metrics analysis",
                    ),
                    IndexDefinition(
                        name="timestamp_metrics",
                        keys=[("timestamp", DESCENDING)],
                        description="Temporal metrics analysis",
                    ),
                ],
            ),
            # User activity indexes
            "user_activity": CollectionIndexes(
                "user_activity",
                [
                    IndexDefinition(
                        name="user_id_timestamp",
                        keys=[("user_id", ASCENDING), ("timestamp", DESCENDING)],
                        description="User activity timeline",
                    ),
                    IndexDefinition(
                        name="activity_type",
                        keys=[("activity_type", ASCENDING)],
                        description="Filter by activity type",
                    ),
                    IndexDefinition(
                        name="repository_activity",
                        keys=[("repository_id", ASCENDING), ("timestamp", DESCENDING)],
                        description="Repository activity timeline",
                    ),
                    IndexDefinition(
                        name="recent_activity",
                        keys=[("timestamp", DESCENDING)],
                        description="Recent activity across all users",
                    ),
                ],
            ),
            # Search history indexes (with TTL)
            "search_history": CollectionIndexes(
                "search_history",
                [
                    IndexDefinition(
                        name="user_id_timestamp",
                        keys=[("user_id", ASCENDING), ("timestamp", DESCENDING)],
                        description="User search history",
                    ),
                    IndexDefinition(
                        name="search_terms_text",
                        keys=[("search_query", TEXT)],
                        description="Text search for search history",
                    ),
                    IndexDefinition(
                        name="ttl_expiry",
                        keys=[("timestamp", ASCENDING)],
                        ttl_seconds=2592000,  # 30 days
                        description="TTL index for search history cleanup",
                    ),
                ],
            ),
            # Cache collection indexes (with TTL)
            "cache_entries": CollectionIndexes(
                "cache_entries",
                [
                    IndexDefinition(
                        name="cache_key_unique",
                        keys=[("cache_key", ASCENDING)],
                        unique=True,
                        description="Unique index on cache keys",
                    ),
                    IndexDefinition(
                        name="ttl_expiry",
                        keys=[("expires_at", ASCENDING)],
                        ttl_seconds=0,  # Use expires_at field value
                        description="TTL index for automatic cache cleanup",
                    ),
                    IndexDefinition(
                        name="cache_type",
                        keys=[("cache_type", ASCENDING)],
                        description="Index for cache type-based queries",
                    ),
                ],
            ),
        }

    async def create_all_indexes(self) -> Dict[str, Any]:
        """
        Create all defined indexes across collections

        Returns:
            Dict with creation results and statistics
        """
        results = {
            "created_collections": [],
            "created_indexes": {},
            "errors": {},
            "total_indexes": 0,
            "successful_indexes": 0,
            "failed_indexes": 0,
        }

        logger.info("🚀 Starting comprehensive index creation...")

        for collection_name, collection_indexes in self._index_definitions.items():
            try:
                collection = self.database[collection_name]

                # Create indexes for this collection
                index_models = collection_indexes.get_index_models()

                if index_models:
                    logger.info(
                        f"📝 Creating {len(index_models)} indexes for '{collection_name}'..."
                    )

                    # Create indexes in batches for better performance
                    index_names = await collection.create_indexes(index_models)

                    results["created_collections"].append(collection_name)
                    results["created_indexes"][collection_name] = index_names
                    results["total_indexes"] += len(index_models)
                    results["successful_indexes"] += len(index_names)

                    logger.info(
                        f"✅ Created {len(index_names)} indexes for '{collection_name}'"
                    )

            except Exception as e:
                error_msg = f"Failed to create indexes for '{collection_name}': {e}"
                logger.error(f"❌ {error_msg}")
                results["errors"][collection_name] = error_msg
                results["failed_indexes"] += len(collection_indexes.indexes)

        logger.info(
            f"✅ Index creation completed: {results['successful_indexes']}/{results['total_indexes']} successful"
        )

        return results

    async def drop_all_indexes(self, confirm: bool = False) -> Dict[str, Any]:
        """
        Drop all non-_id indexes (use with caution!)

        Args:
            confirm: Must be True to actually drop indexes

        Returns:
            Dict with drop results
        """
        if not confirm:
            raise ValueError("Must set confirm=True to drop indexes")

        results = {
            "dropped_collections": [],
            "dropped_indexes": {},
            "errors": {},
            "total_dropped": 0,
        }

        logger.warning("⚠️  Starting index drop operation...")

        for collection_name in self._index_definitions.keys():
            try:
                collection = self.database[collection_name]

                # Get current indexes
                current_indexes = await collection.list_indexes().to_list(None)
                index_names = [
                    idx["name"] for idx in current_indexes if idx["name"] != "_id_"
                ]

                if index_names:
                    # Drop all non-_id indexes
                    for index_name in index_names:
                        await collection.drop_index(index_name)

                    results["dropped_collections"].append(collection_name)
                    results["dropped_indexes"][collection_name] = index_names
                    results["total_dropped"] += len(index_names)

                    logger.info(
                        f"🗑️  Dropped {len(index_names)} indexes from '{collection_name}'"
                    )

            except Exception as e:
                error_msg = f"Failed to drop indexes from '{collection_name}': {e}"
                logger.error(f"❌ {error_msg}")
                results["errors"][collection_name] = error_msg

        logger.warning(
            f"⚠️  Index drop completed: {results['total_dropped']} indexes removed"
        )

        return results

    async def get_index_status(self) -> Dict[str, Any]:
        """
        Get current index status across all collections

        Returns:
            Comprehensive index status report
        """
        status = {
            "collections": {},
            "total_collections": 0,
            "total_indexes": 0,
            "index_sizes": {},
            "missing_indexes": [],
            "extra_indexes": [],
        }

        for collection_name, expected_indexes in self._index_definitions.items():
            try:
                collection = self.database[collection_name]

                # Get current indexes
                current_indexes = await collection.list_indexes().to_list(None)
                current_index_names = {idx["name"] for idx in current_indexes}

                # Get expected index names
                expected_index_names = {idx.name for idx in expected_indexes.indexes}
                expected_index_names.add("_id_")  # Add default _id index

                # Calculate missing and extra indexes
                missing = expected_index_names - current_index_names
                extra = current_index_names - expected_index_names

                if missing:
                    status["missing_indexes"].extend(
                        [f"{collection_name}.{name}" for name in missing]
                    )

                if extra:
                    status["extra_indexes"].extend(
                        [f"{collection_name}.{name}" for name in extra]
                    )

                # Get index statistics
                try:
                    stats = await self.database.command(
                        "collStats", collection_name, indexDetails=True
                    )
                    index_sizes = stats.get("indexSizes", {})
                    status["index_sizes"][collection_name] = index_sizes
                except:
                    # Collection might not exist yet
                    pass

                status["collections"][collection_name] = {
                    "current_indexes": list(current_index_names),
                    "expected_indexes": list(expected_index_names),
                    "missing_indexes": list(missing),
                    "extra_indexes": list(extra),
                    "index_count": len(current_index_names),
                }

                status["total_collections"] += 1
                status["total_indexes"] += len(current_index_names)

            except Exception as e:
                logger.error(f"❌ Error checking indexes for '{collection_name}': {e}")
                status["collections"][collection_name] = {"error": str(e)}

        return status

    async def rebuild_index(self, collection_name: str, index_name: str) -> bool:
        """
        Rebuild a specific index

        Args:
            collection_name: Name of the collection
            index_name: Name of the index to rebuild

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.database[collection_name]

            # Find index definition
            if collection_name not in self._index_definitions:
                raise ValueError(
                    f"No index definitions found for collection '{collection_name}'"
                )

            collection_indexes = self._index_definitions[collection_name]
            index_def = None

            for idx in collection_indexes.indexes:
                if idx.name == index_name:
                    index_def = idx
                    break

            if not index_def:
                raise ValueError(f"Index '{index_name}' not found in definitions")

            logger.info(f"🔄 Rebuilding index '{index_name}' on '{collection_name}'...")

            # Drop existing index
            try:
                await collection.drop_index(index_name)
            except OperationFailure:
                pass  # Index might not exist

            # Recreate index
            index_model = index_def.to_index_model()
            await collection.create_indexes([index_model])

            logger.info(
                f"✅ Successfully rebuilt index '{index_name}' on '{collection_name}'"
            )
            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to rebuild index '{index_name}' on '{collection_name}': {e}"
            )
            return False

    async def get_index_usage_stats(self) -> Dict[str, Any]:
        """
        Get index usage statistics for performance analysis

        Returns:
            Index usage statistics across collections
        """
        usage_stats = {}

        for collection_name in self._index_definitions.keys():
            try:
                collection = self.database[collection_name]

                # Get index statistics
                stats = await collection.aggregate([{"$indexStats": {}}]).to_list(None)

                usage_stats[collection_name] = {
                    "indexes": stats,
                    "total_indexes": len(stats),
                }

            except Exception as e:
                logger.error(
                    f"❌ Error getting index stats for '{collection_name}': {e}"
                )
                usage_stats[collection_name] = {"error": str(e)}

        return usage_stats
