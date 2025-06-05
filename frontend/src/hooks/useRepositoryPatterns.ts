import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { apiClient } from "../api/client";

export const useRepositoryPatterns = (
  repoId: string | null
): UseQueryResult<any, Error> =>
  useQuery<any, Error>({
    queryKey: ["repositoryPatterns", repoId],
    queryFn: () => apiClient.getRepositoryPatterns(repoId!),
    enabled: !!repoId,
  });
