# app/services/repository_service.py - MongoDB Repository Service
"""
MongoDB Repository Service for Code Evolution Tracker

This service provides high-level repository operations using MongoDB models.
It integrates with the enhanced MongoDB infrastructure for production-ready
repository management with comprehensive error handling and performance optimization.
"""

import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from odmantic.exceptions import DuplicateKeyError

from app.core.database import get_enhanced_database_manager
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
    get_repositories_with_stats,
    get_technologies_by_repository,
    get_analysis_sessions_by_repository,
    get_available_ai_models,
    get_model_comparisons_by_repository,
)

logger = logging.getLogger(__name__)


class RepositoryService:
    """
    High-level repository service providing comprehensive repository management
    with MongoDB backend, caching, and performance optimization.
    """

    def __init__(self):
        """Initialize repository service with enhanced database manager"""
        self.db_manager = get_enhanced_database_manager()
        self.engine = self.db_manager.engine
        self.cache = self.db_manager.cache

        # Service metrics
        self._operation_count = 0
        self._error_count = 0

        logger.info("RepositoryService initialized with enhanced MongoDB backend")

    async def create_repository(
        self,
        url: str,
        name: str,
        description: Optional[str] = None,
        branch: str = "main",
    ) -> Repository:
        """
        Create a new repository with comprehensive validation and error handling

        Args:
            url: Repository URL
            name: Repository name
            description: Optional description
            branch: Default branch name

        Returns:
            Repository: Created repository object

        Raises:
            ValueError: If repository already exists or invalid parameters
            Exception: For database errors
        """
        try:
            self._operation_count += 1

            # Validate input parameters
            if not url or not name:
                raise ValueError("Repository URL and name are required")

            # Check if repository already exists
            existing = await self.engine.find_one(Repository, Repository.url == url)
            if existing:
                raise ValueError(f"Repository with URL {url} already exists")

            # Create repository object
            repository = Repository(
                url=url,
                name=name,
                description=description,
                default_branch=branch,
                status="created",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Save to database
            saved_repo = await self.engine.save(repository)

            # Initialize analysis session
            await self._create_initial_analysis_session(saved_repo.id)

            # Cache repository data (convert ObjectIds to strings for serialization)
            cache_key = f"repository:{saved_repo.id}"
            repo_dict = saved_repo.dict()
            # Convert ObjectId to string for cache serialization
            if 'id' in repo_dict:
                repo_dict['id'] = str(repo_dict['id'])
            # Ensure updated_at is set for new repositories
            if repo_dict.get('updated_at') is None:
                repo_dict['updated_at'] = datetime.utcnow().isoformat()
            # Serialize to JSON string for cache storage
            await self.cache.set(cache_key, json.dumps(repo_dict, default=str), ttl=3600)

            logger.info(f"✅ Created repository: {name} (ID: {saved_repo.id})")
            return saved_repo

        except DuplicateKeyError:
            self._error_count += 1
            raise ValueError(f"Repository with URL {url} already exists")
        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to create repository {name}: {e}")
            raise

    async def get_or_create_repository(
        self,
        url: str,
        name: str,
        description: Optional[str] = None,
        branch: str = "main",
    ) -> Repository:
        """
        Get existing repository by URL or create a new one
        
        Args:
            url: Repository URL
            name: Repository name
            description: Optional description
            branch: Default branch name
            
        Returns:
            Repository: Existing or newly created repository object
        """
        try:
            self._operation_count += 1

            # Check if repository already exists
            existing = await self.engine.find_one(Repository, Repository.url == url)
            if existing:
                logger.info(f"✅ Found existing repository: {name} (ID: {existing.id})")
                return existing

            # Create new repository if it doesn't exist
            return await self.create_repository(url, name, description, branch)

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to get or create repository {name}: {e}")
            raise

    async def get_repository(self, repository_id: str) -> Optional[Repository]:
        """
        Get repository by ID with caching support

        Args:
            repository_id: Repository ID

        Returns:
            Repository object or None if not found
        """
        try:
            self._operation_count += 1

            # Check cache first
            cache_key = f"repository:{repository_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"📋 Cache hit for repository {repository_id}")
                # Deserialize from JSON
                cached_data = json.loads(cached) if isinstance(cached, str) else cached
                return Repository(**cached_data)

            # Convert to ObjectId
            obj_id = ObjectId(repository_id)
            repository = await self.engine.find_one(Repository, Repository.id == obj_id)

            if repository:
                # Cache for future requests
                repo_dict = repository.dict()
                if 'id' in repo_dict:
                    repo_dict['id'] = str(repo_dict['id'])
                # Handle None updated_at for existing repositories
                if repo_dict.get('updated_at') is None:
                    repo_dict['updated_at'] = datetime.utcnow().isoformat()
                await self.cache.set(cache_key, json.dumps(repo_dict, default=str), ttl=3600)
                logger.debug(f"📊 Retrieved repository {repository_id} from database")

            return repository

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to get repository {repository_id}: {e}")
            return None

    async def list_repositories(
        self, limit: int = 50, offset: int = 0, status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List repositories with pagination and filtering

        Args:
            limit: Maximum number of repositories to return
            offset: Number of repositories to skip
            status_filter: Optional status filter

        Returns:
            Dict containing repositories and metadata
        """
        try:
            self._operation_count += 1

            # Build query conditions
            conditions = {}
            if status_filter:
                conditions["status"] = status_filter

            # Get repositories with enhanced stats
            repositories = await get_repositories_with_stats(
                self.engine, limit=limit, offset=offset
            )

            # Get total count for pagination
            total_count = await self.engine.count(Repository)

            return {
                "repositories": repositories,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
            }

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to list repositories: {e}")
            return {
                "repositories": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
                "error": str(e),
            }

    async def update_repository_status(
        self, repository_id: str, status: str, error_message: Optional[str] = None
    ) -> bool:
        """
        Update repository status with error handling

        Args:
            repository_id: Repository ID
            status: New status
            error_message: Optional error message

        Returns:
            bool: True if updated successfully
        """
        try:
            self._operation_count += 1

            obj_id = ObjectId(repository_id)
            repository = await self.engine.find_one(Repository, Repository.id == obj_id)

            if not repository:
                logger.warning(
                    f"⚠️ Repository {repository_id} not found for status update"
                )
                return False

            # Update status and timestamps
            repository.status = status
            repository.updated_at = datetime.utcnow()

            if error_message:
                repository.error_message = error_message

            if status == "analyzed":
                repository.last_analyzed = datetime.utcnow()

            # Save changes
            await self.engine.save(repository)

            # Update cache
            cache_key = f"repository:{repository_id}"
            repo_dict = repository.dict()
            if 'id' in repo_dict:
                repo_dict['id'] = str(repo_dict['id'])
            # Handle None updated_at for existing repositories  
            if repo_dict.get('updated_at') is None:
                repo_dict['updated_at'] = datetime.utcnow().isoformat()
            await self.cache.set(cache_key, json.dumps(repo_dict, default=str), ttl=3600)

            logger.info(f"✅ Updated repository {repository_id} status to {status}")
            return True

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to update repository status: {e}")
            return False

    async def add_commits(
        self, repository_id: str, commits_data: List[Dict[str, Any]]
    ) -> int:
        """
        Add multiple commits to repository with bulk operations

        Args:
            repository_id: Repository ID
            commits_data: List of commit data dictionaries

        Returns:
            int: Number of commits successfully added
        """
        try:
            self._operation_count += 1

            obj_id = ObjectId(repository_id)
            added_count = 0

            # Process commits in batches for better performance
            batch_size = 100
            for i in range(0, len(commits_data), batch_size):
                batch = commits_data[i : i + batch_size]

                commits = []
                for commit_data in batch:
                    try:
                        commit = Commit(
                            repository_id=obj_id,
                            hash=commit_data["hash"],
                            message=commit_data.get("message", ""),
                            author_name=commit_data.get("author_name", ""),
                            author_email=commit_data.get("author_email", ""),
                            committed_date=commit_data.get(
                                "committed_date", datetime.utcnow()
                            ),
                            additions=commit_data.get("additions", 0),
                            deletions=commit_data.get("deletions", 0),
                            files_changed=commit_data.get("files_changed", 0),
                        )
                        commits.append(commit)
                    except Exception as ce:
                        logger.warning(f"⚠️ Skipping invalid commit data: {ce}")
                        continue

                # Bulk save commits
                if commits:
                    try:
                        await self.engine.save_all(commits)
                        added_count += len(commits)
                        logger.debug(f"📊 Added batch of {len(commits)} commits")
                    except DuplicateKeyError:
                        # Handle duplicate commits individually
                        for commit in commits:
                            try:
                                await self.engine.save(commit)
                                added_count += 1
                            except DuplicateKeyError:
                                logger.debug(
                                    f"⚠️ Duplicate commit skipped: {commit.hash}"
                                )
                                continue

            # Update repository commit count
            await self._update_repository_stats(repository_id)

            logger.info(f"✅ Added {added_count} commits to repository {repository_id}")
            return added_count

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to add commits: {e}")
            return 0

    async def add_technologies(
        self, repository_id: str, technologies_data: List[Dict[str, Any]]
    ) -> int:
        """
        Add or update technologies for repository

        Args:
            repository_id: Repository ID
            technologies_data: List of technology data

        Returns:
            int: Number of technologies processed
        """
        try:
            self._operation_count += 1

            obj_id = ObjectId(repository_id)
            processed_count = 0

            for tech_data in technologies_data:
                try:
                    # Check if technology already exists
                    existing = await self.engine.find_one(
                        Technology,
                        Technology.repository_id == obj_id,
                        Technology.name == tech_data["name"],
                        Technology.category == tech_data.get("category"),
                    )

                    if existing:
                        # Update existing technology
                        existing.usage_count += tech_data.get("usage_count", 1)
                        existing.last_seen = datetime.utcnow()
                        existing.version = tech_data.get("version", existing.version)
                        await self.engine.save(existing)
                    else:
                        # Create new technology
                        technology = Technology(
                            repository_id=obj_id,
                            name=tech_data["name"],
                            category=tech_data.get("category"),
                            version=tech_data.get("version"),
                            usage_count=tech_data.get("usage_count", 1),
                            tech_metadata=tech_data.get("metadata"),
                        )
                        await self.engine.save(technology)

                    processed_count += 1

                except Exception as te:
                    logger.warning(
                        f"⚠️ Failed to process technology {tech_data.get('name', 'unknown')}: {te}"
                    )
                    continue

            logger.info(
                f"✅ Processed {processed_count} technologies for repository {repository_id}"
            )
            return processed_count

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to add technologies: {e}")
            return 0

    async def get_repository_analysis(self, repository_id: str) -> Dict[str, Any]:
        """
        Get comprehensive repository analysis data

        Args:
            repository_id: Repository ID

        Returns:
            Dict containing complete analysis data
        """
        try:
            self._operation_count += 1

            # Check cache first
            cache_key = f"analysis:{repository_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"📋 Cache hit for analysis {repository_id}")
                return cached

            obj_id = ObjectId(repository_id)

            # Get repository
            repository = await self.get_repository(repository_id)
            if not repository:
                raise ValueError(f"Repository {repository_id} not found")

            # Get related data in parallel
            technologies_task = get_technologies_by_repository(self.engine, obj_id)
            sessions_task = get_analysis_sessions_by_repository(
                self.engine, obj_id, limit=5
            )
            patterns_task = self._get_repository_patterns(obj_id)
            commits_task = self._get_repository_commits_summary(obj_id)

            technologies, sessions, patterns, commits_summary = await asyncio.gather(
                technologies_task,
                sessions_task,
                patterns_task,
                commits_task,
                return_exceptions=True,
            )

            # Build comprehensive analysis
            analysis = {
                "repository": repository.dict(),
                "technologies": (
                    [tech.dict() for tech in technologies]
                    if not isinstance(technologies, Exception)
                    else []
                ),
                "analysis_sessions": (
                    [session.dict() for session in sessions]
                    if not isinstance(sessions, Exception)
                    else []
                ),
                "patterns": patterns if not isinstance(patterns, Exception) else [],
                "commits_summary": (
                    commits_summary
                    if not isinstance(commits_summary, Exception)
                    else {}
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Cache analysis for 30 minutes
            await self.cache.set(cache_key, analysis, ttl=1800)

            logger.info(f"✅ Generated analysis for repository {repository_id}")
            return analysis

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to get repository analysis: {e}")
            return {
                "error": str(e),
                "repository_id": repository_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _create_initial_analysis_session(
        self, repository_id: ObjectId
    ) -> AnalysisSession:
        """Create initial analysis session for new repository"""
        try:
            session = AnalysisSession(
                repository_id=repository_id,
                status="created",
                configuration={"initial": True},
            )
            return await self.engine.save(session)
        except Exception as e:
            logger.error(f"❌ Failed to create initial analysis session: {e}")
            raise

    async def _update_repository_stats(self, repository_id: str) -> None:
        """Update repository statistics"""
        try:
            obj_id = ObjectId(repository_id)

            # Count commits
            commit_count = await self.engine.count(
                Commit, Commit.repository_id == obj_id
            )

            # Update repository
            repository = await self.engine.find_one(Repository, Repository.id == obj_id)
            if repository:
                repository.total_commits = commit_count
                repository.updated_at = datetime.utcnow()
                await self.engine.save(repository)

                # Update cache
                cache_key = f"repository:{repository_id}"
                repo_dict = repository.dict()
                if 'id' in repo_dict:
                    repo_dict['id'] = str(repo_dict['id'])
                # Handle None updated_at for existing repositories
                if repo_dict.get('updated_at') is None:
                    repo_dict['updated_at'] = datetime.utcnow().isoformat()
                await self.cache.set(cache_key, json.dumps(repo_dict, default=str), ttl=3600)

        except Exception as e:
            logger.error(f"❌ Failed to update repository stats: {e}")

    async def _get_repository_patterns(
        self, repository_id: ObjectId
    ) -> List[Dict[str, Any]]:
        """Get patterns for repository with statistics"""
        try:
            # Get pattern occurrences
            occurrences = await self.engine.find(
                PatternOccurrence, PatternOccurrence.repository_id == repository_id
            )

            # Group by pattern and calculate statistics
            pattern_stats = {}
            for occurrence in occurrences:
                pattern_id = str(occurrence.pattern_id)
                if pattern_id not in pattern_stats:
                    pattern_stats[pattern_id] = {
                        "pattern_id": pattern_id,
                        "occurrences": 0,
                        "total_confidence": 0.0,
                        "files": set(),
                        "latest_detection": occurrence.detected_at,
                    }

                stats = pattern_stats[pattern_id]
                stats["occurrences"] += 1
                stats["total_confidence"] += occurrence.confidence_score
                if occurrence.file_path:
                    stats["files"].add(occurrence.file_path)

                if occurrence.detected_at > stats["latest_detection"]:
                    stats["latest_detection"] = occurrence.detected_at

            # Convert to list and calculate averages
            result = []
            for stats in pattern_stats.values():
                stats["avg_confidence"] = (
                    stats["total_confidence"] / stats["occurrences"]
                )
                stats["files"] = list(stats["files"])
                stats["unique_files"] = len(stats["files"])
                del stats["total_confidence"]
                result.append(stats)

            return result

        except Exception as e:
            logger.error(f"❌ Failed to get repository patterns: {e}")
            return []

    async def _get_repository_commits_summary(
        self, repository_id: ObjectId
    ) -> Dict[str, Any]:
        """Get repository commits summary"""
        try:
            # Get basic commit statistics
            total_commits = await self.engine.count(
                Commit, Commit.repository_id == repository_id
            )  # Get recent commits
            recent_commits = await self.engine.find(
                Commit,
                Commit.repository_id == repository_id,
                sort=Commit.committed_date.desc(),
                limit=10,
            )

            # Calculate totals
            total_additions = 0
            total_deletions = 0
            authors = set()

            for commit in recent_commits:
                total_additions += commit.additions or 0
                total_deletions += commit.deletions or 0
                if commit.author_email:
                    authors.add(commit.author_email)

            return {
                "total_commits": total_commits,
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "unique_authors": len(authors),
                "recent_commits": [commit.dict() for commit in recent_commits],
            }

        except Exception as e:
            logger.error(f"❌ Failed to get commits summary: {e}")
            return {"total_commits": 0, "error": str(e)}

    async def get_service_health(self) -> Dict[str, Any]:
        """Get repository service health metrics"""
        try:
            # Check database connectivity
            db_health = await self.db_manager.check_health()

            # Check cache connectivity
            cache_health = (
                await self.cache.ping() if hasattr(self.cache, "ping") else True
            )

            # Get service metrics
            error_rate = (self._error_count / max(self._operation_count, 1)) * 100

            return {
                "status": (
                    "healthy"
                    if db_health["status"] == "healthy" and cache_health
                    else "degraded"
                ),
                "database": db_health,
                "cache": {"status": "healthy" if cache_health else "unhealthy"},
                "metrics": {
                    "total_operations": self._operation_count,
                    "total_errors": self._error_count,
                    "error_rate_percent": round(error_rate, 2),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Async context manager for service lifecycle
class RepositoryServiceManager:
    """Context manager for repository service lifecycle management"""

    def __init__(self):
        self.service = None

    async def __aenter__(self) -> RepositoryService:
        from app.core.service_manager import get_repository_service
        self.service = get_repository_service()
        logger.info("🚀 Repository service started")
        return self.service

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.service:
            health = await self.service.get_service_health()
            logger.info(
                f"🏁 Repository service stopped - Final health: {health['status']}"
            )
        return False


# Convenience function for getting service instance
async def get_repository_service() -> RepositoryService:
    """Get repository service instance"""
    from app.core.service_manager import get_repository_service as get_singleton
    return get_singleton()
