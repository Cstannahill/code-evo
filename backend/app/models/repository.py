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
from typing import List, Optional, Dict, Any
from pydantic import validator
from bson import ObjectId

logger = logging.getLogger(__name__)


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
    model_comparisons = relationship(
        "ModelComparisonSQL", back_populates="repository", cascade="all, delete-orphan"
    )


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


class ModelComparisonSQL(Base):
    __tablename__ = "model_comparisons"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"))

    # Comparison details
    models_compared = Column(JSON, nullable=False)  # List of model names
    analysis_type = Column(
        String, default="comparison"
    )  # comparison, benchmark, evaluation

    # Comparison results
    consensus_patterns = Column(JSON)  # Patterns all models agreed on
    disputed_patterns = Column(JSON)  # Patterns with disagreement
    agreement_score = Column(Float)  # Overall agreement score (0-1)
    diversity_score = Column(Float)  # How diverse the analyses were
    consistency_score = Column(Float)  # How consistent models were

    # Performance comparison
    performance_metrics = Column(JSON)  # Processing times, costs, etc.

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    configuration = Column(JSON)  # Analysis configuration used

    # Relationships
    repository = relationship("RepositorySQL", back_populates="model_comparisons")

    __table_args__ = (
        Index("idx_model_comparison_repo", "repository_id"),
        Index("idx_model_comparison_created", "created_at"),
        Index("idx_model_comparison_models", "models_compared"),
    )


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


class Repository(Model):
    """Repository model for MongoDB"""

    url: str = Field(unique=True, index=True)
    name: str
    default_branch: str = "main"
    status: str = "pending"
    total_commits: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_analyzed: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"collection": "repositories"}


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

    @validator("repository_id", pre=True)
    def validate_repository_id(cls, v):
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

    @validator("commit_id", pre=True)
    def validate_commit_id(cls, v):
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

    @validator("repository_id", pre=True)
    def validate_repository_id(cls, v):
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

    model_config = {"collection": "pattern_occurrences"}

    @validator("repository_id", "pattern_id", pre=True)
    def validate_object_ids(cls, v):
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @validator("commit_id", pre=True)
    def validate_commit_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return ObjectId(v)
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

    @validator("repository_id", pre=True)
    def validate_repository_id(cls, v):
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

    @validator("analysis_session_id", "model_id", pre=True)
    def validate_object_ids(cls, v):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class ModelComparison(Model):
    """Model comparison results for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    models_compared: List[str] = Field(index=True)
    analysis_type: str = "comparison"
    consensus_patterns: List[str] = []
    disputed_patterns: Optional[Dict[str, Any]] = None
    agreement_score: Optional[float] = None
    diversity_score: Optional[float] = None
    consistency_score: Optional[float] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    configuration: Optional[Dict[str, Any]] = None

    model_config = {"collection": "model_comparisons"}

    @validator("repository_id", pre=True)
    def validate_repository_id(cls, v):
        if isinstance(v, str):
            return ObjectId(v)
        return v

    @validator("updated_at", pre=True, always=True)
    def set_updated_at(cls, v):
        return datetime.utcnow()


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

    @validator("model_id", pre=True)
    def validate_model_id(cls, v):
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
                sort=AnalysisSession.created_at.desc(),
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
                            latest_session.created_at if latest_session else None
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


async def get_model_comparisons_by_repository(
    engine, repository_id: ObjectId, limit: int = 10
) -> List[ModelComparison]:
    """Get model comparisons for a repository"""
    return await engine.find(
        ModelComparison, ModelComparison.repository_id == repository_id, limit=limit
    )


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
