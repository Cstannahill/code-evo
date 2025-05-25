import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import toast from "react-hot-toast";

export const useCreateRepository = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { url: string; branch?: string }) =>
      apiClient.createRepository(data),
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
      // Poll while analyzing
      if (query.data?.status === "analyzing") {
        return 5000; // 5 seconds
      }
      return false;
    },
  });
};

export const useRepositories = () => {
  return useQuery({
    queryKey: ["repositories"],
    queryFn: () => apiClient.getRepositories(),
  });
};
