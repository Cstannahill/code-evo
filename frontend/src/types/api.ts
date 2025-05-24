export interface Repository {
  id: string;
  url: string;
  name: string;
  status: "pending" | "analyzing" | "completed" | "failed";
  total_commits: number;
  created_at: string;
  updated_at: string;
  first_commit_date?: string;
  last_commit_date?: string;
  branch?: string;
}

export interface AnalysisSession {
  id: string;
  repository_id: string;
  status: "running" | "completed" | "failed" | "cancelled";
  commits_analyzed: number;
  patterns_found: number;
  started_at: string;
  completed_at?: string;
  configuration?: Record<string, any>;
  error_message?: string;
}

export interface Pattern {
  name: string;
  category: string;
  description: string;
  complexity_level: string;
  is_antipattern: boolean;
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
  category: "language" | "framework" | "library" | "tool";
  first_seen: string;
  last_seen: string;
  usage_count: number;
  metadata?: Record<string, any>;
}
export interface RepositoryAnalysisResponse {
  repository_id: string;
  status: string;
  analysis_session: AnalysisSession;
  technologies: {
    language: Array<{
      name: string;
      category: string;
      usage_count: number;
    }>;
  };
  patterns: Array<{
    pattern_name: string;
    file_path: string;
    confidence_score: number;
    detected_at: string;
  }>;
  insights: any[]; // Single insight object in array
}
export interface RepositoryAnalysis {
  repository_id: string;
  status: string;
  analysis_session: AnalysisSession;
  technologies: {
    language: Technology[];
    framework: Technology[];
    library: Technology[];
    tool: Technology[];
  };
  patterns: Pattern[];
  pattern_timeline: {
    timeline: Array<{
      date: string;
      patterns: Record<string, number>;
    }>;
    summary: Record<string, any>;
  };
  pattern_statistics: Record<
    string,
    {
      category: string;
      occurrences: number;
      complexity_level: string;
      is_antipattern: boolean;
    }
  >;
  insights: Insight[];
  summary: {
    total_patterns: number;
    antipatterns_detected: number;
    complexity_distribution: Record<string, number>;
  };
  ai_powered: boolean;
}

export interface Insight {
  type:
    | "info"
    | "warning"
    | "achievement"
    | "trend"
    | "recommendation"
    | "ai_analysis";
  title: string;
  description: string;
  severity?: "info" | "warning" | "critical";
  data?: Record<string, any>;
}

export interface CodeAnalysisResult {
  code: string;
  language: string;
  pattern_analysis: {
    detected_patterns: string[];
    combined_patterns: string[];
    confidence_scores: Record<string, number>;
  };
  quality_analysis: {
    quality_score: number;
    readability: string;
    suggestions: string[];
    complexity: string;
  };
  similar_patterns: Array<{
    pattern: string;
    similarity: number;
    description: string;
  }>;
  ai_powered: boolean;
}
