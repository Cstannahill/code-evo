/**
 * @fileoverview Types for Insights Dashboard and related components.
 * @module types/insights
 */

/**
 * @fileoverview Types for Insights Dashboard and related components.
 * @module types/insights
 */

/**
 * Possible types of insights.
 */
export type InsightType =
  | "recommendation"
  | "ai_analysis"
  | "achievement"
  | "warning"
  | "trend"
  | "pattern_summary"
  | string;

/**
 * Insight data structure.
 */
export interface Insight {
  type: InsightType;
  title: string;
  description: string;
  data?: unknown;
}

/**
 * Categorized insights for dashboard summary.
 */
export interface CategorizedInsights {
  recommendations: Insight[];
  achievements: Insight[];
  warnings: Insight[];
  trends: Insight[];
}

/**
 * Learning path step for recommendations.
 */
export interface PathStep {
  title: string;
  description: string;
  difficulty: string;
  estimatedTime: string;
}

/**
 * Analysis data structure for dashboard.
 */
export interface Analysis {
  summary: {
    total_patterns: number;
    antipatterns_detected: number;
  };
  analysis_session: {
    commits_analyzed: number;
  };
  technologies: Record<string, any[]> | Record<string, string[]>;
  pattern_statistics: Record<
    string,
    | number
    | {
        complexity_level?: string;
        is_antipattern?: boolean;
        [key: string]: unknown;
      }
  >;
  security_analysis?: unknown;
  performance_analysis?: unknown;
  architectural_analysis?: unknown;
}
