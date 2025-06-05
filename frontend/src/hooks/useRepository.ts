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
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
      toast.success(`Repository ${data.name} created!`);
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
      // Only poll while analyzing - stop when completed, failed, or pending
      const status = query?.state?.data?.status;
      console.log("🔍 Polling check - Repository status:", status);

      if (status === "analyzing") {
        console.log("⏰ Continuing to poll (analyzing)");
        return 3000; // Poll every 3 seconds
      }

      console.log("✋ Stopping poll - status:", status);
      return false; // Stop polling
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
    staleTime: 10000, // 10 seconds
  });
};
