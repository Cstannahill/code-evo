import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Toaster } from "react-hot-toast";
import { Github, Loader2, Search, X } from "lucide-react";
import { Button } from "../ui/button";
import {
  useCreateRepository,
  useRepository,
  useRepositories,
} from "../../hooks/useRepository"; // Assuming useCreateRepository's input type is defined here or in a related file
import { AnalysisDashboard } from "./AnalysisDashboard";
import { ModelSelectComponent } from "../ai/ModelSelectComponent";
// Corrected type-only import for AIModel due to verbatimModuleSyntax
import { defaultModels, type AIModel } from "../../types/ai";

// This interface describes the shape ModelSelectComponent expects for its 'models' prop values,
// based on the error message (needs 'available') and component usage (uses 'display_name').
interface ModelInfoForSelect {
  id: string; // Keep id for consistency if needed, and it's part of AIModel
  display_name: string; // Used by ModelSelectComponent
  available: boolean; // Required by ModelInfo as per error TS2322
  // Include other properties from AIModel if they are intended to be passed through
  // or used by ModelSelectComponent indirectly.
  name: string;
  provider: string;
  model_type: string;
  context_window: number;
  cost_per_1k_tokens: number;
  strengths: string[];
  created_at: string;
  usage_count: number;
}

export const Dashboard: React.FC = () => {
  const [repoUrl, setRepoUrl] = useState("");
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string | undefined>(
    undefined
  );

  const createRepo = useCreateRepository();
  const { data: selectedRepo } = useRepository(selectedRepoId);
  const { data: repositories = [] } = useRepositories();

  // Transform defaultModels (AIModel[]) into Record<string, ModelInfoForSelect>
  // to match the structure expected by ModelSelectComponent.
  const modelsForSelect: Record<string, ModelInfoForSelect> = useMemo(() => {
    return defaultModels.reduce((acc, model) => {
      // Create a new object conforming to ModelInfoForSelect
      // by mapping is_available to available and including other necessary fields.
      const { is_available, ...restOfModel } = model;
      acc[model.id] = {
        ...restOfModel,
        available: is_available, // Map AIModel's 'is_available' to 'available'
      };
      return acc;
    }, {} as Record<string, ModelInfoForSelect>);
  }, []); // defaultModels is a constant import

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim() || !selectedModelId) return;

    try {
      // TODO: The type for useCreateRepository().mutateAsync needs to be updated
      // in its definition (likely in '../../hooks/useRepository.ts')
      // to include 'model_id: string'.
      // For example: interface CreateRepositoryInput { url: string; branch?: string; model_id?: string; }
      const repoPayload: any = {
        // Using 'any' temporarily to bypass TS error; type definition should be fixed
        url: repoUrl,
        model_id: selectedModelId,
      };
      const repo = await createRepo.mutateAsync(repoPayload);
      setSelectedRepoId(repo.id);
      setRepoUrl("");
    } catch (error) {
      // Error handled by mutation
      console.error("Failed to create repository for analysis:", error);
    }
  };

  const isAnalyzing = selectedRepo?.status === "analyzing";

  return (
    <>
      <Toaster position="top-right" />
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          {/* Header */}
          <motion.header
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-12"
          >
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
              Code Evolution Tracker
            </h1>
            <p className="text-lg text-muted-foreground">
              AI-powered repository analysis to understand your coding journey
            </p>
          </motion.header>

          {/* Model Selection */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="mb-6"
          >
            <ModelSelectComponent
              models={modelsForSelect} // Pass the transformed Record
              selectedModelName={selectedModelId}
              onSelectedModelChange={setSelectedModelId}
              placeholder="Select an AI Model..."
              disabled={createRepo.isPending || isAnalyzing}
            />
          </motion.div>

          {/* Repository Selection */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8"
          >
            <form onSubmit={handleAnalyze} className="flex gap-4 mb-4">
              <div className="relative flex-1">
                <Github className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/username/repository"
                  className="w-full pl-10 pr-4 py-2 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  disabled={createRepo.isPending}
                />
              </div>
              <Button
                type="submit"
                disabled={
                  createRepo.isPending || !repoUrl.trim() || !selectedModelId
                }
                className="border border-gray-400/60"
              >
                {createRepo.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Analyze
                  </>
                )}
              </Button>
            </form>

            {/* Repository List */}
            {repositories.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {repositories.map((repo) => (
                  <Button
                    key={repo.id}
                    variant={selectedRepoId === repo.id ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedRepoId(repo.id)}
                    className="text-xs"
                  >
                    {repo.name}
                    {repo.status === "analyzing" && (
                      <Loader2 className="w-3 h-3 ml-1 animate-spin" />
                    )}
                  </Button>
                ))}
              </div>
            )}
          </motion.div>

          {/* Analysis Display */}
          <AnimatePresence mode="wait">
            {selectedRepoId && selectedRepo ? (
              <motion.div
                key={selectedRepoId}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                {isAnalyzing ? (
                  // ... (rest of the component is the same)
                  <div className="text-center py-20">
                    <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-primary" />
                    <h3 className="text-xl font-semibold mb-2">
                      Analyzing Repository
                    </h3>
                    <p className="text-muted-foreground">
                      This may take a few minutes depending on the repository
                      size...
                    </p>
                    <div className="mt-8 inline-flex items-center gap-2 text-sm text-muted-foreground">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      AI is processing your code patterns
                    </div>
                  </div>
                ) : selectedRepo.status === "completed" ? (
                  <AnalysisDashboard repositoryId={selectedRepoId} />
                ) : (
                  <div className="text-center py-20">
                    <X className="w-12 h-12 mx-auto mb-4 text-destructive" />
                    <h3 className="text-xl font-semibold mb-2">
                      Analysis Failed
                    </h3>
                    <p className="text-muted-foreground">
                      Something went wrong. Please try again.
                    </p>
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-20 bg-card rounded-lg border"
              >
                <Github className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-xl font-semibold mb-2">
                  No Repository Selected
                </h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Enter a GitHub repository URL to start the analysis. Make sure
                  to select an AI model above.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  );
};
