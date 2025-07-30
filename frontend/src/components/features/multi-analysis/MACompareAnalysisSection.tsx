import React from "react";
import { Github, Loader2 } from "lucide-react";
import { Button } from "../../ui/button";
import type { AIModel } from "../../../types/ai";

/**
 * MACompareAnalysisSection - Handles multi-model comparison UI
 * @param selectedModels The selected AI model IDs
 * @param onModelToggle Handler to toggle model selection
 * @param repoUrl The repository URL
 * @param setRepoUrl Setter for repo URL
 * @param handleKeyPress Key press handler
 * @param handleComparisonAnalysis Analysis trigger
 * @param isComparing Is comparison running
 */
export interface MACompareAnalysisSectionProps {
    selectedModels: string[];
    onModelToggle: (id: string) => void;
    repoUrl: string;
    setRepoUrl: (url: string) => void;
    handleKeyPress: (e: React.KeyboardEvent, action: () => void) => void;
    handleComparisonAnalysis: () => void;
    isComparing: boolean;
}

export const MACompareAnalysisSection: React.FC<MACompareAnalysisSectionProps> = ({
    selectedModels,
    onModelToggle,
    repoUrl,
    setRepoUrl,
    handleKeyPress,
    handleComparisonAnalysis,
    isComparing,
}) => (
    <div className="space-y-4">
        {/* Multi-Model Selection (to be replaced with a dedicated component if needed) */}
        {/* <ModelSelection ... /> */}
        <div className="relative bg-[color:var(--ctan-card)] border border-[color:var(--ctan-border)] rounded-md p-3">
            <Github className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-ctan-gold" />
            <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyPress={(e) => handleKeyPress(e, handleComparisonAnalysis)}
                placeholder="https://github.com/username/repository"
                className="w-full pl-10 pr-4 py-3 rounded-md border border-ctan-dark-border bg-ctan-dark-hover text-sm text-ctan-text-primary placeholder:text-ctan-text-muted focus:outline-none focus:ring-2 focus:ring-ctan-gold focus:border-transparent transition-all duration-300"
                disabled={isComparing}
            />
        </div>
        <Button
            onClick={handleComparisonAnalysis}
            disabled={isComparing || !repoUrl.trim() || selectedModels.length < 2}
            className="ctan-button w-full"
            size="lg"
        >
            {isComparing ? (
                <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Comparing...
                </>
            ) : (
                <>Compare Selected Models</>
            )}
        </Button>
    </div>
);
