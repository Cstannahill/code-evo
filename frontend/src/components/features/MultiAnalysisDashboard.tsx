import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import toast, { Toaster } from "react-hot-toast";
import {
  Github,
  Loader2,
  Search,
  X,
  Brain,
  Zap,
  BarChart3,
  ChevronDown,
  Sparkles,
} from "lucide-react";
import { Button } from "../ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import * as Select from "@radix-ui/react-select";
import {
  useCreateRepository,
  useRepository,
  useRepositories,
} from "../../hooks/useRepository";
import { AnalysisDashboard } from "./AnalysisDashboard";
import { ModelSelection } from "../ai/ModelSelection";
import { ModelComparisonDashboard } from "../ai/ModelComparisonDashboard";
import type { AIModel } from "../../types/ai";
import type { RepositoryCreateRequest } from "../../types/api";
import { useModelAvailability } from "../../hooks/useModelAvailability";
import { apiClient } from "../../api/client";

// Import styles
import "../../styles/ctan-brand.css";

// Enhanced Select Component with brand styling
const ModelSelect: React.FC<{
  models: AIModel[];
  selectedModelId: string | undefined;
  onModelChange: (id: string) => void;
  disabled?: boolean;
}> = ({ models, selectedModelId, onModelChange, disabled }) => {

  return (
    <Select.Root
      value={selectedModelId}
      onValueChange={onModelChange}
      disabled={disabled}
    >
      <Select.Trigger className="model-select-trigger inline-flex items-center justify-between rounded-md px-4 py-2 text-sm gap-2 hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ctan-gold focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[placeholder]:text-muted-foreground min-w-[280px] transition-all duration-300">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-ctan-gold" />
          <Select.Value placeholder="Select AI model..." />
        </div>
        <Select.Icon>
          <ChevronDown className="w-4 h-4 opacity-50" />
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal>
        <Select.Content className="overflow-hidden bg-ctan-dark-card rounded-md shadow-2xl border border-ctan-dark-border">
          <Select.ScrollUpButton className="flex items-center justify-center h-6 bg-ctan-dark-card text-muted-foreground cursor-default">
            <ChevronDown className="w-4 h-4 rotate-180" />
          </Select.ScrollUpButton>

          <Select.Viewport className="p-1">
            {/* Local Models */}
            <Select.Group>
              <Select.Label className="px-6 py-1.5 text-xs font-medium">
                Local Models (Free)
              </Select.Label>
              {models
                .filter((m) => m.cost_per_1k_tokens === 0)
                .map((model) => (
                  <Select.Item
                    key={model.id}
                    value={model.id}
                    className="relative flex items-center px-6 py-2 text-sm rounded select-none hover:bg-ctan-dark-hover hover:text-accent-foreground focus:bg-ctan-dark-hover focus:text-accent-foreground cursor-pointer data-[disabled]:opacity-50 data-[disabled]:pointer-events-none transition-all duration-200"
                    disabled={!model.is_available}
                  >
                    <Select.ItemText>
                      <div className="flex items-center justify-between w-full">
                        <span>{model.display_name}</span>
                        {!model.is_available && (
                          <span className="text-xs text-muted-foreground ml-2">
                            (Not Available)
                          </span>
                        )}
                      </div>
                    </Select.ItemText>
                    <Select.ItemIndicator className="absolute left-2 inline-flex items-center">
                      <div className="w-2 h-2 rounded-full bg-ctan-gold" />
                    </Select.ItemIndicator>
                  </Select.Item>
                ))}
            </Select.Group>

            {/* API Models */}
            <Select.Separator className="h-px bg-ctan-dark-border my-1" />
            <Select.Group>
              <Select.Label className="px-6 py-1.5 text-xs font-medium text-ctan-gold">
                Cloud Models (Paid)
              </Select.Label>
              {models
                .filter((m) => m.cost_per_1k_tokens > 0)
                .map((model) => (
                  <Select.Item
                    key={model.id}
                    value={model.id}
                    className="relative flex items-center px-6 py-2 text-sm rounded select-none hover:bg-ctan-dark-hover hover:text-accent-foreground focus:bg-ctan-dark-hover focus:text-accent-foreground cursor-pointer data-[disabled]:opacity-50 data-[disabled]:pointer-events-none transition-all duration-200"
                    disabled={!model.is_available}
                  >
                    <Select.ItemText>
                      <div className="flex items-center justify-between w-full">
                        <span>{model.display_name}</span>
                        <span className="text-xs text-ctan-amber">
                          ${model.cost_per_1k_tokens}/1k
                        </span>
                      </div>
                    </Select.ItemText>
                    <Select.ItemIndicator className="absolute left-2 inline-flex items-center">
                      <div className="w-2 h-2 rounded-full bg-ctan-gold" />
                    </Select.ItemIndicator>
                  </Select.Item>
                ))}
            </Select.Group>
          </Select.Viewport>

          <Select.ScrollDownButton className="flex items-center justify-center h-6 bg-ctan-dark-card text-muted-foreground cursor-default">
            <ChevronDown className="w-4 h-4" />
          </Select.ScrollDownButton>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
};

export const MultiAnalysisDashboard: React.FC = () => {
  const [repoUrl, setRepoUrl] = useState("");
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string | undefined>(
    undefined
  );
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [analysisMode, setAnalysisMode] = useState<"single" | "compare">(
    "single"
  );
  const [comparisonResults, setComparisonResults] = useState<any>(null);
  const [isComparing, setIsComparing] = useState(false);

  const createRepo = useCreateRepository();
  const { data: selectedRepo } =
    useRepository(selectedRepoId);
  const { data: repositories = [] } = useRepositories();
  const availableModels = useModelAvailability();
  console.log("Available Models:", availableModels);

  // Set default model when models are loaded
  useEffect(() => {
    if (availableModels.length > 0 && !selectedModelId) {
      const defaultModel = availableModels.find((m) => m.is_available);
      if (defaultModel) {
        setSelectedModelId(defaultModel.id);
      }
    }
  }, [availableModels, selectedModelId]);

  // Handle single analysis
  const handleSingleAnalysis = async () => {
    if (!repoUrl.trim() || !selectedModelId) {
      toast.error("Please enter a repository URL and select an AI model");
      return;
    }

    try {
      const modelName = availableModels.find(
        (m) => m.id === selectedModelId
      )?.name;
      const repoPayload: RepositoryCreateRequest = {
        url: repoUrl,
        model_id: modelName, // Pass the model name, not ID
      };

      const repo = await createRepo.mutateAsync(repoPayload);
      setSelectedRepoId(repo.id);
      setRepoUrl("");
      toast.success("Analysis started!");
    } catch (error) {
      console.error("Failed to create repository for analysis:", error);
    }
  };

  // Handle comparison analysis
  const handleComparisonAnalysis = async () => {
    if (!repoUrl.trim() || selectedModels.length < 2) {
      toast.error("Please enter a repository URL and select at least 2 models");
      return;
    }

    setIsComparing(true);
    try {
      // First create the repository
      const repoPayload: RepositoryCreateRequest = {
        url: repoUrl,
      };
      const repo = await createRepo.mutateAsync(repoPayload);

      // Then run comparison analysis
      const comparisonResponse = await apiClient.compareModels({
        models: selectedModels.map(
          (id) => availableModels.find((m) => m.id === id)?.name || id
        ),
        code: repoUrl, // This would be actual code in real implementation
        language: "javascript",
      });

      setComparisonResults(comparisonResponse);
      setSelectedRepoId(repo.id);
      toast.success("Comparison analysis completed!");
    } catch (error) {
      console.error("Failed to run comparison analysis:", error);
      toast.error("Comparison analysis failed");
    } finally {
      setIsComparing(false);
    }
  };

  const handleModelToggle = (modelId: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelId)
        ? prev.filter((id) => id !== modelId)
        : [...prev, modelId]
    );
  };

  const handleKeyPress = (e: React.KeyboardEvent, action: () => void) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      action();
    }
  };

  const selectedModel = availableModels.find((m) => m.id === selectedModelId);
  const isAnalyzing = selectedRepo?.status === "analyzing";

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "var(--ctan-dark-card)",
            color: "var(--ctan-text-primary)",
            border: "1px solid var(--ctan-dark-border)",
          },
        }}
      />
      <div className="min-h-screen bg-ctan-dark-bg">
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          {/* Header */}
          <motion.header
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-12 text-center"
          >
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4 brand-title">
              Code Evolution
            </h1>
            <p className="text-lg text-ctan-text-secondary">
              AI-powered repository analysis to understand your coding journey
            </p>
          </motion.header>

          {/* Main Analysis Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8"
          >
            <div className="ctan-card rounded-lg p-6 shadow-xl">
              {/* Analysis Mode Tabs */}
              <Tabs
                value={analysisMode}
                onValueChange={(v) =>
                  setAnalysisMode(v as "single" | "compare")
                }
              >
                <div className="flex items-center justify-between mb-6">
                  <TabsList className="grid w-fit grid-cols-2 bg-ctan-dark-hover">
                    <TabsTrigger
                      value="single"
                      className="ctan-tab flex items-center gap-2"
                    >
                      <Brain className="w-4 h-4" />
                      Analyze
                    </TabsTrigger>
                    <TabsTrigger
                      value="compare"
                      className="ctan-tab flex items-center gap-2"
                    >
                      <Zap className="w-4 h-4" />
                      Compare Models
                    </TabsTrigger>
                  </TabsList>

                  {/* Model Selection for Single Analysis */}
                  {analysisMode === "single" && (
                    <ModelSelect
                      models={availableModels}
                      selectedModelId={selectedModelId}
                      onModelChange={setSelectedModelId}
                      disabled={createRepo.isPending || isAnalyzing}
                    />
                  )}
                </div>

                <TabsContent value="single" className="space-y-4">
                  <div className="space-y-4">
                    {/* Selected Model Info */}
                    {selectedModel && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="bg-gradient-to-r from-ctan-dark-hover to-transparent rounded-md p-3 text-sm border border-ctan-dark-border"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <Sparkles className="w-4 h-4 text-ctan-gold ctan-icon" />
                          <span className="font-medium text-ctan-text-primary">
                            {selectedModel.display_name}
                          </span>
                        </div>
                        <div className="text-xs text-ctan-text-secondary space-y-1">
                          <p>Provider: {selectedModel.provider}</p>
                          <p>Strengths: {selectedModel.strengths.join(", ")}</p>
                          <p>
                            Context:{" "}
                            {selectedModel.context_window.toLocaleString()}{" "}
                            tokens
                          </p>
                        </div>
                      </motion.div>
                    )}

                    {/* Repository Input */}
                    <div className="relative">
                      <Github className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-ctan-gold" />
                      <input
                        type="url"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        onKeyPress={(e) =>
                          handleKeyPress(e, handleSingleAnalysis)
                        }
                        placeholder="https://github.com/username/repository"
                        className="w-full pl-10 pr-4 py-3 rounded-md border border-ctan-dark-border bg-ctan-dark-hover text-sm text-ctan-text-primary placeholder:text-ctan-text-muted focus:outline-none focus:ring-2 focus:ring-ctan-gold focus:border-transparent transition-all duration-300"
                        disabled={createRepo.isPending}
                      />
                    </div>

                    <Button
                      onClick={handleSingleAnalysis}
                      disabled={
                        createRepo.isPending ||
                        !repoUrl.trim() ||
                        !selectedModelId
                      }
                      className="ctan-button w-full"
                      size="lg"
                    >
                      {createRepo.isPending ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Search className="w-4 h-4 mr-2" />
                          Start Analysis
                        </>
                      )}
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="compare" className="space-y-4">
                  {/* Multi-Model Selection */}
                  <ModelSelection
                    selectedModels={selectedModels}
                    onModelToggle={handleModelToggle}
                    onAnalyze={() => { }}
                    maxModels={4}
                    analysisType="comparison"
                    loading={isComparing}
                  />

                  <div className="space-y-4">
                    <div className="relative">
                      <Github className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-ctan-gold" />
                      <input
                        type="url"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        onKeyPress={(e) =>
                          handleKeyPress(e, handleComparisonAnalysis)
                        }
                        placeholder="https://github.com/username/repository"
                        className="w-full pl-10 pr-4 py-3 rounded-md border border-ctan-dark-border bg-ctan-dark-hover text-sm text-ctan-text-primary placeholder:text-ctan-text-muted focus:outline-none focus:ring-2 focus:ring-ctan-gold focus:border-transparent transition-all duration-300"
                        disabled={isComparing}
                      />
                    </div>

                    <Button
                      onClick={handleComparisonAnalysis}
                      disabled={
                        isComparing ||
                        !repoUrl.trim() ||
                        selectedModels.length < 2
                      }
                      className="ctan-button w-full"
                      size="lg"
                    >
                      {isComparing ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Comparing Models...
                        </>
                      ) : (
                        <>
                          <BarChart3 className="w-4 h-4 mr-2" />
                          Compare {selectedModels.length} Models
                        </>
                      )}
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            </div>

            {/* Repository List */}
            {repositories.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="mt-4 flex flex-wrap gap-2"
              >
                {repositories.map((repo: any) => (
                  <Button
                    key={repo.id}
                    variant={selectedRepoId === repo.id ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedRepoId(repo.id)}
                    className={`repo-button text-xs ${selectedRepoId === repo.id ? "active" : ""
                      }`}
                  >
                    {repo.name}
                    {repo.status === "analyzing" && (
                      <Loader2 className="w-3 h-3 ml-1 animate-spin" />
                    )}
                  </Button>
                ))}
              </motion.div>
            )}
          </motion.div>

          {/* Analysis Results */}
          <AnimatePresence mode="wait">
            {comparisonResults && analysisMode === "compare" ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <ModelComparisonDashboard
                  results={comparisonResults.individual_results}
                  comparison={comparisonResults.comparison_analysis}
                />
              </motion.div>
            ) : selectedRepoId && selectedRepo && analysisMode === "single" ? (
              <motion.div
                key={selectedRepoId}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                {isAnalyzing ? (
                  <div className="text-center py-20 ctan-card rounded-lg">
                    <div className="ctan-loading inline-block">
                      <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-ctan-gold" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2 text-ctan-text-primary">
                      Analyzing Repository
                    </h3>
                    <p className="text-ctan-text-secondary">
                      This may take a few minutes depending on the repository
                      size...
                    </p>
                    <div className="mt-8 inline-flex items-center gap-2 text-sm text-ctan-text-muted">
                      <div className="w-2 h-2 bg-ctan-gold rounded-full animate-pulse" />
                      {selectedModel && (
                        <span>
                          Using {selectedModel.display_name} for analysis
                        </span>
                      )}
                    </div>
                  </div>
                ) : selectedRepo.status === "completed" ? (
                  <AnalysisDashboard repositoryId={selectedRepoId} />
                ) : (
                  <div className="text-center py-20 ctan-card rounded-lg">
                    <X className="w-12 h-12 mx-auto mb-4 text-destructive" />
                    <h3 className="text-xl font-semibold mb-2 text-ctan-text-primary">
                      Analysis Failed
                    </h3>
                    <p className="text-ctan-text-secondary">
                      Something went wrong. Please try again.
                    </p>
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-20 ctan-card rounded-lg"
              >
                <Github className="w-16 h-16 mx-auto mb-4 text-ctan-gold ctan-icon" />
                <h3 className="text-xl font-semibold mb-2 text-ctan-text-primary">
                  Ready to Analyze
                </h3>
                <p className="text-ctan-text-secondary max-w-md mx-auto">
                  Choose an analysis mode above, select your AI model(s), and
                  enter a GitHub repository URL to begin.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  );
};
