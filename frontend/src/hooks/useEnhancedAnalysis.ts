import type { UseQueryResult } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { EnhancedRepositoryAnalysisResponse } from "../types/api";

export const useEnhancedAnalysis = (
  repoId: string | null
): UseQueryResult<EnhancedRepositoryAnalysisResponse, Error> => {
  return useQuery<EnhancedRepositoryAnalysisResponse, Error>({
    queryKey: ["enhancedRepositoryAnalysis", repoId],
    queryFn: () => apiClient.getEnhancedRepositoryAnalysis(repoId!),
    enabled: !!repoId,
    retry: (failureCount, error) => {
      // Only retry on network errors, not on 404/403 (endpoint might not exist)
      if (error?.message?.includes('404') || error?.message?.includes('403')) {
        return false;
      }
      return failureCount < 2;
    },
    refetchInterval: (query) => {
      // Poll while analyzing
      if (query?.state?.data?.status === "analyzing") {
        return 5000; // 5 seconds
      }
      return false;
    },
  });
};