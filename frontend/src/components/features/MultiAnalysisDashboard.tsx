import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import toast, { Toaster } from "react-hot-toast";

import { TabsContent } from "../ui/tabs";
// import * as Select from "@radix-ui/react-select";
import {
  useCreateRepository,
  useRepository,
} from "../../hooks/useRepository";
import { useUserRepositories, useGlobalRepositories, useUserRelevantRepositories } from "../../hooks/useRepositoryScoped";
import { ModelSelection } from "../ai/ModelSelection";
// import type { AIModel } from "../../types/ai";
import type { RepositoryCreateRequest } from "../../types/api";
import { useModelAvailability } from "../../hooks/useModelAvailability";
import { apiClient } from "../../api/client";

// Import styles
import "../../styles/ctan-brand.css";

// ModelSelect is now imported from components/ai/ModelSelect
// import { ModelSelect } from "../ai/ModelSelect";
import { MAHeader } from "./multi-analysis/MAHeader";
import { MAAnalysisModeTabs } from "./multi-analysis/MAAnalysisModeTabs";
import { MASingleAnalysisSection } from "./multi-analysis/MASingleAnalysisSection";
import { MACompareAnalysisSection } from "./multi-analysis/MACompareAnalysisSection";
import { MARepositoryTabs, type RepositoryScope } from "./multi-analysis/MARepositoryTabs";
import { MAResultsSection } from "./multi-analysis/MAResultsSection";


export const MultiAnalysisDashboard: React.FC = () => {
  const [repoUrl, setRepoUrl] = useState("");
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string | undefined>(undefined);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [analysisMode, setAnalysisMode] = useState<"single" | "compare">("single");
  const [comparisonResults, setComparisonResults] = useState<unknown>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [repositoryScope, setRepositoryScope] = useState<RepositoryScope>("user");

  const createRepo = useCreateRepository();
  const { data: selectedRepo } = useRepository(selectedRepoId);

  // Use scoped repository hooks
  const { data: userRepositories = [], isLoading: isLoadingUser } = useUserRepositories();
  const { data: globalRepositories = [], isLoading: isLoadingGlobal } = useGlobalRepositories();
  const { data: relevantRepositories = [], isLoading: isLoadingRelevant } = useUserRelevantRepositories();

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

  // Track analysisStarted state based on repo status
  useEffect(() => {
    if (selectedRepo?.status === "analyzing") {
      setAnalysisStarted(true);
    } else if (selectedRepo?.status === "completed" || selectedRepo?.status === "failed") {
      setAnalysisStarted(false);
    }
  }, [selectedRepo?.status]);

  // Handle single analysis
  const handleSingleAnalysis = async () => {
    if (!repoUrl.trim() || !selectedModelId) {
      toast.error("⚠️ Missing required fields - Please enter a repository URL and select an AI model to begin analysis");
      return;
    }

    // Check if selected model is available
    const selectedModel = availableModels.find((m) => m.id === selectedModelId);
    if (!selectedModel?.is_available) {
      const providerName = selectedModel?.provider === 'openai' ? 'OpenAI' :
        selectedModel?.provider === 'anthropic' ? 'Anthropic' :
          selectedModel?.provider || 'provider';
      toast.error(
        `🔒 ${selectedModel?.display_name || 'This model'} requires an API key. Please add your ${providerName} API key in Settings → API Keys to unlock this model.`,
        { duration: 6000 }
      );
      return;
    }

    setAnalysisStarted(true); // Immediately show analyzing state
    try {
      const modelName = selectedModel?.name;

      console.log("🤖 Selected Model ID:", selectedModelId);
      console.log("🤖 Selected Model Name:", modelName);
      console.log("🤖 Selected Model Object:", selectedModel);

      const repoPayload: RepositoryCreateRequest = {
        url: repoUrl,
        model_id: modelName, // Pass the model name, not ID
      };

      console.log("🚀 Repository Payload:", repoPayload);

      const repo = await createRepo.mutateAsync(repoPayload);
      setSelectedRepoId(repo.id);
      setRepoUrl("");
      toast.success(`🚀 Analysis started successfully! Processing repository with ${selectedModel?.display_name || selectedModel?.name || 'selected model'}`);
    } catch (error) {
      setAnalysisStarted(false); // Reset if error
      console.error("Failed to create repository for analysis:", error);
    }
  };

  // Handle comparison analysis
  const handleComparisonAnalysis = async () => {
    if (!repoUrl.trim() || selectedModels.length < 2) {
      toast.error("⚠️ Comparison requires multiple models - Please select at least 2 different AI models to compare results");
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
  const isAnalyzing = analysisStarted || selectedRepo?.status === "analyzing";

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "linear-gradient(145deg, #383b44, #181818)",
            color: "#ffb700",
            border: "1px solid rgba(255, 183, 0, 0.3)",
            borderRadius: "8px",
            boxShadow: "0 4px 12px rgba(255, 183, 0, 0.1)",
            backdropFilter: "blur(10px)",
            fontSize: "14px",
            fontWeight: "500",
          },
          success: {
            iconTheme: {
              primary: "#ffb700",
              secondary: "#181818",
            },
            style: {
              background: "linear-gradient(145deg, #2d3d2f, #1a1a1a)",
              border: "1px solid rgba(34, 197, 94, 0.3)",
              color: "#22c55e",
            },
          },
          error: {
            iconTheme: {
              primary: "#ff4444",
              secondary: "#181818",
            },
            style: {
              background: "linear-gradient(145deg, #3d2d2d, #1a1a1a)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#ef4444",
            },
          },
        }}
      />
      <div className="min-h-screen bg-ctan-dark-bg">
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          {/* Header */}
          {/* Dashboard Header */}
          <MAHeader />


          {/* Main Analysis Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8 bg-card"
          >
            <div className="bg-ctan-card rounded-lg p-6 shadow-xl">
              {/* Analysis Mode Tabs (componentized) */}
              <MAAnalysisModeTabs
                analysisMode={analysisMode}
                setAnalysisMode={setAnalysisMode}
                availableModels={availableModels}
                selectedModelId={selectedModelId}
                setSelectedModelId={setSelectedModelId}
                createRepoPending={createRepo.isPending}
                isAnalyzing={isAnalyzing}
              >

                <TabsContent value="single" className="space-y-4 bg-card">
                  <MASingleAnalysisSection
                    selectedModel={selectedModel}
                    repoUrl={repoUrl}
                    setRepoUrl={setRepoUrl}
                    handleKeyPress={handleKeyPress}
                    handleSingleAnalysis={handleSingleAnalysis}
                    createRepoPending={createRepo.isPending}
                  />
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
                  <MACompareAnalysisSection
                    selectedModels={selectedModels}
                    repoUrl={repoUrl}
                    setRepoUrl={setRepoUrl}
                    handleKeyPress={handleKeyPress}
                    handleComparisonAnalysis={handleComparisonAnalysis}
                    isComparing={isComparing}
                  />
                </TabsContent>
              </MAAnalysisModeTabs>
            </div>

            {/* Repository Tabs */}
            <MARepositoryTabs
              userRepositories={userRepositories}
              globalRepositories={globalRepositories}
              relevantRepositories={relevantRepositories}
              selectedRepoId={selectedRepoId}
              setSelectedRepoId={setSelectedRepoId}
              isLoadingUser={isLoadingUser}
              isLoadingGlobal={isLoadingGlobal}
              isLoadingRelevant={isLoadingRelevant}
              currentScope={repositoryScope}
              onScopeChange={setRepositoryScope}
            />
          </motion.div>

          {/* Analysis Results */}
          <MAResultsSection
            analysisMode={analysisMode}
            isAnalyzing={isAnalyzing}
            selectedRepoId={selectedRepoId}
            selectedRepo={selectedRepo}
            selectedModel={selectedModel}
            comparisonResults={comparisonResults}
          />
        </div>
      </div>
    </>
  );
};
