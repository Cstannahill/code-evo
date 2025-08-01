// src/hooks/useRepositoryAnalysis.ts

import type { UseQueryResult } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { RepositoryAnalysis, EnhancedRepositoryAnalysisResponse } from "../types/api";

export const useRepositoryAnalysis = (
  repoId: string | null,
  useEnhanced: boolean = false
): UseQueryResult<RepositoryAnalysis | EnhancedRepositoryAnalysisResponse, Error> => {
  return useQuery<RepositoryAnalysis | EnhancedRepositoryAnalysisResponse, Error>({
    queryKey: ["repositoryAnalysis", repoId, useEnhanced],
    queryFn: async () => {
      if (useEnhanced) {
        try {
          return await apiClient.getEnhancedRepositoryAnalysis(repoId!);
        } catch (error) {
          console.warn("Enhanced analysis not available, falling back to standard:", error);
          return await apiClient.getRepositoryAnalysis(repoId!);
        }
      }
      return apiClient.getRepositoryAnalysis(repoId!);
    },
    enabled: !!repoId,
    refetchInterval: (query) => {
      // Poll while pending or analyzing
      const status = query?.state?.data?.status;
      console.log("📊 Analysis polling check - status:", status);
      
      if (status === "pending" || status === "analyzing") {
        console.log("🔄 Polling analysis data - status:", status);
        return 4000; // 4 seconds for analysis data
      }
      
      console.log("ℹ️ Analysis polling stopped for status:", status);
      return false;
    },
  });
};
