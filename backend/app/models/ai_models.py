"""
Centralized AI Analysis Models

This module consolidates all AI-related Pydantic models to eliminate duplication
and provide a single source of truth for AI analysis data structures.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from pydantic import field_validator, model_validator
from bson import ObjectId


class AIModelType(str, Enum):
    """Types of AI models"""

    LOCAL_LLM = "local_llm"  # Ollama local models
    OPENAI_API = "openai_api"  # OpenAI API models
    ANTHROPIC_API = "anthropic_api"  # Claude API models
    FALLBACK = "fallback"  # Rule-based fallback


class AnalysisType(str, Enum):
    """Types of analysis performed"""

    PATTERN = "pattern"
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    EVOLUTION = "evolution"
    COMPREHENSIVE = "comprehensive"
    INCREMENTAL = "incremental"


class RiskLevel(str, Enum):
    """Risk levels for analysis results"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class QualityGrade(str, Enum):
    """Quality assessment grades"""

    EXCELLENT = "A+"
    GOOD = "A"
    FAIR = "B"
    POOR = "C"
    CRITICAL = "D"


# Core AI Analysis Models


class PatternAnalysis(BaseModel):
    """Pattern analysis result

    Some LLM outputs may omit non-essential fields like `confidence` or
    `processing_time`. Make those fields optional so parsers remain
    tolerant of partial responses from language models.
    """

    patterns: List[str] = Field(description="Detected code patterns")
    # Optional overall confidence score (0.0 - 1.0). LLM may omit this field.
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Overall confidence score"
    )
    complexity_score: float = Field(
        ge=0.0, le=10.0, description="Code complexity score"
    )
    suggestions: List[str] = Field(description="Improvement suggestions")
    # Optional processing time in seconds. LLM outputs may not include it.
    processing_time: Optional[float] = Field(
        default=None, description="Analysis processing time in seconds"
    )
    token_usage: Optional[Dict[str, Any]] = Field(
        default=None, description="Token usage information"
    )


class CodeQualityAnalysis(BaseModel):
    """Code quality analysis result"""

    quality_score: float = Field(ge=0.0, le=100.0, description="Overall quality score")
    maintainability: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Maintainability score"
    )
    # Readability is expressed as a human-friendly string in some parsers
    readability: str = Field(default="Unknown", description="Readability assessment")
    testability: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Testability score"
    )
    issues_found: List[str] = Field(
        default_factory=list, description="List of quality issues"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )

    # Backwards compatible fields used by older service code
    issues: List[str] = Field(
        default_factory=list, description="List of quality issues (alias)"
    )
    improvements: List[str] = Field(
        default_factory=list, description="Improvement recommendations (alias)"
    )

    @field_validator("issues", mode="before")
    def _sync_issues(cls, v):
        # In Pydantic v2's 'before' mode, we can't access other fields
        # The synchronization will be handled in the model_validator
        return v

    @field_validator("improvements", mode="before")
    def _sync_improvements(cls, v):
        # In Pydantic v2's 'before' mode, we can't access other fields
        # The synchronization will be handled in the model_validator
        return v

    @model_validator(mode="after")
    def _sync_alias_fields(self):
        """Synchronize alias fields after validation"""
        # Sync issues alias - prefer issues_found if both are provided
        if not self.issues and self.issues_found:
            self.issues = self.issues_found.copy()
        elif not self.issues_found and self.issues:
            self.issues_found = self.issues.copy()
        elif self.issues_found and self.issues:
            # Both provided, keep both but ensure they're consistent
            pass
        
        # Sync improvements alias - prefer recommendations if both are provided
        if not self.improvements and self.recommendations:
            self.improvements = self.recommendations.copy()
        elif not self.recommendations and self.improvements:
            self.recommendations = self.improvements.copy()
        elif self.recommendations and self.improvements:
            # Both provided, keep both but ensure they're consistent
            pass
        
        return self


class EvolutionAnalysis(BaseModel):
    """Code evolution analysis result"""

    evolution_trend: str = Field(default="", description="Overall evolution trend")
    complexity_change: str = Field(
        default="stable", description="Complexity change over time"
    )
    refactoring_frequency: float = Field(
        default=0.0, description="Refactoring frequency"
    )
    technical_debt: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Technical debt score"
    )
    improvement_areas: List[str] = Field(
        default_factory=list, description="Areas for improvement"
    )

    # Backwards compatible fields expected by ai_service
    new_patterns: List[str] = Field(
        default_factory=list, description="New patterns observed"
    )
    improvements: List[str] = Field(
        default_factory=list, description="List of improvements"
    )
    learning_insights: str = Field(
        default="", description="Summary insight about learning"
    )

    @field_validator("new_patterns", mode="before")
    def _sync_new_patterns(cls, v):
        # In Pydantic v2's 'before' mode, we can't access other fields
        # The synchronization will be handled in the model_validator
        return v

    @field_validator("improvements", mode="before")
    def _sync_improvements_evo(cls, v):
        # In Pydantic v2's 'before' mode, we can't access other fields
        # The synchronization will be handled in the model_validator
        return v

    @model_validator(mode="after")
    def _sync_alias_fields(self):
        """Synchronize alias fields after validation"""
        # Sync new_patterns alias - prefer improvement_areas if both are provided
        if not self.new_patterns and self.improvement_areas:
            self.new_patterns = self.improvement_areas.copy()
        elif not self.improvement_areas and self.new_patterns:
            self.improvement_areas = self.new_patterns.copy()
        elif self.improvement_areas and self.new_patterns:
            # Both provided, keep both but ensure they're consistent
            pass
        
        # Sync improvements alias - prefer improvement_areas if both are provided
        if not self.improvements and self.improvement_areas:
            self.improvements = self.improvement_areas.copy()
        elif not self.improvement_areas and self.improvements:
            self.improvement_areas = self.improvements.copy()
        elif self.improvement_areas and self.improvements:
            # Both provided, keep both but ensure they're consistent
            pass
        
        return self


class SecurityAnalysis(BaseModel):
    """Security analysis result"""

    security_score: float = Field(
        ge=0.0, le=100.0, description="Overall security score"
    )
    vulnerabilities: List[Dict[str, Any]] = Field(
        description="Security vulnerabilities found"
    )
    risk_level: RiskLevel = Field(description="Overall risk level")
    recommendations: List[str] = Field(description="Security recommendations")


class PerformanceAnalysis(BaseModel):
    """Performance analysis result"""

    performance_score: float = Field(
        ge=0.0, le=100.0, description="Overall performance score"
    )
    bottlenecks: List[str] = Field(description="Performance bottlenecks identified")
    optimization_opportunities: List[str] = Field(
        description="Optimization opportunities"
    )
    grade: QualityGrade = Field(description="Performance grade")


class ArchitecturalAnalysis(BaseModel):
    """Architectural analysis result"""

    architecture_style: str = Field(description="Detected architectural style")
    coupling_score: float = Field(ge=0.0, le=100.0, description="Coupling assessment")
    cohesion_score: float = Field(ge=0.0, le=100.0, description="Cohesion assessment")
    design_patterns: List[str] = Field(description="Design patterns identified")
    architectural_debt: float = Field(
        ge=0.0, le=100.0, description="Architectural debt score"
    )


# Comprehensive Analysis Models


class ComprehensiveAnalysisResult(BaseModel):
    """Comprehensive analysis combining all analysis types"""

    analysis_id: str = Field(description="Unique analysis identifier")
    repository_id: str = Field(description="Repository identifier")
    analysis_type: AnalysisType = Field(description="Type of analysis performed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )

    # Individual analysis results
    pattern_analysis: Optional[PatternAnalysis] = None
    quality_analysis: Optional[CodeQualityAnalysis] = None
    evolution_analysis: Optional[EvolutionAnalysis] = None
    security_analysis: Optional[SecurityAnalysis] = None
    performance_analysis: Optional[PerformanceAnalysis] = None
    architectural_analysis: Optional[ArchitecturalAnalysis] = None

    # Overall metrics
    overall_score: float = Field(ge=0.0, le=100.0, description="Overall analysis score")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence score")
    processing_time: float = Field(description="Total processing time in seconds")

    # Metadata
    models_used: List[str] = Field(description="AI models used in analysis")
    analysis_config: Dict[str, Any] = Field(description="Analysis configuration")
    error_details: Optional[Dict[str, Any]] = Field(
        default=None, description="Error details if any"
    )


# ModelComparisonResult removed - using single model analysis only


# Request/Response Models for API


class AnalysisRequest(BaseModel):
    """Request model for starting an analysis"""

    repository_url: str = Field(description="Repository URL to analyze")
    branch: str = Field(default="main", description="Branch to analyze")
    analysis_type: AnalysisType = Field(description="Type of analysis to perform")
    models: List[str] = Field(description="AI models to use for analysis")
    commit_limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum commits to analyze"
    )
    include_security: bool = Field(
        default=True, description="Include security analysis"
    )
    include_performance: bool = Field(
        default=True, description="Include performance analysis"
    )
    include_architecture: bool = Field(
        default=True, description="Include architectural analysis"
    )


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""

    analysis_id: str = Field(description="Unique analysis identifier")
    repository_id: str = Field(description="Repository identifier")
    status: str = Field(description="Analysis status")
    progress: float = Field(
        ge=0.0, le=100.0, description="Analysis progress percentage"
    )
    results: Optional[ComprehensiveAnalysisResult] = Field(
        default=None, description="Analysis results"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if analysis failed"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Analysis completion time"
    )


class ModelSelectionRequest(BaseModel):
    """Request model for model selection"""

    models: List[str] = Field(description="Selected AI models")
    analysis_type: AnalysisType = Field(description="Type of analysis to perform")
    repository_url: Optional[str] = Field(
        default=None, description="Repository URL for analysis"
    )
    branch: str = Field(default="main", description="Branch to analyze")
    commit_limit: int = Field(
        default=50, ge=1, le=1000, description="Maximum commits to analyze"
    )


# ModelComparisonResponse removed - using single model analysis only


# Ensemble and Multi-Model Models


class EnsembleMetadata(BaseModel):
    """Metadata for ensemble analysis"""

    models_used: List[str] = Field(description="Models used in ensemble")
    consensus_method: str = Field(description="Consensus building method")
    confidence_threshold: float = Field(
        ge=0.0, le=1.0, description="Confidence threshold"
    )
    fallback_used: bool = Field(default=False, description="Whether fallback was used")
    ensemble_score: float = Field(
        ge=0.0, le=1.0, description="Ensemble confidence score"
    )


class IncrementalAnalysisMetadata(BaseModel):
    """Metadata for incremental analysis"""

    previous_analysis_id: Optional[str] = Field(
        default=None, description="Previous analysis ID"
    )
    files_changed: List[str] = Field(
        description="Files that changed since last analysis"
    )
    commits_analyzed: List[str] = Field(description="Commits analyzed in this run")
    efficiency_ratio: float = Field(ge=0.0, description="Analysis efficiency ratio")
    time_saved: float = Field(
        ge=0.0, description="Time saved compared to full analysis"
    )


# Validation and Configuration Models


class AnalysisConfig(BaseModel):
    """Configuration for analysis parameters"""

    max_commits: int = Field(
        default=100, ge=1, le=1000, description="Maximum commits to analyze"
    )
    max_files: int = Field(
        default=1000, ge=1, le=10000, description="Maximum files to analyze"
    )
    timeout_seconds: int = Field(
        default=300, ge=30, le=3600, description="Analysis timeout"
    )
    parallel_processing: bool = Field(
        default=True, description="Enable parallel processing"
    )
    cache_results: bool = Field(default=True, description="Cache analysis results")
    include_metadata: bool = Field(
        default=True, description="Include metadata in results"
    )


class ModelConfig(BaseModel):
    """Configuration for AI model usage"""

    model_name: str = Field(description="AI model name")
    provider: str = Field(description="Model provider")
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Model temperature"
    )
    max_tokens: int = Field(
        default=4000, ge=100, le=32000, description="Maximum tokens"
    )
    timeout_seconds: int = Field(default=60, ge=10, le=300, description="Model timeout")
    retry_attempts: int = Field(default=3, ge=1, le=5, description="Retry attempts")
    fallback_enabled: bool = Field(
        default=True, description="Enable fallback mechanisms"
    )
