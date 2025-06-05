// src/hooks/useRepositoryAnalysis.ts

import type { UseQueryResult } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { RepositoryAnalysis } from "../types/api";

export const useRepositoryAnalysis = (
  repoId: string | null
): UseQueryResult<RepositoryAnalysis, Error> => {
  return useQuery<RepositoryAnalysis, Error>({
    queryKey: ["repositoryAnalysis", repoId],
    queryFn: () => apiClient.getRepositoryAnalysis(repoId!),
    enabled: !!repoId,
    refetchInterval: (query) => {
      // Poll while analyzing
      if (query?.state?.data?.status === "analyzing") {
        return 5000; // 5 seconds
      }
      return false;
    },
  });
};
