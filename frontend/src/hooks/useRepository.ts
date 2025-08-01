import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import toast from "react-hot-toast";
import type { RepositoryCreateRequest } from "../types/api";

export const useCreateRepository = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (
      data: RepositoryCreateRequest // Updated type here
    ) => apiClient.createRepository(data),
    onSuccess: (data) => {
      // Invalidate repositories list to show the new repository
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
      // Also invalidate the specific repository query to ensure it starts polling
      queryClient.invalidateQueries({ queryKey: ["repository", data.id] });
      // Set initial data for the repository to avoid a loading state
      queryClient.setQueryData(["repository", data.id], data);
      toast.success(`Repository ${data.name} created and analysis started!`);
    },
    onError: (error: Error) => {
      const errorMessage =
        error instanceof Error && "response" in error
          ? (error as { response?: { data?: { detail?: string } } }).response
              ?.data?.detail
          : error.message;
      toast.error(errorMessage || "Failed to create repository");
    },
  });
};

export const useRepository = (id: string | null) => {
  return useQuery({
    queryKey: ["repository", id],
    queryFn: () => (id ? apiClient.getRepository(id) : null),
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll while pending or analyzing - stop when completed or failed
      const status = query?.state?.data?.status;
      console.log("🔍 Polling check - Repository status:", status);

      if (status === "pending") {
        console.log("⏰ Continuing to poll (pending - waiting to start)");
        return 2000; // Poll every 2 seconds for pending (faster since it should transition quickly)
      }

      if (status === "analyzing") {
        console.log("⏰ Continuing to poll (analyzing)");
        return 3000; // Poll every 3 seconds for analyzing
      }

      if (status === "completed") {
        console.log("✅ Analysis completed - stopping poll");
        return false; // Stop polling
      }

      if (status === "failed") {
        console.log("❌ Analysis failed - stopping poll");
        return false; // Stop polling
      }

      console.log("✋ Stopping poll - unknown status:", status);
      return false; // Stop polling for unknown states
    },
    // Also enable refetching when window focuses to catch any missed updates
    refetchOnWindowFocus: true,
    // Keep data for 30 seconds to avoid unnecessary refetches
    staleTime: 30000,
  });
};

export const useRepositories = () => {
  return useQuery({
    queryKey: ["repositories"],
    queryFn: () => apiClient.getRepositories(),
    // Refetch repositories list when window focuses to get latest status
    refetchOnWindowFocus: true,
    staleTime: 5000, // 5 seconds - shorter to catch status changes
    refetchInterval: (query) => {
      // Check if any repository is pending or analyzing
      const repositories = query?.state?.data;
      if (repositories && Array.isArray(repositories)) {
        const hasActiveAnalysis = repositories.some(
          (repo: any) =>
            repo.status === "pending" || repo.status === "analyzing"
        );

        if (hasActiveAnalysis) {
          console.log(
            "🔄 Polling repositories list - active analysis detected"
          );
          return 5000; // Poll every 5 seconds if any repo is being analyzed
        }
      }

      return false; // Stop polling if no active analysis
    },
  });
};
