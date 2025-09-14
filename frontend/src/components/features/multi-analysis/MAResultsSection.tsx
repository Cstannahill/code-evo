import React from "react";
import { motion } from "framer-motion";
import { Loader2, X, Github } from "lucide-react";
import { AnalysisDashboard } from "../AnalysisDashboard";
import { ModelSelector } from "../../shared/ModelSelector";
import { apiClient } from "../../../api/client";

/**
 * MAResultsSection - Handles display of analysis results, loading, and errors
 * @param analysisMode Current analysis mode (single/compare)
 * @param isAnalyzing Is analysis running
 * @param selectedRepoId Selected repository ID
 * @param selectedRepo Selected repository object
 * @param selectedModel Selected AI model object
 * @param comparisonResults Results for comparison mode
 */
export interface MAResultsSectionProps {
    analysisMode: "single" | "compare";
    isAnalyzing: boolean;
    selectedRepoId: string | null;
    selectedRepo?: { status: string };
    selectedModel?: { display_name: string };
    comparisonResults?: unknown;
}


export const MAResultsSection: React.FC<MAResultsSectionProps> = ({
    analysisMode,
    isAnalyzing,
    selectedRepoId,
    selectedRepo,
    selectedModel,
    comparisonResults,
}) => {
    // Always render AnalysisDashboard, but control its rendering with props
    const shouldShowAnalysisDashboard =
        selectedRepoId && selectedRepo && analysisMode === "single" && selectedRepo.status === "completed";

    const [modelOverride, setModelOverride] = React.useState<string | null>(null);
    const [_byModel, setByModel] = React.useState<unknown | null>(null);
    const [loadingModel, setLoadingModel] = React.useState(false);
    const [modelError, setModelError] = React.useState<string | null>(null);

    React.useEffect(() => {
        let cancelled = false;
        (async () => {
            if (!selectedRepoId) return;
            if (!modelOverride) {
                setByModel(null);
                return;
            }
            try {
                setLoadingModel(true);
                setModelError(null);
                const data = await apiClient.getRepositoryAnalysisByModel(selectedRepoId, modelOverride);
                if (!cancelled) setByModel(data);
            } catch {
                if (!cancelled) setModelError("Failed to load model-specific analysis");
            } finally {
                if (!cancelled) setLoadingModel(false);
            }
        })();
        return () => { cancelled = true; };
    }, [selectedRepoId, modelOverride]);

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="dark:text-[#ffd700]">
            {comparisonResults && analysisMode === "compare" ? (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    {/* ModelComparisonDashboard should be rendered here */}
                </motion.div>
            ) : selectedRepoId && selectedRepo && analysisMode === "single" ? (
                <motion.div key={selectedRepoId} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    {isAnalyzing ? (
                        <div className="text-center py-20 ctan-card rounded-lg">
                            <div className="ctan-loading inline-block">
                                <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-ctan-gold" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2 text-ctan-text-primary">Analyzing Repository</h3>
                            <p className="text-ctan-text-secondary">This may take a few minutes depending on the repository size...</p>
                            <div className="mt-8 inline-flex items-center gap-2 text-sm text-ctan-text-muted">
                                <div className="w-2 h-2 bg-ctan-gold rounded-full animate-pulse" />
                                {selectedModel && <span>Using {selectedModel.display_name} for analysis</span>}
                            </div>
                        </div>
                    ) : shouldShowAnalysisDashboard ? (
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="text-sm text-muted-foreground">
                                    {selectedModel ? `Using ${selectedModel.display_name}` : "Default model"}
                                    {modelOverride ? ` · Override: ${modelOverride}` : ""}
                                    {loadingModel ? " · Loading…" : ""}
                                    {modelError ? ` · ${modelError}` : ""}
                                </div>
                                <ModelSelector
                                    repositoryId={selectedRepoId}
                                    selectedModel={modelOverride}
                                    onChange={setModelOverride}
                                />
                            </div>
                            {/* Pass through repositoryId. The dashboard already calls hooks that fetch base/enhanced.
                                                    If a model override is chosen, child sections that rely on pattern/quality could be
                                                    optionally adapted to accept overrides; for now, we keep base rendering and show the
                                                    selected model context in the header. */}
                            <AnalysisDashboard repositoryId={selectedRepoId} />
                        </div>
                    ) : (
                        <div className="text-center py-20 ctan-card rounded-lg">
                            <X className="w-12 h-12 mx-auto mb-4 text-destructive" />
                            <h3 className="text-xl font-semibold mb-2 text-ctan-text-primary">Analysis Failed</h3>
                            <p className="text-ctan-text-secondary">Something went wrong. Please try again.</p>
                        </div>
                    )}
                </motion.div>
            ) : (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20 ctan-card rounded-lg">
                    <Github className="w-16 h-16 mx-auto mb-4 text-ctan-gold ctan-icon" />
                    <h3 className="text-xl font-semibold mb-2 text-ctan-text-primary">Ready to Analyze</h3>
                    <p className="text-ctan-text-secondary max-w-md mx-auto">Choose an analysis mode above, select your AI model(s), and enter a GitHub repository URL to begin.</p>
                </motion.div>
            )}
        </motion.div>
    );
};
