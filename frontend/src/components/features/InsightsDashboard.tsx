import React, { useMemo } from "react";
import { motion } from "framer-motion";
import {
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  Zap,
  Award,
  Sparkles,
} from "lucide-react";
import type { Insight, InsightType, Analysis, CategorizedInsights } from "../../types/insights";
import { AISummaryCard } from "./insights/AISummaryCard";
import { InsightsSummary } from "./insights/InsightsSummary";
import { InsightsCategorySection } from "./insights/InsightsCategorySection";
import { LearningPathSection } from "./insights/LearningPathSection";

interface InsightsDashboardProps {
  insights: Insight[];
  analysis: Analysis;
}

// Safely stringify unknown data


// Transform raw pattern data into proper insights
const transformRawInsights = (rawInsights: any[]): Insight[] => {
  if (!rawInsights || !Array.isArray(rawInsights)) {
    return [];
  }

  return rawInsights.map((item, index) => {
    // Handle raw pattern data that looks like: { pattern: {...}, total_occurrences: N, unique_files: [...] }
    if (item.pattern && item.total_occurrences && item.unique_files) {
      const pattern = item.pattern;
      const isAntipattern = pattern.is_antipattern;
      const complexity = pattern.complexity_level;

      return {
        type: isAntipattern ? "warning" : (complexity === "advanced" ? "achievement" : "recommendation") as any,
        title: `${pattern.name.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())} Pattern`,
        description: pattern.description ||
          `Found in ${item.unique_files.length} files with ${item.total_occurrences} total occurrences. ${isAntipattern ? 'This pattern may indicate areas for improvement.' : `This ${complexity || 'standard'} pattern shows good code organization.`}`,
        data: {
          occurrences: item.total_occurrences,
          files: item.unique_files.slice(0, 5), // Show only first 5 files
          complexity: complexity,
          isAntipattern: isAntipattern,
          aiModels: item.ai_models_used || []
        }
      };
    }

    // Handle properly formatted insights
    if (item.type && item.title && item.description) {
      return item as Insight;
    }

    // Handle generic objects - convert to debugging insight
    return {
      type: "info" as any,
      title: `Analysis Data ${index + 1}`,
      description: typeof item === 'string' ? item : 'Raw analysis data from the backend',
      data: item
    };
  });
};

export const InsightsDashboard: React.FC<InsightsDashboardProps> = ({
  insights,
  analysis,
}) => {
  // Transform insights and add generated ones
  const processedInsights = useMemo(() => {
    const transformed = transformRawInsights(insights);

    // Generate additional insights from analysis data
    const additionalInsights: Insight[] = [];

    // Pattern complexity insights
    const patternStats = analysis.pattern_statistics || {};
    const complexPatterns = Object.entries(patternStats).filter(([, info]) => {
      if (!info || typeof info !== 'object') return false;
      const complexity = 'complexity_level' in info ? (info as any).complexity_level : undefined;
      return complexity === 'advanced';
    });

    if (complexPatterns.length > 0) {
      additionalInsights.push({
        type: "achievement",
        title: "Advanced Pattern Usage",
        description: `Your codebase demonstrates ${complexPatterns.length} advanced patterns, indicating sophisticated architectural decisions.`,
        data: { patterns: complexPatterns.map(([name]) => name) }
      });
    }

    // Anti-pattern warnings
    const antiPatterns = Object.entries(patternStats).filter(([, info]) => {
      if (!info || typeof info !== 'object') return false;
      const isAnti = 'is_antipattern' in info ? (info as any).is_antipattern : false;
      return isAnti;
    });

    if (antiPatterns.length > 0) {
      additionalInsights.push({
        type: "warning",
        title: "Anti-patterns Detected",
        description: `${antiPatterns.length} anti-patterns detected. Consider refactoring these areas to improve code quality.`,
        data: { patterns: antiPatterns.map(([name]) => name) }
      });
    }

    // Technology diversity insight
    const techCount = Object.values(analysis.technologies || {}).flat().length;
    if (techCount > 10) {
      additionalInsights.push({
        type: "trend",
        title: "High Technology Diversity",
        description: `Your project uses ${techCount} different technologies, showing a diverse and modern tech stack.`,
        data: { count: techCount }
      });
    }

    return [...transformed, ...additionalInsights];
  }, [insights, analysis]);

  const categorizedInsights: CategorizedInsights = useMemo(() => {
    const categories: CategorizedInsights = {
      recommendations: [],
      achievements: [],
      warnings: [],
      trends: [],
    };
    processedInsights.forEach((insight) => {
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
        default:
          categories.recommendations.push(insight);
      }
    });
    return categories;
  }, [processedInsights]);

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

  // firstPatternKey removed — no longer used by AISummaryCard

  return (
    <div className="space-y-6">
      {/* AI Summary */}
      <AISummaryCard analysis={analysis} />

      {/* Empty State */}
      {processedInsights.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <Sparkles className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-semibold mb-2">No AI Insights Available</h3>
          <p className="text-muted-foreground mb-4 max-w-md mx-auto">
            AI insights will appear here once your repository has been analyzed.
            The analysis may be in progress or no AI models are currently available.
          </p>
        </motion.div>
      )}

      {/* Insights Summary */}
      {processedInsights.length > 0 && (
        <InsightsSummary categorizedInsights={categorizedInsights} />
      )}

      {/* Categorized Insights */}
      {processedInsights.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <InsightsCategorySection
            title="Recommendations"
            icon={<Lightbulb className="w-4 h-4" />}
            count={categorizedInsights.recommendations.length}
            insights={categorizedInsights.recommendations}
            getIcon={getIcon}
            getColor={getColor}
          />
          <InsightsCategorySection
            title="Achievements"
            icon={<Award className="w-4 h-4" />}
            count={categorizedInsights.achievements.length}
            insights={categorizedInsights.achievements}
            getIcon={getIcon}
            getColor={getColor}
          />
          <InsightsCategorySection
            title="Areas for Improvement"
            icon={<AlertTriangle className="w-4 h-4" />}
            count={categorizedInsights.warnings.length}
            insights={categorizedInsights.warnings}
            getIcon={getIcon}
            getColor={getColor}
          />
          <InsightsCategorySection
            title="Identified Trends"
            icon={<TrendingUp className="w-4 h-4" />}
            count={categorizedInsights.trends.length}
            insights={categorizedInsights.trends}
            getIcon={getIcon}
            getColor={getColor}
          />
        </div>
      )}

      {/* Learning Path Recommendations */}
      {processedInsights.length > 0 && (
        <LearningPathSection analysis={analysis} />
      )}
    </div>
  );
};

// generateLearningPath moved to LearningPathSection
