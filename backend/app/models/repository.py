# app/models/repository.py (SQLite compatible - fixed JSONB issue)
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


# Use string UUIDs for SQLite compatibility
def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    avatar_url = Column(Text)
    github_token = Column(Text)  # Store encrypted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    repositories = relationship(
        "Repository", back_populates="user", cascade="all, delete-orphan"
    )
    analysis_sessions = relationship("AnalysisSession", back_populates="user")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )  # Made nullable for now
    url = Column(String(500), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    default_branch = Column(String(100), default="main")
    total_commits = Column(Integer, default=0)
    first_commit_date = Column(DateTime)
    last_commit_date = Column(DateTime)
    last_analyzed = Column(DateTime)
    status = Column(
        String(50), default="pending", index=True
    )  # pending, analyzing, completed, failed
    repo_metadata = Column(JSON, default={})  # Changed from JSONB to JSON for SQLite
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


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )  # Made nullable
    status = Column(
        String(50), default="running"
    )  # running, completed, failed, cancelled
    commits_analyzed = Column(Integer, default=0)
    patterns_found = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    configuration = Column(JSON, default={})  # Changed from JSONB to JSON
    error_message = Column(Text)

    # Relationships
    repository = relationship("Repository", back_populates="analysis_sessions")
    user = relationship("User", back_populates="analysis_sessions")
    insights = relationship("Insight", back_populates="analysis_session")


class Commit(Base):
    __tablename__ = "commits"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    commit_hash = Column(String(40), unique=True, nullable=False, index=True)
    author_name = Column(String(255))
    author_email = Column(String(255), index=True)
    committed_date = Column(DateTime, nullable=False, index=True)
    message = Column(Text)
    files_changed_count = Column(Integer, default=0)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    repository = relationship("Repository", back_populates="commits")
    file_changes = relationship(
        "FileChange", back_populates="commit", cascade="all, delete-orphan"
    )
    pattern_occurrences = relationship("PatternOccurrence", back_populates="commit")


class FileChange(Base):
    __tablename__ = "file_changes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    commit_id = Column(
        String(36), ForeignKey("commits.id", ondelete="CASCADE"), nullable=False
    )
    file_path = Column(Text, nullable=False, index=True)
    old_path = Column(Text)  # For renames
    change_type = Column(
        String(20), nullable=False
    )  # added, modified, deleted, renamed
    language = Column(String(50), index=True)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    patch = Column(Text)  # Store the actual diff
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    commit = relationship("Commit", back_populates="file_changes")


class Technology(Base):
    __tablename__ = "technologies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), index=True)  # language, framework, library, tool
    version = Column(String(50))
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    usage_count = Column(Integer, default=1)
    tech_metadata = Column(JSON, default={})  # Changed from JSONB to JSON

    # Relationships
    repository = relationship("Repository", back_populates="technologies")
    timeline_entries = relationship("TechnologyTimeline", back_populates="technology")


class TechnologyTimeline(Base):
    __tablename__ = "technology_timeline"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    technology_id = Column(
        String(36), ForeignKey("technologies.id", ondelete="CASCADE"), nullable=False
    )
    date = Column(DateTime, nullable=False, index=True)
    commit_count = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    complexity_score = Column(Float, default=0.0)

    # Relationships
    technology = relationship("Technology", back_populates="timeline_entries")


class Pattern(Base):
    __tablename__ = "patterns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    complexity_level = Column(String(20), default="intermediate")
    detection_rules = Column(JSON, default={})  # Changed from JSONB to JSON
    is_antipattern = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    occurrences = relationship("PatternOccurrence", back_populates="pattern")


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
    file_path = Column(Text, nullable=False)
    line_number = Column(Integer)
    code_snippet = Column(Text)
    confidence_score = Column(Float, default=1.0)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    pattern = relationship("Pattern", back_populates="occurrences")
    repository = relationship("Repository", back_populates="pattern_occurrences")
    commit = relationship("Commit", back_populates="pattern_occurrences")


class Insight(Base):
    __tablename__ = "insights"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_session_id = Column(
        String(36), ForeignKey("analysis_sessions.id", ondelete="CASCADE")
    )
    repository_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    type = Column(
        String(50), nullable=False, index=True
    )  # recommendation, warning, achievement, trend
    title = Column(String(255), nullable=False)
    description = Column(Text)
    data = Column(JSON, default={})  # Changed from JSONB to JSON
    severity = Column(String(20), default="info", index=True)  # info, warning, critical
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis_session = relationship("AnalysisSession", back_populates="insights")
