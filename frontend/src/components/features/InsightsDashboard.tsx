import React, { useMemo } from "react";
import { motion } from "framer-motion";
import {
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  BookOpen,
  Zap,
  Award,
} from "lucide-react";

// Possible insight types
export type InsightType =
  | "recommendation"
  | "ai_analysis"
  | "achievement"
  | "warning"
  | "trend"
  | "pattern_summary"
  | string;

// Insight data structure
export interface Insight {
  type: InsightType;
  title: string;
  description: string;
  data?: unknown;
}

// Analysis data structures
interface AnalysisSummary {
  total_patterns: number;
  antipatterns_detected: number;
}

interface AnalysisSession {
  commits_analyzed: number;
}

export interface Analysis {
  summary: AnalysisSummary;
  analysis_session: AnalysisSession;
  technologies: Record<string, string[]>;
  pattern_statistics: Record<string, number>;
}

// Component props
interface InsightsDashboardProps {
  insights: Insight[];
  analysis: Analysis;
}

// Categorized insights
interface CategorizedInsights {
  recommendations: Insight[];
  achievements: Insight[];
  warnings: Insight[];
  trends: Insight[];
}

// Safely stringify unknown data
const safeStringify = (data: unknown): string => {
  try {
    if (typeof data === "object" && data !== null) {
      return JSON.stringify(data, null, 2);
    }
    return String(data);
  } catch {
    return "Unable to display data";
  }
};

export const InsightsDashboard: React.FC<InsightsDashboardProps> = ({
  insights,
  analysis,
}) => {
  const categorizedInsights: CategorizedInsights = useMemo(() => {
    const categories: CategorizedInsights = {
      recommendations: [],
      achievements: [],
      warnings: [],
      trends: [],
    };
    insights.forEach((insight) => {
      switch (insight.type) {
        case "recommendation":
        case "ai_analysis":
          categories.recommendations.push(insight);
          break;
        case "achievement":
          categories.achievements.push(insight);
          break;
        case "warning":
          categories.warnings.push(insight);
          break;
        case "trend":
        case "pattern_summary":
          categories.trends.push(insight);
          break;
      }
    });
    return categories;
  }, [insights]);

  const getIcon = (
    type: InsightType
  ): React.ComponentType<React.SVGProps<SVGSVGElement>> => {
    switch (type) {
      case "recommendation":
      case "ai_analysis":
        return Lightbulb;
      case "achievement":
        return Award;
      case "warning":
        return AlertTriangle;
      case "trend":
        return TrendingUp;
      default:
        return Zap;
    }
  };

  const getColor = (type: InsightType): string => {
    switch (type) {
      case "recommendation":
      case "ai_analysis":
        return "text-blue-500 bg-blue-500/10";
      case "achievement":
        return "text-green-500 bg-green-500/10";
      case "warning":
        return "text-orange-500 bg-orange-500/10";
      case "trend":
        return "text-purple-500 bg-purple-500/10";
      default:
        return "text-gray-500 bg-gray-500/10";
    }
  };

  const firstPatternKey =
    Object.keys(analysis.pattern_statistics)[0]?.replace("_", " ") || "";

  return (
    <div className="space-y-6">
      {/* AI Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg border p-6"
      >
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500">
            <Lightbulb className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold mb-2">AI Analysis Summary</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Your repository demonstrates {analysis.summary.total_patterns}{" "}
              distinct coding patterns across{" "}
              {analysis.analysis_session.commits_analyzed} commits. The codebase
              shows{" "}
              {Object.values(analysis.technologies).flat().length > 5
                ? "high"
                : "moderate"}{" "}
              technological diversity with a focus on {firstPatternKey}{" "}
              patterns.
              {analysis.summary.antipatterns_detected > 0 &&
                ` ${analysis.summary.antipatterns_detected} areas have been identified for potential improvement.`}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Categorized Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recommendations */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Lightbulb className="w-4 h-4" /> Recommendations (
            {categorizedInsights.recommendations.length})
          </h4>
          <div className="space-y-3">
            {categorizedInsights.recommendations.map((insight, idx) => (
              <InsightCard
                key={idx}
                insight={insight}
                getIcon={getIcon}
                getColor={getColor}
              />
            ))}
          </div>
        </div>

        {/* Achievements */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Award className="w-4 h-4" /> Achievements (
            {categorizedInsights.achievements.length})
          </h4>
          <div className="space-y-3">
            {categorizedInsights.achievements.map((insight, idx) => (
              <InsightCard
                key={idx}
                insight={insight}
                getIcon={getIcon}
                getColor={getColor}
              />
            ))}
          </div>
        </div>

        {/* Warnings */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> Areas for Improvement (
            {categorizedInsights.warnings.length})
          </h4>
          <div className="space-y-3">
            {categorizedInsights.warnings.map((insight, idx) => (
              <InsightCard
                key={idx}
                insight={insight}
                getIcon={getIcon}
                getColor={getColor}
              />
            ))}
          </div>
        </div>

        {/* Trends */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <TrendingUp className="w-4 h-4" /> Identified Trends (
            {categorizedInsights.trends.length})
          </h4>
          <div className="space-y-3">
            {categorizedInsights.trends.map((insight, idx) => (
              <InsightCard
                key={idx}
                insight={insight}
                getIcon={getIcon}
                getColor={getColor}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Learning Path Recommendations */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="bg-card rounded-lg border p-6"
      >
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5" /> Recommended Learning Path
        </h3>
        <div className="space-y-4">
          {generateLearningPath(analysis).map((step, idx) => (
            <div key={idx} className="flex items-start gap-4">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  idx === 0
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {idx + 1}
              </div>
              <div className="flex-1">
                <h4 className="font-medium">{step.title}</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  {step.description}
                </p>
                <div className="flex items-center gap-4 mt-2">
                  <span className="text-xs text-muted-foreground">
                    Difficulty: {step.difficulty}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Time: {step.estimatedTime}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

interface InsightCardProps {
  insight: Insight;
  getIcon: (
    type: InsightType
  ) => React.ComponentType<React.SVGProps<SVGSVGElement>>;
  getColor: (type: InsightType) => string;
}

const InsightCard: React.FC<InsightCardProps> = ({
  insight,
  getIcon,
  getColor,
}) => {
  const Icon = getIcon(insight.type);
  const colorClass = getColor(insight.type);
  const [, bgClass] = colorClass.split(" ");

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`rounded-lg p-4 ${bgClass}`}
    >
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 mt-0.5 ${colorClass.split(" ")[0]}`} />
        <div className="flex-1">
          <h4 className="font-medium text-sm">{insight.title}</h4>
          <p className="text-sm text-muted-foreground mt-1">
            {insight.description}
          </p>
          {insight.data !== undefined && (
            <div className="mt-3 p-2 bg-background/50 rounded text-xs">
              <pre>{safeStringify(insight.data)}</pre>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export interface PathStep {
  title: string;
  description: string;
  difficulty: string;
  estimatedTime: string;
}

export const generateLearningPath = (analysis: Analysis): PathStep[] => {
  const paths: PathStep[] = [];
  if (analysis.summary.antipatterns_detected > 0) {
    paths.push({
      title: "Refactoring Anti-patterns",
      description:
        "Focus on eliminating detected anti-patterns to improve code quality",
      difficulty: "Intermediate",
      estimatedTime: "2-3 weeks",
    });
  }
  const techCount = Object.values(analysis.technologies).flat().length;
  if (techCount < 5) {
    paths.push({
      title: "Explore Modern Frameworks",
      description:
        "Expand your technology stack with modern frameworks and tools",
      difficulty: "Beginner",
      estimatedTime: "4-6 weeks",
    });
  }
  paths.push({
    title: "Advanced Pattern Implementation",
    description: "Master advanced design patterns for scalable architecture",
    difficulty: "Advanced",
    estimatedTime: "6-8 weeks",
  });
  return paths;
};
