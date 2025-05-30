# app/models/repository.py - MongoDB Models with ODMantic
from odmantic import Model, Field, Reference
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import validator
from bson import ObjectId
import uuid


class Repository(Model):
    """Repository model for MongoDB"""

    # Basic repository info
    url: str = Field(unique=True, index=True)
    name: str
    default_branch: str = "main"
    status: str = "pending"  # pending, analyzing, completed, error
    total_commits: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_analyzed: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        collection = "repositories"


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

    class Config:
        collection = "commits"

    @validator("repository_id", pre=True)
    def validate_repository_id(cls, v):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class FileChange(Model):
    """File change model for MongoDB"""

    commit_id: ObjectId = Field(index=True)
    file_path: str
    change_type: Optional[str] = None  # added, modified, deleted, renamed
    language: Optional[str] = None
    additions: int = 0
    deletions: int = 0
    content_snippet: Optional[str] = None

    class Config:
        collection = "file_changes"

    @validator("commit_id", pre=True)
    def validate_commit_id(cls, v):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class Technology(Model):
    """Technology model for MongoDB"""

    repository_id: ObjectId = Field(index=True)
    name: str
    category: Optional[str] = (
        None  # language, framework, library, tool, database, platform
    )
    version: Optional[str] = None
    usage_count: int = 1
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    tech_metadata: Optional[Dict[str, Any]] = None

    class Config:
        collection = "technologies"

    @validator("repository_id", pre=True)
    def validate_repository_id(cls, v):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class Pattern(Model):
    """Pattern model for MongoDB"""

    name: str = Field(unique=True, index=True)
    category: Optional[str] = (
        None  # design_pattern, architectural, language_feature, anti_pattern
    )
    description: Optional[str] = None
    complexity_level: Optional[str] = None  # simple, intermediate, advanced
    is_antipattern: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection = "patterns"


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

    # Multi-model support
    ai_model_used: Optional[str] = Field(default=None, index=True)
    model_confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    token_usage: Optional[Dict[str, Any]] = None

    class Config:
        collection = "pattern_occurrences"

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
    status: str = "running"  # running, completed, failed
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    commits_analyzed: int = 0
    patterns_found: int = 0
    configuration: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    class Config:
        collection = "analysis_sessions"

    @validator("repository_id", pre=True)
    def validate_repository_id(cls, v):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class AIModel(Model):
    """AI model configuration for MongoDB"""

    name: str = Field(unique=True, index=True)  # e.g., "codellama:7b"
    display_name: str  # e.g., "CodeLlama 7B"
    provider: str = Field(index=True)  # e.g., "Ollama", "OpenAI", "Anthropic"
    model_type: str = "code_analysis"  # code_analysis, general, specialized
    context_window: Optional[int] = None
    cost_per_1k_tokens: float = 0.0
    strengths: List[str] = []  # List of model strengths
    is_available: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    usage_count: int = 0

    class Config:
        collection = "ai_models"


class AIAnalysisResult(Model):
    """AI analysis result model for MongoDB"""

    analysis_session_id: ObjectId = Field(index=True)
    model_id: ObjectId = Field(index=True)

    # Analysis input
    code_snippet: str
    language: Optional[str] = None

    # Analysis results
    detected_patterns: List[str] = []  # List of pattern names
    complexity_score: Optional[float] = None
    skill_level: Optional[str] = None  # beginner, intermediate, advanced
    suggestions: List[str] = []  # List of suggestions
    confidence_score: Optional[float] = None

    # Performance metrics
    processing_time: Optional[float] = None  # Processing time in seconds
    token_usage: Optional[Dict[str, Any]] = None  # Token usage details
    cost_estimate: float = 0.0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    error_message: Optional[str] = None

    class Config:
        collection = "ai_analysis_results"

    @validator("analysis_session_id", "model_id", pre=True)
    def validate_object_ids(cls, v):
        if isinstance(v, str):
            return ObjectId(v)
        return v


class ModelComparison(Model):
    """Model comparison results for MongoDB"""

    repository_id: ObjectId = Field(index=True)

    # Comparison details
    models_compared: List[str] = Field(index=True)  # List of model names
    analysis_type: str = "comparison"  # comparison, benchmark, evaluation

    # Comparison results
    consensus_patterns: List[str] = []  # Patterns all models agreed on
    disputed_patterns: Optional[Dict[str, Any]] = None  # Patterns with disagreement
    agreement_score: Optional[float] = None  # Overall agreement score (0-1)
    diversity_score: Optional[float] = None  # How diverse the analyses were
    consistency_score: Optional[float] = None  # How consistent models were

    # Performance comparison
    performance_metrics: Optional[Dict[str, Any]] = (
        None  # Processing times, costs, etc.
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    configuration: Optional[Dict[str, Any]] = None  # Analysis configuration used

    class Config:
        collection = "model_comparisons"

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

    # Benchmark details
    benchmark_name: str = Field(index=True)  # e.g., "code_pattern_detection"
    benchmark_version: str = "1.0"
    test_dataset_size: Optional[int] = None

    # Performance metrics
    accuracy_score: Optional[float] = None
    precision_score: Optional[float] = None
    recall_score: Optional[float] = None
    f1_score: Optional[float] = None
    avg_processing_time: Optional[float] = None
    avg_cost_per_analysis: Optional[float] = None

    # Additional metrics
    pattern_detection_rate: Optional[Dict[str, Any]] = (
        None  # Per-pattern detection rates
    )
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None

    # Metadata
    benchmark_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    notes: Optional[str] = None

    class Config:
        collection = "model_benchmarks"

    @validator("model_id", pre=True)
    def validate_model_id(cls, v):
        if isinstance(v, str):
            return ObjectId(v)
        return v


# Utility functions for common queries


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


# Index creation helper
async def create_custom_indexes(engine):
    """Create custom compound indexes for better performance"""

    # Compound indexes for common queries
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

    # Unique compound indexes
    await engine.get_collection(Commit).create_index(
        [("repository_id", 1), ("hash", 1)], unique=True
    )

    await engine.get_collection(Technology).create_index(
        [("repository_id", 1), ("name", 1), ("category", 1)], unique=True
    )

    await engine.get_collection(ModelBenchmark).create_index(
        [("model_id", 1), ("benchmark_name", 1), ("benchmark_version", 1)], unique=True
    )
