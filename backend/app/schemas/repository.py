# app/schemas/repository.py - Updated for MongoDB/ODMantic
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId


class RepositoryCreate(BaseModel):
    url: str
    branch: Optional[str] = "main"


class RepositoryResponse(BaseModel):
    id: str = Field(alias="_id")  # Handle MongoDB ObjectId
    url: str
    name: str
    status: str
    total_commits: int
    first_commit_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None
    last_analyzed: Optional[datetime] = None
    created_at: datetime

    class Config:
        populate_by_name = True  # Allow both _id and id
        json_encoders = {ObjectId: str}  # Convert ObjectId to string in JSON

    @validator("id", pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class AnalysisResponse(BaseModel):
    repository_id: str
    status: str
    analysis_session: Dict[str, Any]
    technologies: Dict[str, List[Dict]]
    patterns: List[Dict]
    insights: List[Dict]

    @validator("repository_id", pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class TimelineResponse(BaseModel):
    repository_id: str
    timeline: List[Dict[str, Any]]

    @validator("repository_id", pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    @validator("timeline", pre=True)
    def convert_timeline_objectids(cls, v):
        # Recursively convert ObjectIds in timeline dicts to str
        def convert(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            if isinstance(obj, dict):
                return {k: convert(val) for k, val in obj.items()}
            if isinstance(obj, list):
                return [convert(i) for i in obj]
            return obj
        return convert(v)


class PatternOccurrenceResponse(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    pattern_name: str
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None
    confidence_score: float
    detected_at: datetime
    ai_model_used: Optional[str] = None  # New field from MongoDB model
    model_confidence: Optional[float] = None  # New field from MongoDB model
    repository_id: Optional[str] = None
    pattern_id: Optional[str] = None
    commit_id: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

    @validator("id", "repository_id", "pattern_id", "commit_id", pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class TechnologyResponse(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    category: Optional[str] = None
    version: Optional[str] = None  # New field from MongoDB model
    first_seen: datetime
    last_seen: datetime  # New field from MongoDB model
    usage_count: int
    tech_metadata: Optional[Dict[str, Any]] = None  # New field from MongoDB model

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

    @validator("id", pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class InsightResponse(BaseModel):
    type: str
    title: str
    description: str
    data: Dict[str, Any]
    severity: str = "info"


# New schemas for multi-model AI features


class AIModelResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    display_name: str
    provider: str
    model_type: str
    context_window: Optional[int] = None
    cost_per_1k_tokens: float
    strengths: List[str]
    is_available: bool
    usage_count: int
    last_used: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

    @validator("id", pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class AIAnalysisResultResponse(BaseModel):
    id: str = Field(alias="_id")
    model_name: str  # Will be populated from joined model data
    code_snippet: str
    language: Optional[str] = None
    detected_patterns: List[str]
    complexity_score: Optional[float] = None
    skill_level: Optional[str] = None
    suggestions: List[str]
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    cost_estimate: float
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

    @validator("id", pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class ModelComparisonResponse(BaseModel):
    id: str = Field(alias="_id")
    repository_id: str
    models_compared: List[str]
    analysis_type: str
    consensus_patterns: List[str]
    disputed_patterns: Optional[Dict[str, Any]] = None
    agreement_score: Optional[float] = None
    diversity_score: Optional[float] = None
    consistency_score: Optional[float] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

    @validator("id", "repository_id", pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class AnalysisSessionResponse(BaseModel):
    id: str = Field(alias="_id")
    repository_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    commits_analyzed: int
    patterns_found: int
    configuration: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

    @validator("id", "repository_id", pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


# Create schemas for requests


class AIModelCreate(BaseModel):
    name: str
    display_name: str
    provider: str
    model_type: str = "code_analysis"
    context_window: Optional[int] = None
    cost_per_1k_tokens: float = 0.0
    strengths: List[str] = []


class ModelComparisonCreate(BaseModel):
    repository_id: str
    models_compared: List[str]
    analysis_type: str = "comparison"
    configuration: Optional[Dict[str, Any]] = None


class AnalysisSessionCreate(BaseModel):
    repository_id: str
    configuration: Optional[Dict[str, Any]] = None


# Enhanced responses with additional computed fields


class RepositoryDetailResponse(RepositoryResponse):
    """Extended repository response with additional computed data"""

    technology_count: int = 0
    pattern_count: int = 0
    latest_analysis_session: Optional[AnalysisSessionResponse] = None
    top_technologies: List[TechnologyResponse] = []
    recent_patterns: List[PatternOccurrenceResponse] = []


class ComprehensiveAnalysisResponse(BaseModel):
    """Complete analysis response with all related data"""

    repository: RepositoryResponse
    analysis_session: AnalysisSessionResponse
    technologies: List[TechnologyResponse]
    patterns: List[PatternOccurrenceResponse]
    ai_results: List[AIAnalysisResultResponse]
    model_comparisons: List[ModelComparisonResponse]
    insights: List[InsightResponse]
    timeline: List[Dict[str, Any]]


# Utility functions for schema conversion


def convert_repository_to_response(
    repo_doc: dict, **extra_fields
) -> RepositoryResponse:
    """Convert MongoDB document to RepositoryResponse"""
    repo_data = {
        "id": str(repo_doc["_id"]),
        "url": repo_doc["url"],
        "name": repo_doc["name"],
        "status": repo_doc["status"],
        "total_commits": repo_doc["total_commits"],
        "last_analyzed": repo_doc.get("last_analyzed"),
        "created_at": repo_doc["created_at"],
        **extra_fields,
    }
    return RepositoryResponse(**repo_data)


def convert_pattern_occurrence_to_response(
    pattern_doc: dict, pattern_name: str
) -> PatternOccurrenceResponse:
    """Convert MongoDB PatternOccurrence document to response"""
    return PatternOccurrenceResponse(
        id=str(pattern_doc["_id"]),
        pattern_name=pattern_name,
        file_path=pattern_doc.get("file_path"),
        code_snippet=pattern_doc.get("code_snippet"),
        confidence_score=pattern_doc["confidence_score"],
        detected_at=pattern_doc["detected_at"],
        ai_model_used=pattern_doc.get("ai_model_used"),
        model_confidence=pattern_doc.get("model_confidence"),
    )
