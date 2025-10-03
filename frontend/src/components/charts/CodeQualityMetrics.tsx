import React from "react";
import { CircularProgressbar, buildStyles } from "react-circular-progressbar";
import "react-circular-progressbar/dist/styles.css";
import { motion } from "framer-motion";
import {
  Code2,
  AlertTriangle,
  TrendingUp,
  Shield,
  Zap,
  GitBranch,
  type LucideIcon,
} from "lucide-react";
import type { RepositoryAnalysis } from "../../types/api";
import type { PatternInfo } from "../../types/analysis";

interface CodeQualityMetricsProps {
  analysis: RepositoryAnalysis;
}

export const CodeQualityMetrics: React.FC<CodeQualityMetricsProps> = ({
  analysis,
}) => {
  // Calculate metrics from analysis data
  const metrics = React.useMemo(() => {
    const totalPatterns = Object.keys(analysis.pattern_statistics || {}).length;
    const antipatterns = analysis.summary?.antipatterns_detected || 0;
    const complexPatterns = Object.values(
      analysis.pattern_statistics || {}
    ).filter((p: PatternInfo) => p.complexity_level === "advanced").length;

    return {
      codeQuality: Math.max(0, Math.min(100, 90 - antipatterns * 15)),
      patternDiversity: Math.min(100, totalPatterns * 12),
      maintainability: Math.max(0, Math.min(100, 85 - complexPatterns * 12)),
      evolutionScore: Math.min(
        100,
        (analysis.pattern_timeline?.timeline?.length || 0) * 8 + 20
      ),
      techDebt: Math.max(0, 100 - antipatterns * 25),
      modernization: Math.min(
        100,
        (() => {
          if (!analysis.technologies) return 30;
          if (Array.isArray(analysis.technologies)) {
            return analysis.technologies.length * 10 + 30;
          }
          return Object.values(analysis.technologies).flat().length * 10 + 30;
        })()
      ),
    };
  }, [analysis]);

  const MetricCard = ({
    title,
    value,
    icon: Icon,
    color,
    description,
  }: {
    title: string;
    value: number;
    icon: LucideIcon;
    color: string;
    description: string;
  }) => {
    // Extract the color hex value for CircularProgressbar
    const colorMap: Record<string, string> = {
      "text-green-500": "#10b981",
      "text-blue-500": "#3b82f6",
      "text-purple-500": "#8b5cf6",
      "text-cyan-500": "#06b6d4",
      "text-orange-500": "#f97316",
      "text-yellow-500": "#eab308",
    };

    const hexColor = colorMap[color] || "#6b7280";

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-card rounded-lg border p-4 shadow-lg flex flex-col items-center"
      >
        <div className="w-full flex flex-col items-center gap-2 mb-4">
          <Icon className={`w-6 h-6 ${color} flex-shrink-0`} />
          <h4 className="text-sm font-medium text-center leading-tight">{title}</h4>
        </div>
        <div className="w-24 h-24 mb-4">
          <CircularProgressbar
            value={value}
            text={`${Math.round(value)}%`}
            styles={buildStyles({
              textSize: "18px",
              pathColor: hexColor,
              textColor: "hsl(var(--foreground))",
              trailColor: "hsl(var(--muted))",
              pathTransition: "stroke-dashoffset 0.5s ease 0s",
            })}
          />
        </div>
        <p className="text-xs text-center text-muted-foreground w-full leading-snug px-1">{description}</p>
      </motion.div>
    );
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      <MetricCard
        title="Code Quality"
        value={metrics.codeQuality}
        icon={Code2}
        color="text-green-500"
        description="Overall code health score"
      />
      <MetricCard
        title="Pattern Diversity"
        value={metrics.patternDiversity}
        icon={GitBranch}
        color="text-blue-500"
        description="Variety of patterns used"
      />
      <MetricCard
        title="Maintainability"
        value={metrics.maintainability}
        icon={Shield}
        color="text-purple-500"
        description="Ease of future changes"
      />
      <MetricCard
        title="Evolution Score"
        value={metrics.evolutionScore}
        icon={TrendingUp}
        color="text-cyan-500"
        description="Learning progression rate"
      />
      <MetricCard
        title="Tech Debt"
        value={metrics.techDebt}
        icon={AlertTriangle}
        color="text-orange-500"
        description="Freedom from antipatterns"
      />
      <MetricCard
        title="Modernization"
        value={metrics.modernization}
        icon={Zap}
        color="text-yellow-500"
        description="Modern tech adoption"
      />
    </div>
  );
};
