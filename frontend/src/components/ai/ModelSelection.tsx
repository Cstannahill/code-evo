import React, { useState, useEffect, useCallback } from "react";
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
import { apiClient } from "../../api/client";
import { useLocalOllama } from "../../hooks/useLocalOllama";

interface ModelStats {
  usage_stats?: {
    avg_processing_time: number;
    total_analyses: number;
    avg_confidence: number;
  };
}

export interface ModelInfo {
  name: string;
  display_name: string;
  provider: string;
  context_window: number;
  cost_per_1k_tokens: number;
  strengths: string[];
  available: boolean;
  cost_tier?: string;
  is_free?: boolean;
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
  const [modelStats, setModelStats] = useState<Record<string, ModelStats>>({});
  const [loadingModels, setLoadingModels] = useState(true);
  const { status: localOllamaStatus } = useLocalOllama();

  const fetchAvailableModels = useCallback(async () => {
    try {
      const data = await apiClient.getAvailableModels();
      console.log("ModelSelection: Raw API data:", data);
      console.log("ModelSelection: Available models:", data.available_models);
      console.log(
        "ModelSelection: Model keys:",
        Object.keys(data.available_models || {})
      );

      setAvailableModels(data.available_models);

      // Initialize empty stats since we don't have stats endpoint anymore
      const statsObject: Record<string, ModelStats> = {};
      Object.keys(data.available_models || {}).forEach((modelName: string) => {
        statsObject[modelName] = {
          usage_stats: {
            avg_processing_time: 0,
            total_analyses: 0,
            avg_confidence: 0,
          },
        };
      });
      setModelStats(statsObject);
    } catch (error) {
      console.error("Error fetching models:", error);
    } finally {
      setLoadingModels(false);
    }
  }, []);

  useEffect(() => {
    void fetchAvailableModels();
  }, [fetchAvailableModels]);

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

  const getCostTierColor = (costTier?: string, isFree?: boolean) => {
    if (isFree) return "text-green-400";
    switch (costTier) {
      case "ultra_low":
        return "text-green-300";
      case "low":
        return "text-yellow-300";
      case "medium":
        return "text-orange-300";
      case "high":
        return "text-red-300";
      default:
        return "text-gray-300";
    }
  };

  const getCostTierLabel = (costTier?: string, isFree?: boolean) => {
    if (isFree) return "Free";
    switch (costTier) {
      case "ultra_low":
        return "Ultra Low Cost";
      case "low":
        return "Low Cost";
      case "medium":
        return "Medium Cost";
      case "high":
        return "High Cost";
      default:
        return "Unknown Cost";
    }
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
          relative p-4 rounded-lg border-2 cursor-pointer bg-card transition-all
          ${isSelected
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
        <div className="grid grid-cols-1 gap-2 mb-3 text-xs">
          <div className="flex items-center gap-1 text-gray-400">
            <Clock className="w-3 h-3" />
            {stats?.usage_stats?.avg_processing_time
              ? `${stats.usage_stats.avg_processing_time}s avg`
              : "No usage data"}
          </div>
          <div className="flex items-center gap-1">
            <DollarSign className="w-3 h-3 text-gray-400" />
            <span className={getCostTierColor(model.cost_tier, model.is_free)}>
              {model.cost_per_1k_tokens === 0
                ? "Free"
                : `$${model.cost_per_1k_tokens}/1k tokens`}
            </span>
          </div>
          <div className="text-xs">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${model.is_free
              ? "bg-green-500/20 text-green-300"
              : "bg-blue-500/20 text-blue-300"
              }`}>
              {getCostTierLabel(model.cost_tier, model.is_free)}
            </span>
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

  console.log("ModelSelection: Available models object:", availableModels);
  console.log("ModelSelection: Local models:", localModels);
  console.log("ModelSelection: API models:", apiModels);
  console.log(
    "ModelSelection: Looking for codellama:13b:",
    availableModels["codellama:13b"]
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
          {!localOllamaStatus.available && localOllamaStatus.blockedReason && (
            <p className="text-sm text-red-400 mb-3" role="status">
              {localOllamaStatus.blockedReason}
            </p>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {localModels.map(([modelName, model]) => (
              <ModelCard key={modelName} modelName={modelName} model={model} />
            ))}
          </div>
        </div>
      )}

      {localModels.length === 0 && localOllamaStatus.blockedReason && (
        <div className="rounded-md border border-red-700 bg-red-900/20 p-4 text-sm text-red-200" role="alert">
          {localOllamaStatus.blockedReason}
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
            • <strong>GPT-4.1 models</strong> offer 1M token context with major coding improvements
          </li>
          <li>
            • <strong>O-series models</strong> are optimized for reasoning and math
          </li>
          <li>
            • <strong>GPT-4o Mini</strong> provides excellent cost-efficiency
          </li>
          <li>
            • <strong>Claude</strong> focuses on code quality and best practices
          </li>
        </ul>
      </div>
    </div>
  );
};
