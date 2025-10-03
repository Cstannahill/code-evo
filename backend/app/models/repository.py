# app/models/repository.py - ENHANCED WITH MULTI-MODEL SUPPORT
import logging
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Float,
    JSON,
    ARRAY,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
from app.core.database import Base

# Imports for MongoDB/ODMantic models
from odmantic import Model, Field, Reference
from typing import List, Optional, Dict, Any, Union
from pydantic import field_validator, model_validator
from bson import ObjectId

# Import enhanced analysis models
from app.models.enhanced_analysis import (
    SecurityAnalysisResult,
    PerformanceAnalysisResult,
    ArchitecturalAnalysisResult,
    PatternAnalysisResult,
    QualityAnalysisResult,
    EvolutionAnalysisResult,
    EnsembleMetadata,
    IncrementalAnalysisMetadata,
    AnalysisDashboard,
)

# User authentication and API key management models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# User Authentication Models (SQL and MongoDB)
# ---------------------------------------------------------------------------


class UserSQL(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_guest = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    api_keys = relationship(
        "APIKeySQL", back_populates="user", cascade="all, delete-orphan"
    )
    user_repositories = relationship(
        "UserRepositorySQL", back_populates="user", cascade="all, delete-orphan"
    )


class APIKeySQL(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    provider = Column(String, nullable=False, index=True)  # openai, anthropic, gemini
    key_name = Column(String)  # user-friendly name
    encrypted_key = Column(Text, nullable=False)  # encrypted API key
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)

    # Relationships
    user = relationship("UserSQL", back_populates="api_keys")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "provider", "key_name", name="uq_user_provider_key"
        ),
        Index("idx_api_key_provider", "provider"),
        Index("idx_api_key_active", "is_active"),
    )


class UserRepositorySQL(Base):
    __tablename__ = "user_repositories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"))
    access_type = Column(String, default="owner")  # owner, viewer, contributor
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)

    # Relationships
    user = relationship("UserSQL", back_populates="user_repositories")
    repository = relationship("RepositorySQL")

    __table_args__ = (
        UniqueConstraint("user_id", "repository_id", name="uq_user_repository"),
        Index("idx_user_repo_user", "user_id"),
        Index("idx_user_repo_repository", "repository_id"),
    )


class RepositorySQL(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    default_branch = Column(String, default="main")
    status = Column(String, default="pending")  # pending, analyzing, completed, error
    total_commits = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_analyzed = Column(DateTime)
    error_message = Column(Text)

    # Relationships
    commits = relationship(
        "CommitSQL", back_populates="repository", cascade="all, delete-orphan"
    )
    technologies = relationship(
        "TechnologySQL", back_populates="repository", cascade="all, delete-orphan"
    )
    analysis_sessions = relationship(
        "AnalysisSessionSQL", back_populates="repository", cascade="all, delete-orphan"
    )
    pattern_occurrences = relationship(
        "PatternOccurrenceSQL",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    # Model comparisons removed - using single model analysis only


class CommitSQL(Base):
    __tablename__ = "commits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"))
    hash = Column(String, nullable=False, index=True)
    author_name = Column(String)
    author_email = Column(String)
    committed_date = Column(DateTime)
    message = Column(Text)
    files_changed_count = Column(Integer, default=0)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    stats = Column(JSON)  # Keep the original stats field too

    # Relationships
    repository = relationship("RepositorySQL", back_populates="commits")
    file_changes = relationship(
        "FileChangeSQL", back_populates="commit", cascade="all, delete-orphan"
    )
    pattern_occurrences = relationship(
        "PatternOccurrenceSQL", back_populates="commit", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("repository_id", "hash", name="uq_repo_commit_hash"),
        Index("idx_commit_date", "committed_date"),
    )


class FileChangeSQL(Base):
    __tablename__ = "file_changes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    commit_id = Column(String, ForeignKey("commits.id", ondelete="CASCADE"))
    file_path = Column(String, nullable=False)
    change_type = Column(String)  # added, modified, deleted, renamed
    language = Column(String)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    content_snippet = Column(Text)

    # Relationships
    commit = relationship("CommitSQL", back_populates="file_changes")


class TechnologySQL(Base):
    __tablename__ = "technologies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    category = Column(String)  # language, framework, library, tool, database, platform
    version = Column(String)
    usage_count = Column(Integer, default=1)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    tech_metadata = Column(JSON)

    # Relationships
    repository = relationship("RepositorySQL", back_populates="technologies")

    __table_args__ = (
        UniqueConstraint("repository_id", "name", "category", name="uq_repo_tech"),
        Index("idx_tech_category", "category"),
    )


class PatternSQL(Base):
    __tablename__ = "patterns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True, index=True)
    category = Column(
        String
    )  # design_pattern, architectural, language_feature, anti_pattern
    description = Column(Text)
    complexity_level = Column(String)  # simple, intermediate, advanced
    is_antipattern = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    occurrences = relationship(
        "PatternOccurrenceSQL", back_populates="pattern", cascade="all, delete-orphan"
    )


class PatternOccurrenceSQL(Base):
    __tablename__ = "pattern_occurrences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"))
    pattern_id = Column(String, ForeignKey("patterns.id", ondelete="CASCADE"))
    commit_id = Column(
        String, ForeignKey("commits.id", ondelete="CASCADE"), nullable=True
    )
    file_path = Column(String)
    code_snippet = Column(Text)
    line_number = Column(Integer)
    confidence_score = Column(Float, default=1.0)
    detected_at = Column(DateTime, default=datetime.utcnow)

    # NEW: Multi-model support
    ai_model_used = Column(String)  # Which AI model detected this
    model_confidence = Column(Float)  # Model's confidence in this detection
    processing_time_ms = Column(Integer)  # How long the analysis took
    token_usage = Column(JSON)  # Token usage for API models

    # Relationships
    repository = relationship("RepositorySQL", back_populates="pattern_occurrences")
    pattern = relationship("PatternSQL", back_populates="occurrences")
    commit = relationship("CommitSQL", back_populates="pattern_occurrences")

    __table_args__ = (
        Index("idx_pattern_occurrence_repo", "repository_id"),
        Index("idx_pattern_occurrence_pattern", "pattern_id"),
        Index("idx_pattern_occurrence_detected", "detected_at"),
        Index("idx_pattern_occurrence_model", "ai_model_used"),
    )


class AnalysisSessionSQL(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"))
    status = Column(String, default="running")  # running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    commits_analyzed = Column(Integer, default=0)
    patterns_found = Column(Integer, default=0)
    configuration = Column(JSON)
    error_message = Column(Text)

    # Relationships
    repository = relationship("RepositorySQL", back_populates="analysis_sessions")
    ai_analysis_results = relationship(
        "AIAnalysisResultSQL",
        back_populates="analysis_session",
        cascade="all, delete-orphan",
    )


# NEW MODELS FOR MULTI-MODEL SUPPORT


class AIModelSQL(Base):
    __tablename__ = "ai_models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(
        String, nullable=False, unique=True, index=True
    )  # e.g., "codellama:7b"
    display_name = Column(String, nullable=False)  # e.g., "CodeLlama 7B"
    provider = Column(String, nullable=False)  # e.g., "Ollama", "OpenAI", "Anthropic"
    model_type = Column(
        String, default="code_analysis"
    )  # code_analysis, general, specialized
    context_window = Column(Integer)
    cost_per_1k_tokens = Column(Float, default=0.0)
    strengths = Column(JSON)  # List of model strengths
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)

    # Relationships
    analysis_results = relationship(
        "AIAnalysisResultSQL", back_populates="model", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_ai_model_provider", "provider"),
        Index("idx_ai_model_available", "is_available"),
    )


class AIAnalysisResultSQL(Base):
    __tablename__ = "ai_analysis_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_session_id = Column(
        String, ForeignKey("analysis_sessions.id", ondelete="CASCADE")
    )
    model_id = Column(String, ForeignKey("ai_models.id", ondelete="CASCADE"))

    # Analysis input
    code_snippet = Column(Text, nullable=False)
    language = Column(String)

    # Analysis results
    detected_patterns = Column(JSON)  # List of pattern names
    complexity_score = Column(Float)
    skill_level = Column(String)  # beginner, intermediate, advanced
    suggestions = Column(JSON)  # List of suggestions
    confidence_score = Column(Float)

    # Performance metrics
    processing_time = Column(Float)  # Processing time in seconds
    token_usage = Column(JSON)  # Token usage details
    cost_estimate = Column(Float, default=0.0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)

    # Relationships
    analysis_session = relationship(
        "AnalysisSessionSQL", back_populates="ai_analysis_results"
    )
    model = relationship("AIModelSQL", back_populates="analysis_results")

    __table_args__ = (
        Index("idx_ai_result_session", "analysis_session_id"),
        Index("idx_ai_result_model", "model_id"),
        Index("idx_ai_result_created", "created_at"),
    )


# ModelComparisonSQL removed - using single model analysis only


class ModelBenchmarkSQL(Base):
    __tablename__ = "model_benchmarks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("ai_models.id", ondelete="CASCADE"))

    # Benchmark details
    benchmark_name = Column(String, nullable=False)  # e.g., "code_pattern_detection"
    benchmark_version = Column(String, default="1.0")
    test_dataset_size = Column(Integer)

    # Performance metrics
    accuracy_score = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    f1_score = Column(Float)
    avg_processing_time = Column(Float)
    avg_cost_per_analysis = Column(Float)

    # Additional metrics
    pattern_detection_rate = Column(JSON)  # Per-pattern detection rates
    false_positive_rate = Column(Float)
    false_negative_rate = Column(Float)

    # Metadata
    benchmark_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

    # Relationships
    model = relationship("AIModelSQL")

    __table_args__ = (
        Index("idx_benchmark_model", "model_id"),
        Index("idx_benchmark_name", "benchmark_name"),
        Index("idx_benchmark_date", "benchmark_date"),
        UniqueConstraint(
            "model_id", "benchmark_name", "benchmark_version", name="uq_model_benchmark"
        ),
    )


# ---------------------------------------------------------------------------
# MongoDB/ODMantic models (moved from repository2.py)
# ---------------------------------------------------------------------------


class User(Model):
    """User model for MongoDB"""

    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = Field(default=True, index=True)
    is_guest: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    last_login: Optional[datetime] = None

    model_config = {"collection": "users"}


class APIKey(Model):
    """API Key model for MongoDB"""

    user_id: ObjectId = Field(index=True)
    provider: str = Field(index=True)  # openai, anthropic, gemini
    key_name: Optional[str] = None  # user-friendly name
    encrypted_key: str  # encrypted API key
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    last_used: Optional[datetime] = None
    is_active: bool = Field(default=True, index=True)
    usage_count: int = Field(default=0)

    model_config = {"collection": "api_keys"}

    @field_validator("user_id", mode="before")
    def validate_user_id(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v

    # converted to Pydantic v2 field_validator above


class UserRepository(Model):
    """User-Repository access model for MongoDB"""

    user_id: ObjectId = Field(index=True)
    repository_id: ObjectId = Field(index=True)
    access_type: str = "owner"  # owner, viewer, contributor
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    last_accessed: Optional[datetime] = None

    model_config = {"collection": "user_repositories"}

    @field_validator("user_id", mode="before")
    def validate_user_id_multi(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("repository_id", mode="before")
    def validate_repository_id_multi(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v

    # converted to Pydantic v2 field_validator


class Repository(Model):
    """Repository model for MongoDB - supports both global and user-specific tracking"""

    url: str = Field(unique=True, index=True)
    name: str
    default_branch: str = "main"
    status: str = "pending"
    total_commits: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_analyzed: Optional[datetime] = None
    error_message: Optional[str] = None

    # Access control - optional for backward compatibility
    is_public: Optional[bool] = Field(
        default=None, index=True
    )  # publicly accessible for global analysis
    created_by_user: Optional[ObjectId] = Field(
        default=None, index=True
    )  # user who first added it
    analysis_count: Optional[int] = Field(default=None)  # track how many times analyzed
    unique_users: Optional[int] = Field(
        default=None
    )  # track unique users who analyzed it

    # Metadata for global tracking - optional for backward compatibility
    tags: Optional[List[str]] = Field(default=None)  # searchable tags
    description: Optional[str] = Field(default=None)
    primary_language: Optional[str] = Field(default=None, index=True)

    model_config = {"collection": "repositories"}

    @field_validator("created_by_user", mode="before")
    def validate_created_by_user(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v

    # Helper methods to get values with defaults
    def get_is_public(self) -> bool:
        """Get is_public with default value for backward compatibility"""
        return self.is_public if self.is_public is not None else True

    def get_analysis_count(self) -> int:
        """Get analysis_count with default value for backward compatibility"""
        return self.analysis_count if self.analysis_count is not None else 0

    def get_unique_users(self) -> int:
        """Get unique_users with default value for backward compatibility"""
        return self.unique_users if self.unique_users is not None else 0

    def get_tags(self) -> List[str]:
        """Get tags with default value for backward compatibility"""
        return self.tags if self.tags is not None else []


class Commit(Model):
    """Commit model for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    hash: str = Field(index=True)
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    committed_date: Optional[datetime] = None
    message: Optional[str] = None
    files_changed_count: int = 0
    additions: int = 0
    deletions: int = 0
    stats: Optional[Dict[str, Any]] = None

    model_config = {"collection": "commits"}

    @field_validator("repository_id", mode="before")
    def validate_repository_id(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class FileChange(Model):
    """File change model for MongoDB"""

    commit_id: ObjectId = Field(index=True)
    file_path: str
    change_type: Optional[str] = None
    language: Optional[str] = None
    additions: int = 0
    deletions: int = 0
    content_snippet: Optional[str] = None

    model_config = {"collection": "file_changes"}

    @field_validator("commit_id", mode="before")
    def validate_commit_id(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class Technology(Model):
    """Technology model for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    name: str
    category: Optional[str] = None
    version: Optional[str] = None
    usage_count: int = 1
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    tech_metadata: Optional[Dict[str, Any]] = None

    model_config = {"collection": "technologies"}

    @field_validator("repository_id", mode="before")
    def validate_repository_id_tech(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class Pattern(Model):
    """Pattern model for MongoDB"""

    name: str = Field(unique=True, index=True)
    category: Optional[str] = None
    description: Optional[str] = None
    complexity_level: Optional[str] = None
    is_antipattern: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "patterns"}


class PatternOccurrence(Model):
    """Pattern occurrence model for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    pattern_id: ObjectId = Field(index=True)
    commit_id: Optional[ObjectId] = Field(default=None, index=True)
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None
    line_number: Optional[int] = None
    confidence_score: float = 1.0
    detected_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    ai_model_used: Optional[str] = Field(default=None, index=True)
    model_confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    token_usage: Optional[Dict[str, Any]] = None
    ai_analysis_metadata: Optional[Dict[str, Any]] = None

    model_config = {"collection": "pattern_occurrences"}

    @field_validator("repository_id", mode="before")
    def validate_repository_id_pattern(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("pattern_id", mode="before")
    def validate_pattern_id(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("commit_id", mode="before")
    def validate_commit_id_optional(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("detected_at", mode="before")
    def validate_detected_at(cls, v, info):
        if v is None:
            return datetime.utcnow()
        if isinstance(v, datetime):
            # Remove timezone info to make it naive
            return v.replace(tzinfo=None)
        return v


class AnalysisSession(Model):
    """Analysis session model for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    status: str = "running"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    commits_analyzed: int = 0
    patterns_found: int = 0
    configuration: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    model_config = {"collection": "analysis_sessions"}

    @field_validator("repository_id", mode="before")
    def validate_repository_id_session(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class AIModel(Model):
    """AI model configuration for MongoDB"""

    name: str = Field(unique=True, index=True)
    display_name: str
    provider: str = Field(index=True)
    model_type: str = "code_analysis"
    context_window: Optional[int] = None
    cost_per_1k_tokens: float = 0.0
    strengths: List[str] = []
    is_available: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    usage_count: int = 0

    model_config = {"collection": "ai_models"}


class AIAnalysisResult(Model):
    """AI analysis result model for MongoDB"""

    analysis_session_id: ObjectId = Field(index=True)
    model_id: ObjectId = Field(index=True)

    code_snippet: str
    language: Optional[str] = None

    detected_patterns: List[str] = []
    complexity_score: Optional[float] = None
    skill_level: Optional[str] = None
    suggestions: List[str] = []
    confidence_score: Optional[float] = None

    processing_time: Optional[float] = None
    token_usage: Optional[Dict[str, Any]] = None
    cost_estimate: float = 0.0

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    error_message: Optional[str] = None

    model_config = {"collection": "ai_analysis_results"}

    @field_validator("analysis_session_id", mode="before")
    def validate_analysis_session_id_model_id(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("model_id", mode="before")
    def validate_model_id_field(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v


# ModelComparison removed - using single model analysis only


class ModelBenchmark(Model):
    """Model benchmark results for MongoDB"""

    model_id: ObjectId = Field(index=True)
    benchmark_name: str = Field(index=True)
    benchmark_version: str = "1.0"
    test_dataset_size: Optional[int] = None
    accuracy_score: Optional[float] = None
    precision_score: Optional[float] = None
    recall_score: Optional[float] = None
    f1_score: Optional[float] = None
    avg_processing_time: Optional[float] = None
    avg_cost_per_analysis: Optional[float] = None
    pattern_detection_rate: Optional[Dict[str, Any]] = None
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None
    benchmark_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    notes: Optional[str] = None

    model_config = {"collection": "model_benchmarks"}

    @field_validator("model_id", mode="before")
    def validate_model_id_benchmark(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v


# Utility functions for common MongoDB queries


async def get_repositories_with_stats(
    engine, limit: int = 50, offset: int = 0
) -> List[Dict[str, Any]]:
    """Get repositories with enhanced statistics including commits and technology counts"""
    try:
        # Get repositories with pagination
        repositories = await engine.find(Repository, limit=limit, skip=offset)

        enhanced_repos = []

        for repo in repositories:
            # Get commit count
            commit_count = await engine.count(Commit, Commit.repository_id == repo.id)

            # Get technology count
            tech_count = await engine.count(
                Technology, Technology.repository_id == repo.id
            )

            # Get pattern occurrences count
            pattern_count = await engine.count(
                PatternOccurrence, PatternOccurrence.repository_id == repo.id
            )  # Get latest analysis session
            latest_session = await engine.find_one(
                AnalysisSession,
                AnalysisSession.repository_id == repo.id,
                sort=AnalysisSession.started_at.desc(),
            )

            # Build enhanced repository data
            repo_dict = repo.dict()
            repo_dict.update(
                {
                    "stats": {
                        "commit_count": commit_count,
                        "technology_count": tech_count,
                        "pattern_count": pattern_count,
                        "has_analysis": latest_session is not None,
                        "last_analysis": (
                            latest_session.started_at if latest_session else None
                        ),
                        "analysis_status": (
                            latest_session.status if latest_session else "not_analyzed"
                        ),
                    }
                }
            )

            enhanced_repos.append(repo_dict)

        return enhanced_repos

    except Exception as e:
        logger.error(f"❌ Failed to get repositories with stats: {e}")
        return []


async def get_repository_by_url(engine, url: str) -> Optional[Repository]:
    """Get repository by URL"""
    return await engine.find_one(Repository, Repository.url == url)


async def get_commits_by_repository(
    engine, repository_id: ObjectId, limit: int = 100
) -> List[Commit]:
    """Get commits for a repository"""
    return await engine.find(Commit, Commit.repository_id == repository_id, limit=limit)


async def get_pattern_occurrences_by_repository(
    engine, repository_id: ObjectId, limit: int = 100
) -> List[PatternOccurrence]:
    """Get pattern occurrences for a repository"""
    return await engine.find(
        PatternOccurrence, PatternOccurrence.repository_id == repository_id, limit=limit
    )


async def get_technologies_by_repository(
    engine, repository_id: ObjectId
) -> List[Technology]:
    """Get technologies used in a repository"""
    return await engine.find(Technology, Technology.repository_id == repository_id)


async def get_analysis_sessions_by_repository(
    engine, repository_id: ObjectId, limit: int = 10
) -> List[AnalysisSession]:
    """Get analysis sessions for a repository"""
    return await engine.find(
        AnalysisSession, AnalysisSession.repository_id == repository_id, limit=limit
    )


async def get_available_ai_models(engine) -> List[AIModel]:
    """Get all available AI models"""
    return await engine.find(AIModel, AIModel.is_available == True)


# get_model_comparisons_by_repository removed - using single model analysis only


async def create_custom_indexes(engine):
    """Create custom compound indexes for better performance"""

    await engine.get_collection(Commit).create_index(
        [("repository_id", 1), ("committed_date", -1)]
    )

    await engine.get_collection(PatternOccurrence).create_index(
        [("repository_id", 1), ("pattern_id", 1), ("detected_at", -1)]
    )

    await engine.get_collection(Technology).create_index(
        [("repository_id", 1), ("category", 1), ("name", 1)]
    )

    await engine.get_collection(AIAnalysisResult).create_index(
        [("analysis_session_id", 1), ("model_id", 1), ("created_at", -1)]
    )

    await engine.get_collection(Commit).create_index(
        [("repository_id", 1), ("hash", 1)], unique=True
    )

    await engine.get_collection(Technology).create_index(
        [("repository_id", 1), ("name", 1), ("category", 1)], unique=True
    )

    await engine.get_collection(ModelBenchmark).create_index(
        [("model_id", 1), ("benchmark_name", 1), ("benchmark_version", 1)], unique=True
    )


# Enhanced Analysis Models for MongoDB


class SecurityAnalysis(Model):
    """Security analysis results for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    analysis_session_id: Optional[ObjectId] = Field(default=None, index=True)
    file_path: Optional[str] = None
    language: Optional[str] = None

    # Security results
    overall_score: int = Field(ge=0, le=100)
    risk_level: str = Field(index=True)  # critical, high, medium, low, info
    total_vulnerabilities: int = Field(ge=0)
    vulnerabilities_by_severity: Dict[str, int] = Field(default_factory=dict)
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    owasp_coverage: Dict[str, int] = Field(default_factory=dict)

    # Metadata
    analyzer_version: str = "1.0.0"
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    model_config = {"collection": "security_analyses"}

    @field_validator("repository_id", mode="before")
    def validate_repoid_security(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("analysis_session_id", mode="before")
    def validate_asisessionid_security(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v


class PerformanceAnalysis(Model):
    """Performance analysis results for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    analysis_session_id: Optional[ObjectId] = Field(default=None, index=True)
    file_path: Optional[str] = None
    language: Optional[str] = None

    # Performance results
    overall_score: int = Field(ge=0, le=100)
    performance_grade: str = Field(index=True)  # A+, A, B, C, D
    total_issues: int = Field(ge=0)
    issues_by_severity: Dict[str, int] = Field(default_factory=dict)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    optimizations: List[str] = Field(default_factory=list)
    bottlenecks: List[str] = Field(default_factory=list)

    # Metadata
    analyzer_version: str = "1.0.0"
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    model_config = {"collection": "performance_analyses"}

    @field_validator("repository_id", mode="before")
    def validate_repoid_perf(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("analysis_session_id", mode="before")
    def validate_asisessionid_perf(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v


class ArchitecturalAnalysis(Model):
    """Architectural analysis results for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    analysis_session_id: Optional[ObjectId] = Field(default=None, index=True)

    # Architecture results
    architectural_style: Dict[str, Any] = Field(default_factory=dict)
    design_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)
    component_analysis: Dict[str, Any] = Field(default_factory=dict)
    dependency_analysis: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    architecture_smells: List[str] = Field(default_factory=list)

    # Metadata
    analyzer_version: str = "1.0.0"
    files_analyzed: int = Field(default=0, ge=0)
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    model_config = {"collection": "architectural_analyses"}

    @field_validator("repository_id", mode="before")
    def validate_repoid_arch(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("analysis_session_id", mode="before")
    def validate_asisessionid_arch(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v


class EnhancedPatternAnalysis(Model):
    """Enhanced pattern analysis results for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    analysis_session_id: Optional[ObjectId] = Field(default=None, index=True)
    file_path: Optional[str] = None
    language: Optional[str] = None

    # Pattern results
    detected_patterns: List[str] = Field(default_factory=list)
    ai_patterns: List[str] = Field(default_factory=list)
    combined_patterns: List[str] = Field(default_factory=list)
    complexity_score: float = Field(ge=1.0, le=10.0)
    skill_level: str = Field(index=True)  # beginner, intermediate, advanced
    suggestions: List[str] = Field(default_factory=list)
    pattern_confidence: Dict[str, float] = Field(default_factory=dict)

    # Metadata
    ai_powered: bool = False
    model_used: Optional[str] = None
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    model_config = {"collection": "enhanced_pattern_analyses"}

    @field_validator("repository_id", mode="before")
    def validate_repoid_pattern(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("analysis_session_id", mode="before")
    def validate_asisessionid_pattern(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v


class EnhancedQualityAnalysis(Model):
    """Enhanced quality analysis results for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    analysis_session_id: Optional[ObjectId] = Field(default=None, index=True)
    file_path: Optional[str] = None
    language: Optional[str] = None

    # Quality results
    quality_score: float = Field(ge=0.0, le=100.0)
    readability: str = Field(index=True)
    issues: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    ai_powered: bool = False
    model_used: Optional[str] = None
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    model_config = {"collection": "enhanced_quality_analyses"}

    @field_validator("repository_id", mode="before")
    def validate_repository_id_dashboard2(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("analysis_session_id", mode="before")
    def validate_analysis_session_id_dashboard2(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v


class EnsembleAnalysisResult(Model):
    """AI ensemble analysis results for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    analysis_session_id: Optional[ObjectId] = Field(default=None, index=True)
    analysis_type: str = Field(index=True)  # pattern, quality, security, performance

    # Ensemble results
    consensus_result: Dict[str, Any] = Field(default_factory=dict)
    individual_results: List[Dict[str, Any]] = Field(default_factory=list)
    consensus_confidence: float = Field(ge=0.0, le=1.0)
    consensus_method: str = Field(index=True)
    models_used: List[str] = Field(default_factory=list)
    total_execution_time: float = Field(ge=0.0)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    model_config = {"collection": "ensemble_analysis_results"}

    @field_validator("repository_id", mode="before")
    def validate_repository_id_analysis_dash(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @field_validator("analysis_session_id", mode="before")
    def validate_analysis_session_id_analysis_dash(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
        return v


class IncrementalAnalysisSnapshot(Model):
    """Snapshot for incremental analysis in MongoDB"""

    repository_id: ObjectId = Field(index=True)
    commit_hash: str = Field(index=True)

    # Snapshot data
    file_hashes: Dict[str, str] = Field(default_factory=dict)
    analysis_results: Dict[str, Any] = Field(default_factory=dict)
    total_files: int = Field(ge=0)
    total_lines: int = Field(ge=0)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    model_config = {"collection": "incremental_snapshots"}

    @field_validator("repository_id", mode="before")
    def validate_repository_id_dashboard(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class AnalysisDashboardData(Model):
    """Dashboard data for repositories in MongoDB"""

    repository_id: ObjectId = Field(unique=True, index=True)
    repo_name: str
    repo_url: str
    branch: str
    last_analyzed: datetime = Field(index=True)

    # High-level metrics
    total_files_analyzed: int = Field(ge=0)
    total_lines_of_code: int = Field(ge=0)
    primary_languages: List[str] = Field(default_factory=list)

    # Scores
    overall_quality_score: int = Field(ge=0, le=100)
    overall_security_score: int = Field(ge=0, le=100)
    overall_performance_score: int = Field(ge=0, le=100)

    # Summaries
    security_summary: Dict[str, Any] = Field(default_factory=dict)
    performance_summary: Dict[str, Any] = Field(default_factory=dict)
    architecture_summary: Dict[str, Any] = Field(default_factory=dict)

    # Trends
    quality_trend: Optional[str] = None
    security_trend: Optional[str] = None
    performance_trend: Optional[str] = None

    # Recommendations
    top_recommendations: List[str] = Field(default_factory=list)

    # Analysis metadata
    analysis_type: str = "comprehensive"
    models_used: List[str] = Field(default_factory=list)
    analysis_duration: float = Field(ge=0.0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    model_config = {"collection": "analysis_dashboards"}

    @field_validator("repository_id", mode="before")
    def validate_repository_id_final(cls, v, info):
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @model_validator(mode="before")
    def set_updated_at(cls, values):
        # In pydantic v2, model-level defaulting can be done via model_validator
        values.setdefault("updated_at", datetime.utcnow())
        return values


# Enhanced query functions


async def get_enhanced_analysis_by_repository(
    engine, repository_id: ObjectId
) -> Dict[str, Any]:
    """Get all enhanced analysis results for a repository"""
    try:
        # Get all analysis types
        security_analyses = await engine.find(
            SecurityAnalysis, SecurityAnalysis.repository_id == repository_id
        )
        performance_analyses = await engine.find(
            PerformanceAnalysis, PerformanceAnalysis.repository_id == repository_id
        )
        architectural_analyses = await engine.find(
            ArchitecturalAnalysis, ArchitecturalAnalysis.repository_id == repository_id
        )
        pattern_analyses = await engine.find(
            EnhancedPatternAnalysis,
            EnhancedPatternAnalysis.repository_id == repository_id,
        )
        quality_analyses = await engine.find(
            EnhancedQualityAnalysis,
            EnhancedQualityAnalysis.repository_id == repository_id,
        )
        ensemble_results = await engine.find(
            EnsembleAnalysisResult,
            EnsembleAnalysisResult.repository_id == repository_id,
        )

        # Get dashboard data
        dashboard = await engine.find_one(
            AnalysisDashboardData, AnalysisDashboardData.repository_id == repository_id
        )

        return {
            "security_analyses": [analysis.dict() for analysis in security_analyses],
            "performance_analyses": [
                analysis.dict() for analysis in performance_analyses
            ],
            "architectural_analyses": [
                analysis.dict() for analysis in architectural_analyses
            ],
            "pattern_analyses": [analysis.dict() for analysis in pattern_analyses],
            "quality_analyses": [analysis.dict() for analysis in quality_analyses],
            "ensemble_results": [result.dict() for result in ensemble_results],
            "dashboard": dashboard.dict() if dashboard else None,
        }

    except Exception as e:
        logger.error(f"Failed to get enhanced analyses: {e}")
        return {}


async def create_enhanced_indexes(engine):
    """Create indexes for enhanced analysis models"""
    try:
        # Security analysis indexes
        await engine.get_collection(SecurityAnalysis).create_index(
            [("repository_id", 1), ("risk_level", 1), ("created_at", -1)]
        )

        # Performance analysis indexes
        await engine.get_collection(PerformanceAnalysis).create_index(
            [("repository_id", 1), ("performance_grade", 1), ("created_at", -1)]
        )

        # Architectural analysis indexes
        await engine.get_collection(ArchitecturalAnalysis).create_index(
            [("repository_id", 1), ("created_at", -1)]
        )

        # Enhanced pattern analysis indexes
        await engine.get_collection(EnhancedPatternAnalysis).create_index(
            [("repository_id", 1), ("skill_level", 1), ("created_at", -1)]
        )

        # Enhanced quality analysis indexes
        await engine.get_collection(EnhancedQualityAnalysis).create_index(
            [("repository_id", 1), ("readability", 1), ("created_at", -1)]
        )

        # Ensemble analysis indexes
        await engine.get_collection(EnsembleAnalysisResult).create_index(
            [("repository_id", 1), ("analysis_type", 1), ("created_at", -1)]
        )

        # Dashboard indexes
        await engine.get_collection(AnalysisDashboardData).create_index(
            [("updated_at", -1)]
        )

        logger.info("✅ Enhanced analysis indexes created successfully")

    except Exception as e:
        logger.error(f"Failed to create enhanced indexes: {e}")
        raise
