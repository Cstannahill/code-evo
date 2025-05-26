import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Brain,
  Zap,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Cloud,
  Home,
} from "lucide-react";
import { Button } from "../ui/button";

interface ModelInfo {
  name: string;
  display_name: string;
  provider: string;
  context_window: number;
  cost_per_1k_tokens: number;
  strengths: string[];
  available: boolean;
}

interface ModelSelectionProps {
  selectedModels: string[];
  onModelToggle: (modelName: string) => void;
  onAnalyze: () => void;
  maxModels?: number;
  analysisType: "single" | "comparison";
  loading?: boolean;
}

export const ModelSelection: React.FC<ModelSelectionProps> = ({
  selectedModels,
  onModelToggle,
  onAnalyze,
  maxModels = 3,
  analysisType,
  loading = false,
}) => {
  const [availableModels, setAvailableModels] = useState<
    Record<string, ModelInfo>
  >({});
  const [modelStats, setModelStats] = useState<Record<string, any>>({});
  const [loadingModels, setLoadingModels] = useState(true);

  useEffect(() => {
    fetchAvailableModels();
  }, []);

  const fetchAvailableModels = async () => {
    try {
      const response = await fetch("/api/multi-model/models/available");
      const data = await response.json();
      setAvailableModels(data.available_models);

      // Fetch stats for each model
      const statsPromises = Object.keys(data.available_models).map(
        async (modelName) => {
          try {
            const statsResponse = await fetch(
              `/api/multi-model/models/${modelName}/stats`
            );
            const statsData = await statsResponse.json();
            return { [modelName]: statsData };
          } catch {
            return { [modelName]: null };
          }
        }
      );

      const allStats = await Promise.all(statsPromises);
      const statsObject = allStats.reduce(
        (acc, stat) => ({ ...acc, ...stat }),
        {}
      );
      setModelStats(statsObject);
    } catch (error) {
      console.error("Error fetching models:", error);
    } finally {
      setLoadingModels(false);
    }
  };

  const getModelIcon = (provider: string) => {
    if (provider.includes("Ollama")) return <Home className="w-5 h-5" />;
    if (provider.includes("OpenAI")) return <Cloud className="w-5 h-5" />;
    if (provider.includes("Anthropic")) return <Brain className="w-5 h-5" />;
    return <Cpu className="w-5 h-5" />;
  };

  const getProviderColor = (provider: string) => {
    if (provider.includes("Ollama")) return "border-green-500 bg-green-500/10";
    if (provider.includes("OpenAI")) return "border-blue-500 bg-blue-500/10";
    if (provider.includes("Anthropic"))
      return "border-purple-500 bg-purple-500/10";
    return "border-gray-500 bg-gray-500/10";
  };

  const ModelCard: React.FC<{ modelName: string; model: ModelInfo }> = ({
    modelName,
    model,
  }) => {
    const isSelected = selectedModels.includes(modelName);
    const canSelect = isSelected || selectedModels.length < maxModels;
    const stats = modelStats[modelName];

    return (
      <motion.div
        whileHover={{ scale: canSelect ? 1.02 : 1 }}
        whileTap={{ scale: canSelect ? 0.98 : 1 }}
        className={`
          relative p-4 rounded-lg border-2 cursor-pointer transition-all
          ${
            isSelected
              ? `${getProviderColor(model.provider)} border-opacity-100`
              : "border-gray-700 bg-gray-800 hover:border-gray-600"
          }
          ${!canSelect && !isSelected ? "opacity-50 cursor-not-allowed" : ""}
        `}
        onClick={() => canSelect && onModelToggle(modelName)}
      >
        {/* Selection indicator */}
        <div className="absolute top-2 right-2">
          {isSelected ? (
            <CheckCircle2 className="w-5 h-5 text-green-500" />
          ) : !canSelect ? (
            <AlertCircle className="w-5 h-5 text-orange-500" />
          ) : null}
        </div>

        {/* Model header */}
        <div className="flex items-start gap-3 mb-3">
          <div className={`p-2 rounded-lg ${getProviderColor(model.provider)}`}>
            {getModelIcon(model.provider)}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-white truncate">
              {model.display_name}
            </h3>
            <p className="text-sm text-gray-400">{model.provider}</p>
          </div>
        </div>

        {/* Model specs */}
        <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
          <div className="flex items-center gap-1 text-gray-400">
            <Clock className="w-3 h-3" />
            {stats?.usage_stats?.avg_processing_time
              ? `${stats.usage_stats.avg_processing_time}s avg`
              : "No usage data"}
          </div>
          <div className="flex items-center gap-1 text-gray-400">
            <DollarSign className="w-3 h-3" />
            {model.cost_per_1k_tokens === 0
              ? "Free"
              : `$${model.cost_per_1k_tokens}/1k tokens`}
          </div>
        </div>

        {/* Model strengths */}
        <div className="space-y-1">
          <p className="text-xs font-medium text-gray-300">Strengths:</p>
          <div className="flex flex-wrap gap-1">
            {model.strengths.slice(0, 3).map((strength, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded-full"
              >
                {strength}
              </span>
            ))}
          </div>
        </div>

        {/* Usage stats */}
        {stats?.usage_stats && (
          <div className="mt-3 pt-3 border-t border-gray-700">
            <div className="flex justify-between text-xs text-gray-400">
              <span>Analyses: {stats.usage_stats.total_analyses}</span>
              <span>
                Confidence: {Math.round(stats.usage_stats.avg_confidence * 100)}
                %
              </span>
            </div>
          </div>
        )}
      </motion.div>
    );
  };

  if (loadingModels) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-400">Loading AI models...</span>
      </div>
    );
  }

  const localModels = Object.entries(availableModels).filter(
    ([_, model]) => model.cost_per_1k_tokens === 0
  );
  const apiModels = Object.entries(availableModels).filter(
    ([_, model]) => model.cost_per_1k_tokens > 0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-xl font-bold text-white mb-2">
          {analysisType === "single"
            ? "Select AI Model"
            : "Select Models to Compare"}
        </h2>
        <p className="text-gray-400 text-sm">
          {analysisType === "single"
            ? "Choose one AI model for code analysis"
            : `Compare up to ${maxModels} AI models side-by-side`}
        </p>
        <div className="mt-2 text-sm text-gray-500">
          Selected: {selectedModels.length}/
          {analysisType === "single" ? 1 : maxModels}
        </div>
      </div>

      {/* Local Models */}
      {localModels.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Home className="w-5 h-5 text-green-500" />
            Local Models (Free)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {localModels.map(([modelName, model]) => (
              <ModelCard key={modelName} modelName={modelName} model={model} />
            ))}
          </div>
        </div>
      )}

      {/* API Models */}
      {apiModels.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Cloud className="w-5 h-5 text-blue-500" />
            Cloud Models (Paid)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {apiModels.map(([modelName, model]) => (
              <ModelCard key={modelName} modelName={modelName} model={model} />
            ))}
          </div>
        </div>
      )}

      {/* Analysis button */}
      <div className="flex justify-center pt-4">
        <Button
          onClick={onAnalyze}
          disabled={selectedModels.length === 0 || loading}
          className="px-8 py-3 text-lg"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Analyzing...
            </>
          ) : analysisType === "single" ? (
            <>
              <Brain className="w-5 h-5 mr-2" />
              Analyze with{" "}
              {selectedModels[0]?.replace(":", " ") || "Selected Model"}
            </>
          ) : (
            <>
              <Zap className="w-5 h-5 mr-2" />
              Compare {selectedModels.length} Models
            </>
          )}
        </Button>
      </div>

      {/* Helpful tips */}
      <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
        <h4 className="font-medium text-blue-300 mb-2">
          💡 Model Selection Tips
        </h4>
        <ul className="text-sm text-blue-200 space-y-1">
          <li>
            • <strong>Local models</strong> are free but require local setup
          </li>
          <li>
            • <strong>Cloud models</strong> offer advanced capabilities but cost
            tokens
          </li>
          <li>
            • <strong>CodeLlama</strong> excels at code understanding
          </li>
          <li>
            • <strong>GPT-4</strong> provides the most detailed analysis
          </li>
          <li>
            • <strong>Claude</strong> focuses on code quality and best practices
          </li>
        </ul>
      </div>
    </div>
  );
};
