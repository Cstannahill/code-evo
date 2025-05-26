import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { defaultModels } from "../types/ai";
import { useMemo } from "react";

export const useModelAvailability = () => {
  const { data: aiStatus } = useQuery({
    queryKey: ["ai-status"],
    queryFn: () => apiClient.getAnalysisStatus(),
    refetchInterval: 30000, // Check every 30 seconds
  });

  return useMemo(() => {
    return defaultModels.map((model) => ({
      ...model,
      is_available:
        model.provider === "Ollama (Local)"
          ? aiStatus?.ai_service?.ollama_available &&
            aiStatus?.ai_service?.ollama_model === model.name
          : false, // For external APIs, you'd check API keys here
    }));
  }, [aiStatus]);
};
