import React from "react";
import { motion } from "framer-motion";
import { Sparkles, Github, Loader2, Search } from "lucide-react";
import { Button } from "../../ui/button";
import type { AIModel } from "../../../types/ai";

/**
 * MASingleAnalysisSection - Handles single model analysis UI
 * @param selectedModel The selected AI model
 * @param repoUrl The repository URL
 * @param setRepoUrl Setter for repo URL
 * @param handleKeyPress Key press handler
 * @param handleSingleAnalysis Analysis trigger
 * @param createRepoPending Is repo creation pending
 * @param isAnalyzing Is analysis running
 */
export interface MASingleAnalysisSectionProps {
    selectedModel?: AIModel;
    repoUrl: string;
    setRepoUrl: (url: string) => void;
    handleKeyPress: (e: React.KeyboardEvent, action: () => void) => void;
    handleSingleAnalysis: () => void;
    createRepoPending: boolean;
    isAnalyzing: boolean;
}

export const MASingleAnalysisSection: React.FC<MASingleAnalysisSectionProps> = ({
    selectedModel,
    repoUrl,
    setRepoUrl,
    handleKeyPress,
    handleSingleAnalysis,
    createRepoPending,
    isAnalyzing,
}) => (
    <div className="space-y-4">
        {/* Selected Model Info */}
        {selectedModel && (
            <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="rounded-md p-3 text-sm border bg-[color:var(--ctan-card)] border-[color:var(--ctan-border)]"
            >
                <div className="flex items-center gap-2 mb-1">
                    <Sparkles className="w-4 h-4 text-[#FFA500] ctan-icon" />
                    <span className="font-medium text-[#FFA500]">
                        {selectedModel.display_name}
                    </span>
                </div>
                <div className="text-xs text-ctan-text-secondary space-y-1">
                    <p>Provider: {selectedModel.provider}</p>
                    <p>Strengths: {selectedModel.strengths.join(", ")}</p>
                    <p>
                        Context: {selectedModel.context_window.toLocaleString()} tokens
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
                onKeyPress={(e) => handleKeyPress(e, handleSingleAnalysis)}
                placeholder="https://github.com/username/repositoryaa"
                className="w-full pl-10 pr-4 py-3 rounded-md border repo-input border-ctan-dark-border bg-ctan-dark-hover text-sm placeholder:text-ctan-text-muted focus:outline-none focus:ring-2 focus:ring-ctan-gold focus:border-transparent transition-all duration-300"
                disabled={createRepoPending}
            />
        </div>

        <Button
            onClick={handleSingleAnalysis}
            disabled={createRepoPending || !repoUrl.trim() || !selectedModel}
            className="ctan-button w-full"
            size="lg"
        >
            {createRepoPending ? (
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
);
