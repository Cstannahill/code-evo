import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  Zap,
  Target,
  Download,
} from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

interface ModelResult {
  model: string;
  model_info: {
    display_name: string;
    provider: string;
    strengths: string[];
  };
  patterns: string[];
  complexity_score: number;
  skill_level: string;
  suggestions: string[];
  confidence: number;
  processing_time: number;
  token_usage?: {
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
  };
  error?: string;
}

interface ComparisonAnalysis {
  consensus_patterns: string[];
  disputed_patterns: Array<{
    pattern: string;
    detected_by: string[];
    agreement_ratio: number;
  }>;
  agreement_score: number;
  performance: {
    processing_times: Record<string, number>;
    fastest_model: string;
    cost_estimates: Record<string, number>;
    most_cost_effective?: string;
  };
  diversity_score: number;
  consistency_score: number;
}

interface ModelComparisonProps {
  results: ModelResult[];
  comparison: ComparisonAnalysis;
  onExportData?: () => void;
}

export const ModelComparisonDashboard: React.FC<ModelComparisonProps> = ({
  results,
  comparison,
  onExportData,
}) => {
  const [selectedView, setSelectedView] = useState<
    "overview" | "patterns" | "performance"
  >("overview");
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  // Prepare radar chart data
  const radarData = [
    {
      metric: "Complexity Score",
      ...results.reduce(
        (acc, result) => ({
          ...acc,
          [result.model_info.display_name]: result.complexity_score,
        }),
        {}
      ),
    },
    {
      metric: "Confidence",
      ...results.reduce(
        (acc, result) => ({
          ...acc,
          [result.model_info.display_name]: result.confidence * 10,
        }),
        {}
      ),
    },
    {
      metric: "Pattern Count",
      ...results.reduce(
        (acc, result) => ({
          ...acc,
          [result.model_info.display_name]: result.patterns.length,
        }),
        {}
      ),
    },
    {
      metric: "Suggestion Count",
      ...results.reduce(
        (acc, result) => ({
          ...acc,
          [result.model_info.display_name]: result.suggestions.length,
        }),
        {}
      ),
    },
  ];

  // Performance comparison data
  const performanceData = results.map((result) => ({
    model: result.model_info.display_name,
    processing_time: result.processing_time,
    tokens: result.token_usage?.total_tokens || 0,
    patterns_found: result.patterns.length,
    confidence: result.confidence * 100,
  }));

  const getModelColor = (index: number) => {
    const colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"];
    return colors[index % colors.length];
  };

  const getSkillLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "beginner":
        return "text-green-400 bg-green-400/20";
      case "intermediate":
        return "text-yellow-400 bg-yellow-400/20";
      case "advanced":
        return "text-red-400 bg-red-400/20";
      default:
        return "text-gray-400 bg-gray-400/20";
    }
  };

  const ModelCard: React.FC<{ result: ModelResult; index: number }> = ({
    result,
    index,
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={`
        bg-gray-800 border-2 rounded-lg p-4 cursor-pointer transition-all
        ${
          selectedModel === result.model
            ? "border-blue-500"
            : "border-gray-700 hover:border-gray-600"
        }
      `}
      onClick={() =>
        setSelectedModel(selectedModel === result.model ? null : result.model)
      }
    >
      {/* Model Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className="w-4 h-4 rounded-full"
            style={{ backgroundColor: getModelColor(index) }}
          />
          <div>
            <h3 className="font-semibold text-white">
              {result.model_info.display_name}
            </h3>
            <p className="text-xs text-gray-400">
              {result.model_info.provider}
            </p>
          </div>
        </div>
        {result.error ? (
          <AlertTriangle className="w-5 h-5 text-red-500" />
        ) : (
          <CheckCircle2 className="w-5 h-5 text-green-500" />
        )}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">
            {result.patterns.length}
          </div>
          <div className="text-xs text-gray-400">Patterns</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-white">
            {result.complexity_score}/10
          </div>
          <div className="text-xs text-gray-400">Complexity</div>
        </div>
      </div>

      {/* Skill Level */}
      <div className="flex justify-center mb-3">
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium ${getSkillLevelColor(
            result.skill_level
          )}`}
        >
          {result.skill_level}
        </span>
      </div>

      {/* Performance Metrics */}
      <div className="flex justify-between text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {result.processing_time.toFixed(2)}s
        </span>
        <span className="flex items-center gap-1">
          <Target className="w-3 h-3" />
          {Math.round(result.confidence * 100)}%
        </span>
      </div>

      {/* Expandable Details */}
      {selectedModel === result.model && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="mt-4 pt-4 border-t border-gray-700"
        >
          <div className="space-y-3">
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-1">
                Detected Patterns:
              </h4>
              <div className="flex flex-wrap gap-1">
                {result.patterns.map((pattern, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded"
                  >
                    {pattern.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-1">
                Suggestions:
              </h4>
              <ul className="text-xs text-gray-400 space-y-1">
                {result.suggestions.slice(0, 3).map((suggestion, idx) => (
                  <li key={idx}>• {suggestion}</li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">
            Model Comparison Results
          </h2>
          <p className="text-gray-400">
            Comparing {results.length} AI models on the same code
          </p>
        </div>
        {onExportData && (
          <button
            onClick={onExportData}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm"
          >
            <Download className="w-4 h-4" />
            Export Data
          </button>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-5 h-5 text-green-500" />
            <span className="text-sm text-gray-400">Agreement Score</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {Math.round(comparison.agreement_score * 100)}%
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-5 h-5 text-blue-500" />
            <span className="text-sm text-gray-400">Consensus Patterns</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {comparison.consensus_patterns.length}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            <span className="text-sm text-gray-400">Disputed Patterns</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {comparison.disputed_patterns.length}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-purple-500" />
            <span className="text-sm text-gray-400">Fastest Model</span>
          </div>
          <div className="text-sm font-bold text-white">
            {comparison.performance.fastest_model}
          </div>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
        {(["overview", "patterns", "performance"] as const).map((view) => (
          <button
            key={view}
            onClick={() => setSelectedView(view)}
            className={`
              flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors
              ${
                selectedView === view
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }
            `}
          >
            {view.charAt(0).toUpperCase() + view.slice(1)}
          </button>
        ))}
      </div>

      {/* View Content */}
      {selectedView === "overview" && (
        <div className="space-y-6">
          {/* Model Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((result, index) => (
              <ModelCard key={result.model} result={result} index={index} />
            ))}
          </div>

          {/* Radar Chart */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
              Performance Comparison
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis
                  dataKey="metric"
                  className="text-xs text-gray-400"
                />
                <PolarRadiusAxis className="text-xs text-gray-400" />
                {results.map((result, index) => (
                  <Radar
                    key={result.model}
                    name={result.model_info.display_name}
                    dataKey={result.model_info.display_name}
                    stroke={getModelColor(index)}
                    fill={getModelColor(index)}
                    fillOpacity={0.1}
                    strokeWidth={2}
                  />
                ))}
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {selectedView === "patterns" && (
        <div className="space-y-6">
          {/* Consensus Patterns */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              Consensus Patterns ({comparison.consensus_patterns.length})
            </h3>
            <div className="flex flex-wrap gap-2">
              {comparison.consensus_patterns.map((pattern, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-green-500/20 text-green-300 rounded-full text-sm"
                >
                  {pattern.replace(/_/g, " ")}
                </span>
              ))}
            </div>
            {comparison.consensus_patterns.length === 0 && (
              <p className="text-gray-400 text-sm">
                No patterns were detected by all models
              </p>
            )}
          </div>

          {/* Disputed Patterns */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              Disputed Patterns ({comparison.disputed_patterns.length})
            </h3>
            <div className="space-y-3">
              {comparison.disputed_patterns.map((dispute, idx) => (
                <div
                  key={idx}
                  className="border border-gray-700 rounded-lg p-3"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-white">
                      {dispute.pattern.replace(/_/g, " ")}
                    </span>
                    <span className="text-sm text-gray-400">
                      {Math.round(dispute.agreement_ratio * 100)}% agreement
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">
                    Detected by: {dispute.detected_by.join(", ")}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {selectedView === "performance" && (
        <div className="space-y-6">
          {/* Performance Chart */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
              Processing Time Comparison
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="model" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "0.5rem",
                  }}
                />
                <Legend />
                <Bar
                  dataKey="processing_time"
                  fill="#3b82f6"
                  name="Processing Time (s)"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Performance Table */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
              Detailed Performance Metrics
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-2 text-gray-400">Model</th>
                    <th className="text-left py-2 text-gray-400">Time (s)</th>
                    <th className="text-left py-2 text-gray-400">Patterns</th>
                    <th className="text-left py-2 text-gray-400">Confidence</th>
                    <th className="text-left py-2 text-gray-400">Tokens</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result) => (
                    <tr
                      key={result.model}
                      className="border-b border-gray-700/50"
                    >
                      <td className="py-2 text-white font-medium">
                        {result.model_info.display_name}
                      </td>
                      <td className="py-2 text-gray-300">
                        {result.processing_time.toFixed(2)}
                      </td>
                      <td className="py-2 text-gray-300">
                        {result.patterns.length}
                      </td>
                      <td className="py-2 text-gray-300">
                        {Math.round(result.confidence * 100)}%
                      </td>
                      <td className="py-2 text-gray-300">
                        {result.token_usage?.total_tokens || "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
