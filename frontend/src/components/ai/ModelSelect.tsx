import React from "react";
import { Brain, ChevronDown } from "lucide-react";
import * as Select from "@radix-ui/react-select";
import type { AIModel } from "../../types/ai";
import { useLocalOllama } from "../../hooks/useLocalOllama";

/**
 * ModelSelect - Dropdown for selecting an AI model
 * @param models List of available models
 * @param selectedModelId Currently selected model id
 * @param onModelChange Callback for model change
 * @param disabled Optional disabled state
 */
export const ModelSelect: React.FC<{
    models: AIModel[];
    selectedModelId: string | undefined;
    onModelChange: (id: string) => void;
    disabled?: boolean;
}> = ({ models, selectedModelId, onModelChange, disabled }) => {
    const { status } = useLocalOllama();

    // Build size map from local Ollama for fallback
    const localSizeMap = React.useMemo(() => {
        const map: Record<string, number> = {};
        for (const m of status.models) {
            map[m.name] = m.size;
        }
        return map;
    }, [status.models]);

    const formatCloudPrice = (val: number): string => {
        // Display two decimals. If current values are per-100 tokens, multiply by 10.
        // Heuristic: if val < 0.01 and > 0, show (val*10). Otherwise show val.
        if (val > 0 && val < 0.01) {
            return (val * 10).toFixed(2);
        }
        return val.toFixed(2);
    };

    const formatGB = (bytes: number | undefined): string | null => {
        if (!bytes || bytes <= 0) return null;
        const gb = bytes / (1024 * 1024 * 1024);
        return `${gb.toFixed(1)} GB`;
    };

    const getSizeDisplay = (model: AIModel): string | null => {
        // Prefer backend-provided size_gb if available
        if (model.size_gb !== undefined && model.size_gb > 0) {
            return `${model.size_gb.toFixed(1)} GB`;
        }

        // Fall back to local Ollama hook for size bytes
        if (model.provider.includes("llama") || model.provider.includes("Ollama")) {
            const localSize = localSizeMap[model.name];
            return formatGB(localSize);
        }

        return null;
    };

    return (
        <Select.Root
            value={selectedModelId}
            onValueChange={onModelChange}
            disabled={disabled}
        >
            <Select.Trigger className="model-select-trigger text-[#ffb700] inline-flex items-center justify-between rounded-md px-4 py-2 text-sm gap-2 hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ctan-gold focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[placeholder]:text-muted-foreground min-w-[280px] transition-all duration-300">
                <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-ctan-gold" />
                    <Select.Value placeholder="Select AI model..." />
                </div>
                <Select.Icon>
                    <ChevronDown className="w-4 h-4 opacity-50" />
                </Select.Icon>
            </Select.Trigger>

            <Select.Portal>
                <Select.Content className="overflow-hidden text-[#ffb700] bg-[#161618] rounded-md shadow-2xl border border-ctan-dark-border max-h-[60vh] will-change-transform">
                    <Select.ScrollUpButton className="flex items-center justify-center h-6 bg-ctan-dark-card text-muted-foreground cursor-default">
                        <ChevronDown className="w-4 h-4 rotate-180" />
                    </Select.ScrollUpButton>

                    <Select.Viewport className="p-1 max-h-64 overflow-auto overscroll-contain">
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
                                        className="relative flex items-center px-6 py-2 text-sm rounded select-none hover:bg-ctan-dark-hover hover:text-accent-foreground focus:bg-ctan-dark-hover focus:text-accent-foreground cursor-pointer transition-all duration-200"
                                    >
                                        <Select.ItemText>
                                            <div className="flex items-center justify-between w-full">
                                                <span>
                                                    {model.display_name}
                                                    {(() => {
                                                        const sizeDisplay = getSizeDisplay(model);
                                                        return sizeDisplay ? (
                                                            <span className="ml-2 opacity-70 text-xs">
                                                                - {sizeDisplay}
                                                            </span>
                                                        ) : null;
                                                    })()}
                                                </span>
                                                {!model.is_available && (
                                                    <span className="text-xs ml-2 text-amber-500">
                                                        🔒 Not Running
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
                                        className="relative flex items-center px-6 py-2 text-sm rounded select-none hover:bg-ctan-dark-hover hover:text-accent-foreground focus:bg-ctan-dark-hover focus:text-accent-foreground cursor-pointer transition-all duration-200"
                                    >
                                        <Select.ItemText>
                                            <div className="flex items-center justify-between w-full">
                                                <span>
                                                    {model.display_name}
                                                    {!model.is_available && (
                                                        <span className="ml-2 text-xs text-amber-500 font-medium">
                                                            🔒 Requires Key
                                                        </span>
                                                    )}
                                                </span>
                                                <span className="text-xs text-ctan-amber">
                                                    ${formatCloudPrice(model.cost_per_1k_tokens)}/1k
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
