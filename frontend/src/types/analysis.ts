// Re-export Technology and TechnologiesByCategory from api.ts to avoid duplication
export type { Technology, TechnologiesByCategory } from "./api";

// Define a base type for a technology with extended properties for analysis
export interface TechnologyWithAnalysis extends Technology {
  adoption_rate?: number;
  complexity_score?: number;
  learning_curve?: "easy" | "moderate" | "difficult";
  relationships?: string[];
  [key: string]: unknown; // For future extensibility
}

// Data structure for individual items in a pie chart representing a tech category
export interface TechStackPieData {
  name: string; // Category name, e.g., "Languages"
  value: number; // Total usage_count for this category, used by Pie's dataKey
  count: number; // Number of distinct technologies in this category
  technologies: Technology[]; // Array of technologies in this category
}

// For ComplexityEvolutionChart
export interface PatternInfo {
  name: string;
  occurrences: number;
  category: string;
  complexity_level?: string; // Optional, as it might be derived or not present
  is_antipattern?: boolean; // Optional, as it might be derived or not present
}

export interface ComplexityGroup {
  simple: PatternInfo[];
  intermediate: PatternInfo[];
  advanced: PatternInfo[];
}

export interface ComplexityChartData {
  complexity: string;
  count: number;
  totalOccurrences: number;
  patterns: PatternInfo[];
}

export interface CodeQualityData {
  overall: number;
  maintainability: number;
  readability: number;
  testability: number;
  issues: {
    critical: number;
    warnings: number;
    info: number;
  };
}

// For EvolutionMetrics
export interface EvolutionMetricValue {
  date: string; // Typically a date string like 'YYYY-MM-DD'
  value: number;
}

export interface EvolutionMetric {
  id: string;
  name: string;
  unit?: string; // e.g., 'lines', 'files', '%'
  data: EvolutionMetricValue[];
  currentValue: number;
  changeSinceLast?: number; // Change compared to the previous period
  trend?: "positive" | "negative" | "neutral";
}

// For useChartData hook
export interface TransformedData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string | string[];
    backgroundColor?: string | string[];
    fill?: boolean;
    // other chart.js dataset properties
  }>;
}
