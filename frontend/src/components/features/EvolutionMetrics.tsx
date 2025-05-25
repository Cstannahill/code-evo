import React from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  GitBranch,
  TrendingUp,
  Zap,
  type LucideProps,
} from "lucide-react";
import { format, differenceInDays } from "date-fns";
import type { PatternInfo } from "../../types/analysis";

// Define a more specific type for the analysis prop
interface AnalysisData {
  pattern_timeline: {
    timeline: Array<{ date: string; patterns: Record<string, number> }>;
  };
  pattern_statistics: Record<string, PatternInfo>;
  analysis_session: {
    commits_analyzed: number;
    // Add other relevant properties from analysis_session if used
  };
  // Add other top-level properties of analysis if used
}

interface EvolutionMetricsProps {
  analysis: AnalysisData;
}

// Interface for the calculated metrics object
interface CalculatedEvolutionMetrics {
  timespan: number;
  velocity: string;
  patternDensity: string;
  evolutionRate: string;
  firstCommit: string;
  lastCommit: string;
}

interface MetricCardProps {
  icon: React.ComponentType<LucideProps>;
  label: string;
  value: string | number;
  unit?: string;
  color: string;
}

export const EvolutionMetrics: React.FC<EvolutionMetricsProps> = ({
  analysis,
}) => {
  const metrics: CalculatedEvolutionMetrics = React.useMemo(() => {
    const timeline = analysis.pattern_timeline.timeline;
    const firstDate = timeline[0]?.date
      ? new Date(timeline[0].date)
      : new Date();
    const lastDate = timeline[timeline.length - 1]?.date
      ? new Date(timeline[timeline.length - 1].date)
      : new Date();

    const daysDiff = differenceInDays(lastDate, firstDate) || 1;
    const totalPatternOccurrences = Object.values(
      analysis.pattern_statistics
    ).reduce(
      (sum: number, stats: PatternInfo) => sum + (stats.occurrences || 0),
      0
    );

    const commitsAnalyzed = analysis.analysis_session.commits_analyzed || 1; // Avoid division by zero
    const timelineLength = timeline.length || 1; // Avoid division by zero

    return {
      timespan: daysDiff,
      velocity: ((commitsAnalyzed / daysDiff) * 30).toFixed(1),
      patternDensity: (totalPatternOccurrences / commitsAnalyzed).toFixed(2),
      evolutionRate: (
        Object.keys(analysis.pattern_statistics).length / timelineLength
      ).toFixed(2),
      firstCommit: format(firstDate, "MMM dd, yyyy"),
      lastCommit: format(lastDate, "MMM dd, yyyy"),
    };
  }, [analysis]);

  const MetricCard: React.FC<MetricCardProps> = ({
    icon: Icon,
    label,
    value,
    unit,
    color,
  }) => (
    <motion.div
      whileHover={{ scale: 1.05 }}
      // Updated class for dark theme consistency
      className="bg-gray-800 rounded-lg border border-gray-700 p-4 flex items-center gap-4 shadow-lg"
    >
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-400">{label}</p>{" "}
        {/* Dark theme text color */}
        <p className="text-2xl font-bold text-gray-100">
          {" "}
          {/* Dark theme text color */}
          {value}
          {unit && <span className="text-sm text-gray-400 ml-1">{unit}</span>}
        </p>
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6 p-1">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={Calendar}
          label="Development Timespan"
          value={metrics.timespan}
          unit="days"
          color="bg-blue-600" // Adjusted color for better contrast
        />
        <MetricCard
          icon={GitBranch}
          label="Commit Velocity"
          value={metrics.velocity}
          unit="commits/month"
          color="bg-purple-600" // Adjusted color
        />
        <MetricCard
          icon={TrendingUp}
          label="Pattern Density"
          value={metrics.patternDensity}
          unit="patterns/commit"
          color="bg-green-600" // Adjusted color
        />
        <MetricCard
          icon={Zap}
          label="Evolution Rate"
          value={metrics.evolutionRate}
          // unit="new patterns/month" // More descriptive unit
          unit="patterns/timeline entry" // Clarified unit based on calculation
          color="bg-yellow-500" // Adjusted color
        />
      </div>

      {/* Timeline Overview section with dark theme styling */}
      <div className="bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-700">
        <h4 className="text-sm font-medium text-gray-400 mb-4">
          Timeline Overview
        </h4>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">First Analyzed Commit</span>
            <span className="font-medium text-gray-200">
              {metrics.firstCommit}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2.5 relative">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "100%" }}
              transition={{ duration: 1.5, ease: "easeOut" }}
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full h-2.5"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Latest Analyzed Commit
            </span>
            <span className="font-medium text-gray-200">
              {metrics.lastCommit}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
