import React from "react";
import { motion } from "framer-motion";
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Info,
  TrendingUp,
  type LucideProps,
} from "lucide-react";
import type { PatternInfo, CodeQualityData } from "../../types/analysis";

// Define a more specific type for the analysis prop
interface AnalysisDataForQuality {
  pattern_statistics: Record<string, PatternInfo>;
  summary: {
    antipatterns_detected: number;
    // Add other relevant properties from summary if used
  };
  analysis_session: {
    commits_analyzed: number;
    // Add other relevant properties from analysis_session if used
  };
  // Add other top-level properties of analysis if used
}

interface CodeQualityDashboardProps {
  analysis: AnalysisDataForQuality;
}

interface QualityCardProps {
  title: string;
  score: number;
  description: string;
  icon: React.ComponentType<LucideProps>;
}

export const CodeQualityDashboard: React.FC<CodeQualityDashboardProps> = ({
  analysis,
}) => {
  const qualityMetrics: CodeQualityData = React.useMemo(() => {
    const totalPatterns = Object.keys(analysis.pattern_statistics).length;
    const antipatterns = analysis.summary.antipatterns_detected;
    const complexPatterns = Object.values(analysis.pattern_statistics).filter(
      (p: PatternInfo) => p.complexity_level === "advanced"
    ).length;
    const simplePatterns = Object.values(analysis.pattern_statistics).filter(
      (p: PatternInfo) => p.complexity_level === "simple"
    ).length;

    const qualityScore = Math.max(
      0,
      100 - antipatterns * 15 - complexPatterns * 5 + simplePatterns * 2
    );
    const maintainabilityScore = Math.max(
      0,
      100 - antipatterns * 20 - complexPatterns * 10
    );
    const readabilityScore = Math.min(
      100,
      50 + simplePatterns * 10 - complexPatterns * 5
    );
    const testabilityScore = Math.min(
      100,
      60 + totalPatterns * 2 - antipatterns * 10
    );

    return {
      overall: qualityScore,
      maintainability: maintainabilityScore,
      readability: readabilityScore,
      testability: testabilityScore,
      issues: {
        critical: antipatterns,
        warnings: complexPatterns,
        info: totalPatterns - antipatterns - complexPatterns,
      },
    };
  }, [analysis]);

  const QualityCard: React.FC<QualityCardProps> = ({
    title,
    score,
    description,
    icon: Icon,
  }) => {
    const getScoreColor = (scoreValue: number): string => {
      if (scoreValue >= 80) return "text-green-500";
      if (scoreValue >= 60) return "text-yellow-500";
      return "text-red-500";
    };
    const getBgScoreColor = (scoreValue: number): string => {
      if (scoreValue >= 80) return "bg-green-500";
      if (scoreValue >= 60) return "bg-yellow-500";
      return "bg-red-500";
    };

    return (
      <motion.div
        whileHover={{ scale: 1.02 }}
        className="bg-card rounded-lg border p-6 shadow-lg"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">{title}</h3>
          <Icon className="w-5 h-5 text-muted-foreground" />
        </div>
        <div className="space-y-4">
          <div>
            <div className="flex items-baseline justify-between mb-2">
              <span className={`text-3xl font-bold ${getScoreColor(score)}`}>
                {score}
              </span>
              <span className="text-sm text-muted-foreground">/100</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2.5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${score}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className={`h-full rounded-full ${getBgScoreColor(score)}`}
              />
            </div>
          </div>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="space-y-6 p-1">
      {/* Overall Quality Score */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 rounded-lg border p-8 text-center shadow-xl"
      >
        <h2 className="text-2xl font-bold mb-4">
          Overall Code Quality Score
        </h2>
        <div className="text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 mb-2">
          {qualityMetrics.overall}
        </div>
        <p className="text-muted-foreground">
          Based on pattern analysis across{" "}
          {analysis.analysis_session.commits_analyzed} commits
        </p>
      </motion.div>

      {/* Quality Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <QualityCard
          title="Maintainability"
          score={qualityMetrics.maintainability}
          description="How easy the code is to modify and extend"
          icon={Shield}
        />
        <QualityCard
          title="Readability"
          score={qualityMetrics.readability}
          description="Code clarity and comprehension ease"
          icon={CheckCircle}
        />
        <QualityCard
          title="Testability"
          score={qualityMetrics.testability}
          description="Ease of writing and maintaining tests"
          icon={TrendingUp}
        />
      </div>

      {/* Issues Summary */}
      <div className="bg-card rounded-lg border p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4">
          Code Issues Summary
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-red-500/10 rounded-lg border border-red-500/30">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <div>
                <p className="font-medium text-red-500">Critical Issues</p>
                <p className="text-sm text-muted-foreground">Anti-patterns detected</p>
              </div>
            </div>
            <span className="text-2xl font-bold text-red-500">
              {qualityMetrics.issues.critical}
            </span>
          </div>
          <div className="flex items-center justify-between p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              <div>
                <p className="font-medium text-yellow-500">Warnings</p>
                <p className="text-sm text-muted-foreground">
                  Complex patterns requiring attention
                </p>
              </div>
            </div>
            <span className="text-2xl font-bold text-yellow-500">
              {qualityMetrics.issues.warnings}
            </span>
          </div>
          <div className="flex items-center justify-between p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
            <div className="flex items-center gap-3">
              <Info className="w-5 h-5 text-blue-500" />
              <div>
                <p className="font-medium text-blue-500">Information</p>
                <p className="text-sm text-muted-foreground">
                  Standard patterns identified
                </p>
              </div>
            </div>
            <span className="text-2xl font-bold text-blue-500">
              {qualityMetrics.issues.info}
            </span>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="bg-card rounded-lg border p-6 shadow-lg"
      >
        <h3 className="text-lg font-semibold mb-4">
          Quality Improvement Recommendations
        </h3>
        <div className="space-y-3">
          {qualityMetrics.issues.critical > 0 && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-white text-xs font-bold">
                1
              </div>
              <div>
                <h4 className="font-medium">
                  Address Anti-patterns
                </h4>
                <p className="text-sm text-muted-foreground">
                  Focus on refactoring the {qualityMetrics.issues.critical}{" "}
                  anti-patterns to improve code quality
                </p>
              </div>
            </div>
          )}
          {qualityMetrics.issues.warnings > 0 && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-yellow-500 flex items-center justify-center text-white text-xs font-bold">
                {qualityMetrics.issues.critical > 0 ? 2 : 1}
              </div>
              <div>
                <h4 className="font-medium">
                  Simplify Complex Patterns
                </h4>
                <p className="text-sm text-muted-foreground">
                  Consider breaking down the {qualityMetrics.issues.warnings}{" "}
                  complex patterns into simpler, more maintainable components.
                </p>
              </div>
            </div>
          )}
          <div className="flex items-start gap-3">
            <div
              className={`w-6 h-6 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold`}
            >
              {qualityMetrics.issues.critical > 0 &&
              qualityMetrics.issues.warnings > 0
                ? 3
                : qualityMetrics.issues.critical > 0 ||
                  qualityMetrics.issues.warnings > 0
                ? 2
                : 1}
            </div>
            <div>
              <h4 className="font-medium">
                Establish Coding Standards
              </h4>
              <p className="text-sm text-muted-foreground">
                Implement consistent coding standards and use linters/formatters
                to maintain quality as the codebase grows.
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
