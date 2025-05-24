import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import toast from "react-hot-toast";
import { useTransformAnalysis } from "./useTransformAnalysis";
import type { RepositoryAnalysisResponse } from "../types/api";

export const useCreateRepository = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { url: string; branch?: string }) =>
      apiClient.createRepository(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
      toast.success(`Repository ${data.name} created!`);
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.detail || "Failed to create repository"
      );
    },
  });
};

export const useRepository = (id: string | null) => {
  return useQuery({
    queryKey: ["repository", id],
    queryFn: () => (id ? apiClient.getRepository(id) : null),
    enabled: !!id,
    refetchInterval: (data) => {
      // Poll while analyzing
      if (data?.status === "analyzing") {
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
export const useRepositoryAnalysis = (id: string | null) => {
  const analysisQuery = useQuery({
    queryKey: ["repository-analysis", id],
    queryFn: () => (id ? apiClient.getRepositoryAnalysis(id) : null),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const insightsQuery = useQuery({
    queryKey: ["repository-insights", id],
    queryFn: () => (id ? apiClient.getInsights(id) : null),
    enabled: !!id && !!analysisQuery.data,
  });

  // Transform the data
  const transformedData = useTransformAnalysis(
    analysisQuery.data
      ? ({
          ...analysisQuery.data,
          insights: insightsQuery.data || [],
          // Ensure patterns are properly formatted
          patterns: analysisQuery.data.patterns.map((pattern) => ({
            pattern_name: pattern.name || "",
            file_path: pattern.path || "",
            confidence_score: pattern.score || 0,
            detected_at: pattern.timestamp || "",
          })),
        } as unknown as RepositoryAnalysisResponse)
      : null
  );

  return {
    data: transformedData,
    isLoading: analysisQuery.isLoading || insightsQuery.isLoading,
    error: analysisQuery.error || insightsQuery.error,
  };
};
