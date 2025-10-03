import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { apiClient } from "../api/client";
import { defaultModels } from "../types";
import type {
  AIModel,
  ModelAvailabilityMap,
  ModelAvailabilityResponse,
} from "../types";

export const useModelAvailability = () => {
  const { data: availableModelsResponse } = useQuery<ModelAvailabilityResponse>(
    {
      queryKey: ["available-models"],
      queryFn: async () => apiClient.getAvailableModels(),
      refetchInterval: 30000, // Check every 30 seconds
    }
  );

  return useMemo<AIModel[]>(() => {
    if (!availableModelsResponse?.available_models) {
      // Fallback to defaultModels with all unavailable if API fails
      return defaultModels.map((model) => ({
        ...model,
        is_available: false,
      }));
    }

    const apiModels: ModelAvailabilityMap =
      availableModelsResponse.available_models;

    // Transform API response to match expected format
    return Object.entries(apiModels).map(([modelKey, apiModel]) => {
      const normalizedModel: AIModel = {
        id: apiModel.name ?? modelKey,
        name: apiModel.name,
        display_name: apiModel.display_name,
        provider: apiModel.provider,
        model_type: "llm",
        context_window: apiModel.context_window,
        cost_per_1k_tokens: apiModel.cost_per_1k_tokens,
        strengths: apiModel.strengths ?? [],
        created_at: new Date().toISOString(),
        usage_count: 0,
        is_available: apiModel.available,
      };

      return normalizedModel;
    });
  }, [availableModelsResponse]);
};
