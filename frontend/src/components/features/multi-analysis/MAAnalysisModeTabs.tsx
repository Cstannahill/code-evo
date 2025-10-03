import React from "react";
import { Tabs, TabsList, TabsTrigger } from "../../ui/tabs";
import { Brain } from "lucide-react";
import { ModelSelect } from "../../ai/ModelSelect";
import type { AIModel } from "../../../types/ai";

/**
 * MAAnalysisModeTabs - Tabs for switching between single and compare analysis modes
 * @param analysisMode Current mode ("single" | "compare")
 * @param setAnalysisMode Setter for mode
 * @param availableModels List of models
 * @param selectedModelId Selected model id
 * @param setSelectedModelId Setter for model id
 * @param createRepoPending Is repo creation pending
 * @param isAnalyzing Is analysis running
 */
export interface MAAnalysisModeTabsProps {
    analysisMode: "single" | "compare";
    setAnalysisMode: (mode: "single" | "compare") => void;
    availableModels: AIModel[];
    selectedModelId: string | undefined;
    setSelectedModelId: (id: string) => void;
    createRepoPending: boolean;
    isAnalyzing: boolean;
    children: React.ReactNode;
}

export const MAAnalysisModeTabs: React.FC<MAAnalysisModeTabsProps> = ({
    analysisMode,
    setAnalysisMode,
    availableModels,
    selectedModelId,
    setSelectedModelId,
    createRepoPending,
    isAnalyzing,
    children,
}) => (
    <Tabs
        value={analysisMode}
        onValueChange={(v) => setAnalysisMode(v as "single" | "compare")}
    >
        <div className="flex items-center justify-between mb-6">
            <TabsList className="grid w-fit grid-cols-2 bg-ctan-dark-hover text-[#ffd700] ">
                <TabsTrigger
                    value="single"
                    className="ctan-tab flex items-center gap-2 hover:text-[#ffb700]"
                >
                    <Brain className="w-4 h-4" />
                    Analyze
                </TabsTrigger>
                {/* <TabsTrigger
                    value="compare"
                    className="ctan-tab flex items-center gap-2 hover:text-[#ffb700]"
                >
                    <Zap className="w-4 h-4" />
                    Compare Models
                </TabsTrigger> */}
            </TabsList>
            {analysisMode === "single" && (
                <ModelSelect
                    models={availableModels}
                    selectedModelId={selectedModelId}
                    onModelChange={setSelectedModelId}
                    disabled={createRepoPending || isAnalyzing}
                />
            )}
        </div>
        {children}
    </Tabs>
);
