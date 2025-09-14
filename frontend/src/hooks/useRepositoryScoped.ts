import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";

interface Repository {
  id: string;
  name: string;
  status?: string;
  url?: string;
  [key: string]: unknown;
}

/**
 * Hook to fetch user's repositories
 */
export const useUserRepositories = () => {
  return useQuery({
    queryKey: ["repositories", "user"],
    queryFn: async () => {
      try {
        return await apiClient.getUserRepositories();
      } catch {
        // Fallback to all repositories if user endpoint fails (not authenticated)
        console.log(
          "User repositories endpoint failed, falling back to all repositories"
        );
        const allRepos = await apiClient.getRepositories();
        return allRepos.repositories || allRepos;
      }
    },
    // Refetch when window focuses to get latest status
    refetchOnWindowFocus: true,
    staleTime: 5000, // 5 seconds
    refetchInterval: (query) => {
      // Check if any repository is pending or analyzing
      const repositories = query?.state?.data;
      if (repositories && Array.isArray(repositories)) {
        const hasActiveAnalysis = repositories.some(
          (repo: Repository) =>
            repo.status === "pending" || repo.status === "analyzing"
        );

        if (hasActiveAnalysis) {
          console.log(
            "🔄 Polling user repositories - active analysis detected"
          );
          return 5000; // Poll every 5 seconds if any repo is being analyzed
        }
      }
      return false; // Stop polling if no active analysis
    },
  });
};

/**
 * Hook to fetch repositories relevant to the user
 */
export const useUserRelevantRepositories = (limit: number = 20) => {
  return useQuery({
    queryKey: ["repositories", "user-relevant", limit],
    queryFn: async () => {
      try {
        return await apiClient.getUserRelevantRepositories(limit);
      } catch (error) {
        console.log("User relevant repositories endpoint failed:", error);
        // Return empty array if endpoint fails
        return [];
      }
    },
    // Less frequent polling for recommendations
    refetchOnWindowFocus: false,
    staleTime: 30000, // 30 seconds
    refetchInterval: false, // No automatic polling for recommendations
  });
};

/**
 * Hook to fetch global repositories
 */
export const useGlobalRepositories = () => {
  return useQuery({
    queryKey: ["repositories", "global"],
    queryFn: async () => {
      try {
        return await apiClient.getGlobalRepositories();
      } catch {
        // Fallback to all repositories if global endpoint fails
        console.log(
          "Global repositories endpoint failed, falling back to all repositories"
        );
        const allRepos = await apiClient.getRepositories();
        return allRepos.repositories || allRepos;
      }
    },
    // Refetch when window focuses to get latest status
    refetchOnWindowFocus: true,
    staleTime: 10000, // 10 seconds - longer for global repos
    refetchInterval: (query) => {
      // Check if any repository is pending or analyzing
      const repositories = query?.state?.data;
      if (repositories && Array.isArray(repositories)) {
        const hasActiveAnalysis = repositories.some(
          (repo: Repository) =>
            repo.status === "pending" || repo.status === "analyzing"
        );

        if (hasActiveAnalysis) {
          console.log(
            "🔄 Polling global repositories - active analysis detected"
          );
          return 10000; // Poll every 10 seconds for global repos (less frequent)
        }
      }
      return false; // Stop polling if no active analysis
    },
  });
};

/**
 * Hook to fetch all repositories (fallback for compatibility)
 */
export const useAllRepositories = () => {
  return useQuery({
    queryKey: ["repositories", "all"],
    queryFn: () => apiClient.getRepositories(),
    refetchOnWindowFocus: true,
    staleTime: 5000,
    refetchInterval: (query) => {
      const repositoriesData = query?.state?.data;
      const repositories = repositoriesData?.repositories || repositoriesData;

      if (repositories && Array.isArray(repositories)) {
        const hasActiveAnalysis = repositories.some(
          (repo: Repository) =>
            repo.status === "pending" || repo.status === "analyzing"
        );

        if (hasActiveAnalysis) {
          console.log("🔄 Polling all repositories - active analysis detected");
          return 5000;
        }
      }
      return false;
    },
  });
};
