# app/models/repository.py - ENHANCED WITH MULTI-MODEL SUPPORT
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

Base = declarative_base()


class Repository(Base):
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
        "Commit", back_populates="repository", cascade="all, delete-orphan"
    )
    technologies = relationship(
        "Technology", back_populates="repository", cascade="all, delete-orphan"
    )
    analysis_sessions = relationship(
        "AnalysisSession", back_populates="repository", cascade="all, delete-orphan"
    )
    pattern_occurrences = relationship(
        "PatternOccurrence", back_populates="repository", cascade="all, delete-orphan"
    )
    model_comparisons = relationship(
        "ModelComparison", back_populates="repository", cascade="all, delete-orphan"
    )


class Commit(Base):
    __tablename__ = "commits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"))
    hash = Column(String, nullable=False, index=True)
    author_name = Column(String)
    author_email = Column(String)
    committed_date = Column(DateTime)
    message = Column(Text)
    stats = Column(JSON)  # additions, deletions, files

    # Relationships
    repository = relationship("Repository", back_populates="commits")
    file_changes = relationship(
        "FileChange", back_populates="commit", cascade="all, delete-orphan"
    )
    pattern_occurrences = relationship(
        "PatternOccurrence", back_populates="commit", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("repository_id", "hash", name="uq_repo_commit_hash"),
        Index("idx_commit_date", "committed_date"),
    )


class FileChange(Base):
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
    commit = relationship("Commit", back_populates="file_changes")


class Technology(Base):
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
    repository = relationship("Repository", back_populates="technologies")

    __table_args__ = (
        UniqueConstraint("repository_id", "name", "category", name="uq_repo_tech"),
        Index("idx_tech_category", "category"),
    )


class Pattern(Base):
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
        "PatternOccurrence", back_populates="pattern", cascade="all, delete-orphan"
    )


class PatternOccurrence(Base):
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
    repository = relationship("Repository", back_populates="pattern_occurrences")
    pattern = relationship("Pattern", back_populates="occurrences")
    commit = relationship("Commit", back_populates="pattern_occurrences")

    __table_args__ = (
        Index("idx_pattern_occurrence_repo", "repository_id"),
        Index("idx_pattern_occurrence_pattern", "pattern_id"),
        Index("idx_pattern_occurrence_detected", "detected_at"),
        Index("idx_pattern_occurrence_model", "ai_model_used"),
    )


class AnalysisSession(Base):
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
    repository = relationship("Repository", back_populates="analysis_sessions")
    ai_analysis_results = relationship(
        "AIAnalysisResult",
        back_populates="analysis_session",
        cascade="all, delete-orphan",
    )


# NEW MODELS FOR MULTI-MODEL SUPPORT


class AIModel(Base):
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
    strengths = Column(ARRAY(String))  # List of model strengths
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)

    # Relationships
    analysis_results = relationship(
        "AIAnalysisResult", back_populates="model", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_ai_model_provider", "provider"),
        Index("idx_ai_model_available", "is_available"),
    )


class AIAnalysisResult(Base):
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
    detected_patterns = Column(ARRAY(String))  # List of pattern names
    complexity_score = Column(Float)
    skill_level = Column(String)  # beginner, intermediate, advanced
    suggestions = Column(ARRAY(String))  # List of suggestions
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
        "AnalysisSession", back_populates="ai_analysis_results"
    )
    model = relationship("AIModel", back_populates="analysis_results")

    __table_args__ = (
        Index("idx_ai_result_session", "analysis_session_id"),
        Index("idx_ai_result_model", "model_id"),
        Index("idx_ai_result_created", "created_at"),
    )


class ModelComparison(Base):
    __tablename__ = "model_comparisons"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"))

    # Comparison details
    models_compared = Column(ARRAY(String), nullable=False)  # List of model names
    analysis_type = Column(
        String, default="comparison"
    )  # comparison, benchmark, evaluation

    # Comparison results
    consensus_patterns = Column(ARRAY(String))  # Patterns all models agreed on
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
    repository = relationship("Repository", back_populates="model_comparisons")

    __table_args__ = (
        Index("idx_model_comparison_repo", "repository_id"),
        Index("idx_model_comparison_created", "created_at"),
        Index("idx_model_comparison_models", "models_compared"),
    )


class ModelBenchmark(Base):
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
    model = relationship("AIModel")

    __table_args__ = (
        Index("idx_benchmark_model", "model_id"),
        Index("idx_benchmark_name", "benchmark_name"),
        Index("idx_benchmark_date", "benchmark_date"),
        UniqueConstraint(
            "model_id", "benchmark_name", "benchmark_version", name="uq_model_benchmark"
        ),
    )
