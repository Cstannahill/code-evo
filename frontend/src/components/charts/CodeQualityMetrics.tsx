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
} from "lucide-react";
import type { RepositoryAnalysis } from "../../types/api";

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
    ).filter((p: any) => p.complexity_level === "advanced").length;

    return {
      codeQuality: Math.max(0, 100 - antipatterns * 10),
      patternDiversity: Math.min(100, totalPatterns * 10),
      maintainability: Math.max(0, 100 - complexPatterns * 15),
      evolutionScore: Math.min(
        100,
        (analysis.pattern_timeline?.timeline?.length || 0) * 5
      ),
      techDebt: antipatterns * 20,
      modernization:
        Object.values(analysis.technologies || {}).flat().length * 8,
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
    icon: any;
    color: string;
    description: string;
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card rounded-lg border p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <div className="w-32 h-32 mx-auto mb-4">
        <CircularProgressbar
          value={value}
          text={`${value}%`}
          styles={buildStyles({
            textSize: "20px",
            pathColor: color.replace("text-", "#").replace("500", ""),
            textColor: "white",
            trailColor: "#374151",
          })}
        />
      </div>
      <p className="text-xs text-center text-muted-foreground">{description}</p>
    </motion.div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
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
        value={100 - metrics.techDebt}
        icon={AlertTriangle}
        color="text-orange-500"
        description="Freedom from antipatterns"
      />
      <MetricCard
        title="Modernization"
        value={Math.min(100, metrics.modernization)}
        icon={Zap}
        color="text-yellow-500"
        description="Modern tech adoption"
      />
    </div>
  );
};
