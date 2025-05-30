import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { defaultModels } from "../types/ai";
import { useMemo } from "react";

export const useModelAvailability = () => {
  const { data: availableModelsResponse } = useQuery({
    queryKey: ["available-models"],
    queryFn: () => apiClient.getAvailableModels(),
    refetchInterval: 30000, // Check every 30 seconds
  });

  return useMemo(() => {
    if (!availableModelsResponse?.available_models) {
      // Fallback to defaultModels with all unavailable if API fails
      return defaultModels.map((model) => ({
        ...model,
        is_available: false,
      }));
    }

    const apiModels = availableModelsResponse.available_models;
    
    // Transform API response to match expected format
    return Object.values(apiModels).map((apiModel: any) => ({
      id: apiModel.name || Object.keys(apiModels).find(key => apiModels[key] === apiModel) || '',
      name: apiModel.name,
      display_name: apiModel.display_name,
      provider: apiModel.provider,
      model_type: 'llm', // Default type
      context_window: apiModel.context_window,
      cost_per_1k_tokens: apiModel.cost_per_1k_tokens,
      strengths: apiModel.strengths || [],
      created_at: new Date().toISOString(), // Default value
      usage_count: 0, // Default value
      is_available: apiModel.available,
    }));
  }, [availableModelsResponse]);
};
