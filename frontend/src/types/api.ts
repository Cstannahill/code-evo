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
