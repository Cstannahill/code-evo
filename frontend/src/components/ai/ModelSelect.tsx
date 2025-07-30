import React from "react";
import { Brain, ChevronDown } from "lucide-react";
import * as Select from "@radix-ui/react-select";
import type { AIModel } from "../../types/ai";

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
                <Select.Content className="overflow-hidden text-[#ffb700] bg-[#161618] rounded-md shadow-2xl border border-ctan-dark-border">
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
                                                    <span className="text-xs ml-2">
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
