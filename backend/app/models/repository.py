# app/models/repository.py - Enhanced with AI model tracking

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
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


# New table for AI model information
class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False)  # e.g., "codellama:7b"
    display_name = Column(String(200), nullable=False)  # e.g., "CodeLlama 7B"
    provider = Column(String(100), nullable=False)  # e.g., "Meta/Ollama"
    model_type = Column(String(50), nullable=False)  # e.g., "local", "api"
    context_window = Column(Integer, default=4096)
    cost_per_1k_tokens = Column(Float, default=0.0)
    strengths = Column(JSON, default=[])  # List of model strengths
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis_results = relationship("AIAnalysisResult", back_populates="model")


# Enhanced AnalysisSession with model tracking
class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    status = Column(String(50), default="running")
    commits_analyzed = Column(Integer, default=0)
    patterns_found = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    configuration = Column(JSON, default={})
    error_message = Column(Text)

    # NEW: Model selection for this analysis
    selected_models = Column(JSON, default=[])  # List of model names used
    is_comparison_analysis = Column(Boolean, default=False)

    # Relationships
    repository = relationship("Repository", back_populates="analysis_sessions")
    user = relationship("User", back_populates="analysis_sessions")
    ai_results = relationship("AIAnalysisResult", back_populates="analysis_session")
    insights = relationship("Insight", back_populates="analysis_session")


# New table for storing AI analysis results per model
class AIAnalysisResult(Base):
    __tablename__ = "ai_analysis_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_session_id = Column(
        String(36),
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_id = Column(
        String(36), ForeignKey("ai_models.id", ondelete="CASCADE"), nullable=False
    )
    repository_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )

    # Analysis results from this specific model
    detected_patterns = Column(JSON, default=[])  # Raw patterns from model
    complexity_score = Column(Float, default=0.0)
    skill_level = Column(String(50), default="intermediate")
    suggestions = Column(JSON, default=[])
    confidence_score = Column(Float, default=0.0)

    # Performance metrics
    processing_time = Column(Float, default=0.0)  # seconds
    token_usage = Column(JSON, default={})  # input/output/total tokens
    cost_estimate = Column(Float, default=0.0)  # USD cost

    # Metadata
    model_version = Column(String(100))  # Track model version
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)  # If analysis failed

    # Relationships
    analysis_session = relationship("AnalysisSession", back_populates="ai_results")
    model = relationship("AIModel", back_populates="analysis_results")
    repository = relationship("Repository")


# Enhanced PatternOccurrence with model attribution
class PatternOccurrence(Base):
    __tablename__ = "pattern_occurrences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    pattern_id = Column(
        String(36), ForeignKey("patterns.id", ondelete="CASCADE"), nullable=False
    )
    repository_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    commit_id = Column(
        String(36), ForeignKey("commits.id", ondelete="CASCADE"), nullable=False
    )

    # NEW: Track which AI model detected this pattern
    detected_by_model_id = Column(
        String(36), ForeignKey("ai_models.id", ondelete="CASCADE")
    )
    ai_analysis_result_id = Column(
        String(36), ForeignKey("ai_analysis_results.id", ondelete="CASCADE")
    )

    file_path = Column(Text, nullable=False)
    line_number = Column(Integer)
    code_snippet = Column(Text)
    confidence_score = Column(Float, default=1.0)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    pattern = relationship("Pattern", back_populates="occurrences")
    repository = relationship("Repository", back_populates="pattern_occurrences")
    commit = relationship("Commit", back_populates="pattern_occurrences")
    detected_by_model = relationship("AIModel")
    ai_analysis_result = relationship("AIAnalysisResult")


# New table for model comparison experiments
class ModelComparison(Base):
    __tablename__ = "model_comparisons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    analysis_session_id = Column(
        String(36),
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Comparison metadata
    models_compared = Column(JSON, default=[])  # List of model IDs
    comparison_type = Column(
        String(50), default="pattern_detection"
    )  # pattern_detection, quality_analysis, etc.

    # Comparison results
    consensus_patterns = Column(JSON, default=[])  # Patterns all models agreed on
    disputed_patterns = Column(JSON, default=[])  # Patterns with disagreement
    model_agreement_score = Column(Float, default=0.0)  # 0-1 how much models agreed

    # Performance comparison
    total_processing_time = Column(Float, default=0.0)
    total_cost_estimate = Column(Float, default=0.0)
    fastest_model = Column(String(36), ForeignKey("ai_models.id"))
    most_accurate_model = Column(String(36), ForeignKey("ai_models.id"))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    repository = relationship("Repository")
    analysis_session = relationship("AnalysisSession")


# Enhanced Repository to track model usage
class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    url = Column(String(500), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    default_branch = Column(String(100), default="main")
    total_commits = Column(Integer, default=0)
    first_commit_date = Column(DateTime)
    last_commit_date = Column(DateTime)
    last_analyzed = Column(DateTime)
    status = Column(String(50), default="pending", index=True)
    repo_metadata = Column(JSON, default={})

    # NEW: Track which models have analyzed this repo
    analyzed_by_models = Column(
        JSON, default=[]
    )  # List of model IDs that analyzed this repo
    preferred_models = Column(JSON, default=[])  # User's preferred models for this repo

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="repositories")
    commits = relationship(
        "Commit", back_populates="repository", cascade="all, delete-orphan"
    )
    analysis_sessions = relationship("AnalysisSession", back_populates="repository")
    technologies = relationship(
        "Technology", back_populates="repository", cascade="all, delete-orphan"
    )
    pattern_occurrences = relationship("PatternOccurrence", back_populates="repository")
