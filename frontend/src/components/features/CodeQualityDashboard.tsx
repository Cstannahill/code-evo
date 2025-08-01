import React from "react";
import { motion } from "framer-motion";
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Info,
  TrendingUp,
  Zap,
  Lock,
  Activity,
  type LucideProps,
} from "lucide-react";
import type { PatternInfo, CodeQualityData } from "../../types/analysis";

// Define a more specific type for the analysis prop
interface AnalysisDataForQuality {
  pattern_statistics: Record<string, PatternInfo>;
  summary: {
    antipatterns_detected: number;
  };
  analysis_session: {
    commits_analyzed: number;
  };
  security_analysis?: {
    overall_score: number;
    risk_level: string;
    total_vulnerabilities: number;
    vulnerabilities_by_severity: Record<string, number>;
    recommendations: string[];
    security_patterns?: Array<{name: string; type: string; is_positive: boolean}>;
  };
  performance_analysis?: {
    overall_score: number;
    performance_grade: string;
    total_issues: number;
    optimizations: string[];
    performance_patterns?: Array<{name: string; type: string; impact: string}>;
  };
  architectural_analysis?: {
    quality_metrics: {
      overall_score: number;
      modularity: number;
      coupling: number;
      cohesion: number;
      grade: string;
    };
    design_patterns: Array<{name: string; confidence: number; detected_in: string}>;
    architectural_styles: string[];
    recommendations: string[];
  };
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

      {/* Enhanced Quality Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
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
        {analysis.security_analysis && (
          <QualityCard
            title="Security"
            score={analysis.security_analysis.overall_score}
            description="Security vulnerability assessment"
            icon={Lock}
          />
        )}
        {analysis.performance_analysis && (
          <QualityCard
            title="Performance"
            score={analysis.performance_analysis.overall_score}
            description="Performance optimization level"
            icon={Zap}
          />
        )}
        {analysis.architectural_analysis && (
          <QualityCard
            title="Architecture"
            score={analysis.architectural_analysis.quality_metrics.overall_score}
            description="Architectural design quality"
            icon={Activity}
          />
        )}
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

      {/* Enhanced Analysis Sections */}
      {analysis.security_analysis && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="bg-card rounded-lg border p-6 shadow-lg"
        >
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-red-500" />
            Security Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Risk Level</span>
                <span className={`px-2 py-1 rounded text-xs font-bold ${
                  analysis.security_analysis.risk_level === 'low' ? 'bg-green-100 text-green-800' :
                  analysis.security_analysis.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {analysis.security_analysis.risk_level.toUpperCase()}
                </span>
              </div>
              <div className="space-y-2">
                <div className="text-sm text-muted-foreground">
                  Total Vulnerabilities: {analysis.security_analysis.total_vulnerabilities}
                </div>
                {Object.entries(analysis.security_analysis.vulnerabilities_by_severity).map(([severity, count]) => (
                  count > 0 && (
                    <div key={severity} className="flex justify-between text-sm">
                      <span className="capitalize">{severity}:</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  )
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2">Security Recommendations</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                {analysis.security_analysis.recommendations.slice(0, 3).map((rec, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="w-1 h-1 bg-muted-foreground rounded-full mt-2 flex-shrink-0" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>
      )}

      {analysis.performance_analysis && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-card rounded-lg border p-6 shadow-lg"
        >
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-500" />
            Performance Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Performance Grade</span>
                <span className={`px-2 py-1 rounded text-xs font-bold ${
                  ['A', 'B'].includes(analysis.performance_analysis.performance_grade) ? 'bg-green-100 text-green-800' :
                  analysis.performance_analysis.performance_grade === 'C' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {analysis.performance_analysis.performance_grade}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                Performance Issues: {analysis.performance_analysis.total_issues}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2">Performance Optimizations</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                {analysis.performance_analysis.optimizations.slice(0, 3).map((opt, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="w-1 h-1 bg-muted-foreground rounded-full mt-2 flex-shrink-0" />
                    {opt}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>
      )}

      {analysis.architectural_analysis && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="bg-card rounded-lg border p-6 shadow-lg"
        >
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-500" />
            Architectural Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h4 className="text-sm font-medium mb-2">Quality Metrics</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Modularity:</span>
                  <span className="font-medium">{(analysis.architectural_analysis.quality_metrics.modularity * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Coupling:</span>
                  <span className="font-medium">{(analysis.architectural_analysis.quality_metrics.coupling * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Cohesion:</span>
                  <span className="font-medium">{(analysis.architectural_analysis.quality_metrics.cohesion * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2">Design Patterns</h4>
              <div className="space-y-1 text-sm">
                {analysis.architectural_analysis.design_patterns.slice(0, 4).map((pattern, index) => (
                  <div key={index} className="flex justify-between">
                    <span>{pattern.name}:</span>
                    <span className="font-medium">{(pattern.confidence * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2">Architecture Styles</h4>
              <div className="flex flex-wrap gap-1 mb-3">
                {analysis.architectural_analysis.architectural_styles.map((style, index) => (
                  <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {style}
                  </span>
                ))}
              </div>
              <div className="text-xs text-muted-foreground">
                Grade: {analysis.architectural_analysis.quality_metrics.grade}
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};
