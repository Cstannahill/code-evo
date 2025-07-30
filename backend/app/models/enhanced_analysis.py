"""
Enhanced Analysis Data Models

Comprehensive Pydantic models for all analysis results including
security, performance, architectural, and ensemble analysis.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


class AnalysisType(str, Enum):
    """Types of analysis performed"""
    PATTERN = "pattern"
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    EVOLUTION = "evolution"


class RiskLevel(str, Enum):
    """Security risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PerformanceGrade(str, Enum):
    """Performance grades"""
    EXCELLENT = "A+"
    GOOD = "A"
    FAIR = "B"
    POOR = "C"
    CRITICAL = "D"


class ArchitecturalStyle(str, Enum):
    """Architectural styles"""
    MONOLITHIC = "monolithic"
    MICROSERVICES = "microservices"
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    EVENT_DRIVEN = "event_driven"
    PIPE_FILTER = "pipe_filter"
    MVC = "mvc"
    MVP = "mvp"
    MVVM = "mvvm"
    CLEAN_ARCHITECTURE = "clean_architecture"
    UNKNOWN = "unknown"


class ConsensusMethod(str, Enum):
    """AI ensemble consensus methods"""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    CONFIDENCE_BASED = "confidence_based"
    BEST_SCORE = "best_score"


# Security Analysis Models

class SecurityVulnerability(BaseModel):
    """Individual security vulnerability"""
    vulnerability_type: str
    description: str
    severity: RiskLevel
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    cve_references: List[str] = Field(default_factory=list)
    owasp_category: Optional[str] = None
    remediation: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class SecurityAnalysisResult(BaseModel):
    """Complete security analysis result"""
    overall_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    total_vulnerabilities: int = Field(ge=0)
    vulnerabilities_by_severity: Dict[RiskLevel, int] = Field(default_factory=dict)
    vulnerabilities: List[SecurityVulnerability] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    owasp_coverage: Dict[str, int] = Field(default_factory=dict)
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Performance Analysis Models

class PerformanceIssue(BaseModel):
    """Individual performance issue"""
    issue_type: str
    description: str
    severity: str  # "critical", "high", "medium", "low"
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    performance_impact: str  # "high", "medium", "low"
    optimization_suggestion: Optional[str] = None
    complexity_estimate: Optional[str] = None  # "O(n)", "O(n²)", etc.


class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    cyclomatic_complexity: Optional[float] = None
    cognitive_complexity: Optional[float] = None
    algorithmic_complexity: Optional[str] = None
    memory_efficiency_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    cpu_efficiency_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    io_efficiency_score: Optional[float] = Field(None, ge=0.0, le=100.0)


class PerformanceAnalysisResult(BaseModel):
    """Complete performance analysis result"""
    overall_score: int = Field(ge=0, le=100)
    performance_grade: PerformanceGrade
    total_issues: int = Field(ge=0)
    issues_by_severity: Dict[str, int] = Field(default_factory=dict)
    issues: List[PerformanceIssue] = Field(default_factory=list)
    metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    optimizations: List[str] = Field(default_factory=list)
    bottlenecks: List[str] = Field(default_factory=list)
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Architectural Analysis Models

class DesignPattern(BaseModel):
    """Detected design pattern"""
    name: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    locations: List[str] = Field(default_factory=list)  # File paths where found
    implementation_quality: Optional[str] = None  # "excellent", "good", "fair", "poor"


class QualityMetrics(BaseModel):
    """Code quality metrics"""
    overall_score: int = Field(ge=0, le=100)
    modularity: float = Field(ge=0.0, le=1.0)
    coupling: float = Field(ge=0.0, le=1.0)  # Lower is better
    cohesion: float = Field(ge=0.0, le=1.0)  # Higher is better
    complexity: float = Field(ge=0.0, le=1.0)  # Lower is better
    maintainability: float = Field(ge=0.0, le=1.0)
    testability: float = Field(ge=0.0, le=1.0)
    grade: str  # "A+", "A", "B", "C", "D", "F"


class ArchitecturalAnalysisResult(BaseModel):
    """Complete architectural analysis result"""
    architectural_style: Dict[str, Any] = Field(default_factory=dict)  # Style info with confidence
    design_patterns: List[DesignPattern] = Field(default_factory=list)
    quality_metrics: QualityMetrics = Field(default_factory=QualityMetrics)
    component_analysis: Dict[str, Any] = Field(default_factory=dict)
    dependency_analysis: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    architecture_smells: List[str] = Field(default_factory=list)
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Enhanced Pattern Analysis Models

class PatternAnalysisResult(BaseModel):
    """Enhanced pattern analysis result"""
    detected_patterns: List[str] = Field(default_factory=list)
    ai_patterns: List[str] = Field(default_factory=list)
    combined_patterns: List[str] = Field(default_factory=list)
    complexity_score: float = Field(ge=1.0, le=10.0)
    skill_level: str  # "beginner", "intermediate", "advanced"
    suggestions: List[str] = Field(default_factory=list)
    pattern_confidence: Dict[str, float] = Field(default_factory=dict)
    ai_powered: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QualityAnalysisResult(BaseModel):
    """Enhanced quality analysis result"""
    quality_score: float = Field(ge=0.0, le=100.0)
    readability: str
    issues: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    ai_powered: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Ensemble Analysis Models

class ModelResult(BaseModel):
    """Result from individual AI model"""
    model_id: str
    model_type: str
    result: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    execution_time: float = Field(ge=0.0)
    success: bool
    error: Optional[str] = None


class EnsembleMetadata(BaseModel):
    """Metadata from ensemble analysis"""
    models_used: List[str] = Field(default_factory=list)
    consensus_confidence: float = Field(ge=0.0, le=1.0)
    consensus_method: ConsensusMethod
    total_execution_time: float = Field(ge=0.0)
    individual_confidences: List[float] = Field(default_factory=list)
    model_agreement: Optional[float] = Field(None, ge=0.0, le=1.0)


# Evolution Analysis Models

class EvolutionAnalysisResult(BaseModel):
    """Code evolution analysis result"""
    complexity_change: str  # "increased", "decreased", "stable"
    new_patterns: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    learning_insights: str
    skill_progression: Optional[str] = None  # "improving", "stable", "declining"
    technical_debt_change: Optional[str] = None  # "increased", "decreased", "stable"
    ai_powered: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Incremental Analysis Models

class FileChange(BaseModel):
    """File change for incremental analysis"""
    file_path: str
    change_type: str  # "added", "modified", "deleted", "renamed"
    old_path: Optional[str] = None
    content_hash: Optional[str] = None
    size: Optional[int] = None
    modified_time: Optional[datetime] = None


class IncrementalAnalysisMetadata(BaseModel):
    """Metadata for incremental analysis"""
    changes_analyzed: int = Field(ge=0)
    change_types: List[str] = Field(default_factory=list)
    no_changes: bool = False
    cached_results: bool = False
    full_reanalysis_triggered: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Comprehensive Analysis Result

class ComprehensiveAnalysisResult(BaseModel):
    """Complete analysis result with all components"""
    # Basic repository information
    repo_info: Dict[str, Any] = Field(default_factory=dict)
    technologies: Dict[str, Any] = Field(default_factory=dict)
    commits: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Pattern analysis
    pattern_analyses: List[PatternAnalysisResult] = Field(default_factory=list)
    
    # Quality analysis
    quality_analyses: List[QualityAnalysisResult] = Field(default_factory=list)
    
    # Security analysis
    security_analyses: List[SecurityAnalysisResult] = Field(default_factory=list)
    
    # Performance analysis
    performance_analyses: List[PerformanceAnalysisResult] = Field(default_factory=list)
    
    # Architectural analysis
    architecture_analysis: Optional[ArchitecturalAnalysisResult] = None
    
    # Evolution analysis
    evolution_analyses: List[EvolutionAnalysisResult] = Field(default_factory=list)
    
    # Insights and recommendations
    insights: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    ensemble_metadata: Optional[EnsembleMetadata] = None
    incremental_analysis: Optional[IncrementalAnalysisMetadata] = None
    analysis_duration: Optional[float] = None
    total_candidates: int = Field(default=0, ge=0)
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Error handling
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

    @validator('completed_at', always=True)
    def set_completed_at(cls, v, values):
        """Auto-set completion time if not provided"""
        if v is None and 'error' not in values:
            return datetime.utcnow()
        return v

    @validator('analysis_duration', always=True)
    def calculate_duration(cls, v, values):
        """Calculate analysis duration if not provided"""
        if v is None and 'started_at' in values and 'completed_at' in values:
            if values['completed_at']:
                delta = values['completed_at'] - values['started_at']
                return delta.total_seconds()
        return v


# Analysis Summary Models for Dashboard

class SecuritySummary(BaseModel):
    """Summary of security analysis for dashboard"""
    total_vulnerabilities: int = Field(ge=0)
    critical_count: int = Field(ge=0)
    high_count: int = Field(ge=0)
    medium_count: int = Field(ge=0)
    low_count: int = Field(ge=0)
    overall_risk_level: RiskLevel
    top_vulnerabilities: List[str] = Field(default_factory=list)


class PerformanceSummary(BaseModel):
    """Summary of performance analysis for dashboard"""
    overall_grade: PerformanceGrade
    total_issues: int = Field(ge=0)
    critical_issues: int = Field(ge=0)
    bottlenecks_count: int = Field(ge=0)
    optimization_opportunities: List[str] = Field(default_factory=list)


class ArchitectureSummary(BaseModel):
    """Summary of architectural analysis for dashboard"""
    primary_style: ArchitecturalStyle
    style_confidence: float = Field(ge=0.0, le=1.0)
    design_patterns_count: int = Field(ge=0)
    overall_quality_grade: str
    architecture_smells: List[str] = Field(default_factory=list)


class AnalysisDashboard(BaseModel):
    """Dashboard summary of all analysis results"""
    repo_name: str
    repo_url: str
    branch: str
    last_analyzed: datetime
    
    # High-level metrics
    total_files_analyzed: int = Field(ge=0)
    total_lines_of_code: int = Field(ge=0)
    primary_languages: List[str] = Field(default_factory=list)
    
    # Component summaries
    security_summary: Optional[SecuritySummary] = None
    performance_summary: Optional[PerformanceSummary] = None
    architecture_summary: Optional[ArchitectureSummary] = None
    
    # Overall scores
    overall_quality_score: int = Field(ge=0, le=100)
    overall_security_score: int = Field(ge=0, le=100)
    overall_performance_score: int = Field(ge=0, le=100)
    
    # Trends (compared to previous analysis)
    quality_trend: Optional[str] = None  # "improving", "stable", "declining"
    security_trend: Optional[str] = None
    performance_trend: Optional[str] = None
    
    # Recommendations
    top_recommendations: List[str] = Field(default_factory=list)
    
    # Analysis metadata
    analysis_type: str = "comprehensive"  # "full", "incremental", "cached"
    models_used: List[str] = Field(default_factory=list)
    analysis_duration: float = Field(ge=0.0)


# Configuration Models

class AnalysisConfiguration(BaseModel):
    """Configuration for analysis runs"""
    # Model settings
    use_ensemble: bool = True
    preferred_models: List[str] = Field(default_factory=list)
    consensus_method: ConsensusMethod = ConsensusMethod.CONFIDENCE_BASED
    
    # Analysis settings
    enable_security_analysis: bool = True
    enable_performance_analysis: bool = True
    enable_architecture_analysis: bool = True
    enable_incremental_analysis: bool = True
    
    # Limits
    commit_limit: int = Field(default=100, ge=1)
    candidate_limit: int = Field(default=20, ge=1)
    analysis_timeout: int = Field(default=300, ge=30)  # seconds
    
    # Caching
    enable_caching: bool = True
    cache_ttl: int = Field(default=3600, ge=60)  # seconds
    
    # Quality thresholds
    min_security_score: int = Field(default=70, ge=0, le=100)
    min_performance_score: int = Field(default=70, ge=0, le=100)
    min_quality_score: int = Field(default=70, ge=0, le=100)


# Export all models
__all__ = [
    "AnalysisType",
    "RiskLevel", 
    "PerformanceGrade",
    "ArchitecturalStyle",
    "ConsensusMethod",
    "SecurityVulnerability",
    "SecurityAnalysisResult",
    "PerformanceIssue",
    "PerformanceMetrics",
    "PerformanceAnalysisResult",
    "DesignPattern",
    "QualityMetrics", 
    "ArchitecturalAnalysisResult",
    "PatternAnalysisResult",
    "QualityAnalysisResult",
    "ModelResult",
    "EnsembleMetadata",
    "EvolutionAnalysisResult",
    "FileChange",
    "IncrementalAnalysisMetadata",
    "ComprehensiveAnalysisResult",
    "SecuritySummary",
    "PerformanceSummary",
    "ArchitectureSummary",
    "AnalysisDashboard",
    "AnalysisConfiguration"
]