# app/schemas/repository.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class RepositoryCreate(BaseModel):
    url: str
    branch: Optional[str] = "main"


class RepositoryResponse(BaseModel):
    id: str
    url: str
    name: str
    status: str
    total_commits: int
    first_commit_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None
    last_analyzed: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    repository_id: str
    status: str
    analysis_session: Dict[str, Any]
    technologies: Dict[str, List[Dict]]
    patterns: List[Dict]
    insights: List[Dict]


class TimelineResponse(BaseModel):
    repository_id: str
    timeline: List[Dict[str, Any]]


class PatternOccurrenceResponse(BaseModel):
    pattern_name: str
    file_path: str
    code_snippet: Optional[str] = None
    confidence_score: float
    detected_at: datetime


class TechnologyResponse(BaseModel):
    name: str
    category: str
    first_seen: datetime
    usage_count: int


class InsightResponse(BaseModel):
    type: str
    title: str
    description: str
    data: Dict[str, Any]
    severity: str = "info"
