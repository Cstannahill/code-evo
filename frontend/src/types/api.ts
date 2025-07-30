export interface Repository {
  id: string;
  url: string;
  name: string;
  status: "pending" | "analyzing" | "completed" | "failed";
  total_commits: number;
  created_at: string;
  updated_at?: string;
  first_commit_date?: string;
  last_commit_date?: string;
  default_branch?: string; // Added to match backend
  repo_metadata?: unknown; // Added to match backend
  last_analyzed?: string;
}

export interface RepositoryCreateRequest {
  url: string;
  branch?: string;
  model_id?: string; // Add this field
}
export interface AnalysisSession {
  id: string | null;
  repository_id?: string;
  user_id?: string;
  status: string; // running, completed, failed, cancelled
  commits_analyzed: number;
  patterns_found: number;
  started_at: string | null;
  completed_at?: string | null;
  configuration: object;
  error_message?: string | null;
}

export interface Pattern {
  id?: string;
  name: string;
  category: string;
  description?: string;
  complexity_level: string;
  is_antipattern: boolean;
  detection_rules?: object;
  created_at?: string;
}

export interface PatternOccurrence {
  pattern_name: string;
  file_path: string;
  code_snippet?: string;
  confidence_score: number;
  detected_at: string;
  line_number?: number;
}

export interface Technology {
  id: string;
  name: string;
  category:
    | "language"
    | "framework"
    | "library"
    | "tool"
    | "database"
    | "platform"
    | "other";
  first_seen: string | null;
  last_seen: string | null;
  usage_count: number;
  version?: string;
  metadata?: Record<string, unknown>;
}

export interface TechnologiesByCategory {
  language: Technology[];
  framework: Technology[];
  library: Technology[];
  tool: Technology[];
  database: Technology[];
  platform: Technology[];
  other: Technology[];
}

export interface RepositoryAnalysisResponse {
  repository_id: string;
  status: string;
  analysis_session: AnalysisSession;
  technologies: TechnologiesByCategory;
  patterns: PatternOccurrence[];
  pattern_timeline: {
    timeline: Array<{
      date: string;
      patterns: Record<string, number>;
    }>;
    summary: {
      total_months: number;
      patterns_tracked: string[];
    };
  };
  pattern_statistics: Record<
    string,
    {
      name: string;
      category: string;
      occurrences: number;
      complexity_level: string;
      is_antipattern: boolean;
      description?: string;
    }
  >;
  insights: Insight[];
  ai_powered: boolean;
  summary: {
    total_patterns: number;
    antipatterns_detected: number;
    complexity_distribution: Record<string, number>;
  };
}

// Enhanced analysis response with new backend data
export interface EnhancedRepositoryAnalysisResponse extends RepositoryAnalysisResponse {
  // New analysis types from enhanced backend
  pattern_analyses?: PatternAnalysisResult[];
  quality_analyses?: QualityAnalysisResult[];
  security_analyses?: SecurityAnalysisResult[];
  performance_analyses?: PerformanceAnalysisResult[];
  architecture_analysis?: ArchitecturalAnalysisResult;
  evolution_analyses?: EvolutionAnalysisResult[];
  
  // Ensemble and incremental metadata
  ensemble_metadata?: EnsembleMetadata;
  incremental_analysis?: IncrementalAnalysisMetadata;
  
  // Additional metadata
  analysis_duration?: number;
  total_candidates?: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
  warnings?: string[];
}

// New analysis result interfaces matching backend models
export interface SecurityAnalysisResult {
  overall_score: number;
  risk_level: "critical" | "high" | "medium" | "low" | "info";
  total_vulnerabilities: number;
  vulnerabilities_by_severity: Record<string, number>;
  vulnerabilities: SecurityVulnerability[];
  recommendations: string[];
  owasp_coverage: Record<string, number>;
  analysis_metadata: Record<string, any>;
  timestamp: string;
}

export interface SecurityVulnerability {
  vulnerability_type: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  line_number?: number;
  code_snippet?: string;
  cve_references: string[];
  owasp_category?: string;
  remediation?: string;
  confidence: number;
}

export interface PerformanceAnalysisResult {
  overall_score: number;
  performance_grade: "A+" | "A" | "B" | "C" | "D";
  total_issues: number;
  issues_by_severity: Record<string, number>;
  issues: PerformanceIssue[];
  metrics: PerformanceMetrics;
  optimizations: string[];
  bottlenecks: string[];
  analysis_metadata: Record<string, any>;
  timestamp: string;
}

export interface PerformanceIssue {
  issue_type: string;
  description: string;
  severity: string;
  line_number?: number;
  code_snippet?: string;
  performance_impact: string;
  optimization_suggestion?: string;
  complexity_estimate?: string;
}

export interface PerformanceMetrics {
  cyclomatic_complexity?: number;
  cognitive_complexity?: number;
  algorithmic_complexity?: string;
  memory_efficiency_score?: number;
  cpu_efficiency_score?: number;
  io_efficiency_score?: number;
}

export interface ArchitecturalAnalysisResult {
  architectural_style: Record<string, any>;
  design_patterns: DesignPattern[];
  quality_metrics: ArchitecturalQualityMetrics;
  component_analysis: Record<string, any>;
  dependency_analysis: Record<string, any>;
  recommendations: string[];
  architecture_smells: string[];
  analysis_metadata: Record<string, any>;
  timestamp: string;
}

export interface DesignPattern {
  name: string;
  description: string;
  confidence: number;
  locations: string[];
  implementation_quality?: string;
}

export interface ArchitecturalQualityMetrics {
  overall_score: number;
  modularity: number;
  coupling: number;
  cohesion: number;
  complexity: number;
  maintainability: number;
  testability: number;
  grade: string;
}

export interface PatternAnalysisResult {
  detected_patterns: string[];
  ai_patterns: string[];
  combined_patterns: string[];
  complexity_score: number;
  skill_level: string;
  suggestions: string[];
  pattern_confidence: Record<string, number>;
  ai_powered: boolean;
  timestamp: string;
}

export interface QualityAnalysisResult {
  quality_score: number;
  readability: string;
  issues: string[];
  improvements: string[];
  metrics: Record<string, any>;
  ai_powered: boolean;
  timestamp: string;
}

export interface EvolutionAnalysisResult {
  complexity_change: string;
  new_patterns: string[];
  improvements: string[];
  learning_insights: string;
  skill_progression?: string;
  technical_debt_change?: string;
  ai_powered: boolean;
  timestamp: string;
}

export interface EnsembleMetadata {
  models_used: string[];
  consensus_confidence: number;
  consensus_method: string;
  total_execution_time: number;
  individual_confidences: number[];
  model_agreement?: number;
}

export interface IncrementalAnalysisMetadata {
  changes_analyzed: number;
  change_types: string[];
  no_changes: boolean;
  cached_results: boolean;
  full_reanalysis_triggered: boolean;
  timestamp: string;
}

// This is the main interface that components will use
export type RepositoryAnalysis = RepositoryAnalysisResponse;

export interface Insight {
  type:
    | "info"
    | "warning"
    | "achievement"
    | "trend"
    | "recommendation"
    | "ai_analysis"
    | "pattern_summary";
  title: string;
  description: string;
  severity?: "info" | "warning" | "critical";
  data?: Record<string, unknown>;
}

export interface CodeAnalysisResult {
  code: string;
  language: string;
  pattern_analysis: {
    detected_patterns: string[];
    ai_patterns: string[];
    combined_patterns: string[];
    complexity_score: number;
    skill_level: string;
    suggestions: string[];
  };
  quality_analysis: {
    quality_score: number;
    readability: string;
    issues: string[];
    improvements: string[];
  };
  similar_patterns: Array<{
    patterns: string[];
    similarity_score: number;
    language: string;
    complexity: number;
    code_preview: string;
  }>;
  ai_powered: boolean;
  analysis_timestamp: string;
}

// Request interfaces
export interface RepositoryCreate {
  url: string;
  branch?: string;
}

export interface CodeAnalysisRequest {
  code: string;
  language: string;
}

// Timeline interfaces
export interface TimelineEntry {
  date: string;
  commits: number;
  languages: string[];
  technologies: string[];
  patterns: Record<string, number>;
}

export interface TimelineResponse {
  repository_id: string;
  timeline: TimelineEntry[];
  summary: {
    total_months: number;
    total_commits: number;
    languages: string[];
    technologies: string[];
  };
  timestamp: string;
}

// Health check response
export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  services: {
    database: {
      connected: boolean;
      type: string;
      tables: number;
    };
    ai: {
      available: boolean;
      model: string;
    };
    cache: {
      type: string;
      connected: boolean;
    };
    vector_db: {
      type: string;
      connected: boolean;
    };
  };
}

// AI service status response
export interface AIServiceStatus {
  ai_service: {
    ollama_available: boolean;
    ollama_model: string | null;
    embeddings_available: boolean;
    embeddings_model: string | null;
    vector_db_available: boolean;
    timestamp: string;
  };
  recommendations: {
    ollama_missing: string | null;
    ready_for_analysis: boolean;
  };
}
export interface ModelComparisonResult {
  model: string;
  model_info: {
    display_name: string;
    provider: string;
    strengths: string[];
  };
  patterns: string[];
  complexity_score: number;
  skill_level: string;
  suggestions: string[];
  confidence: number;
  processing_time: number;
  token_usage?: {
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
  };
  error?: string;
}
export interface MultiModelComparisonRequest {
  models: string[];
  code: string;
  language?: string;
  repository_id?: string;
}
