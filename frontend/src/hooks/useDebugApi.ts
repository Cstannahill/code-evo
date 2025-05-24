import { useEffect } from "react";
import { apiClient } from "../api/client";

export const useDebugApi = (repositoryId: string | null) => {
  useEffect(() => {
    if (!repositoryId) return;

    const debugApi = async () => {
      try {
        // Log raw API responses
        const analysis = await apiClient.getRepositoryAnalysis(repositoryId);
        console.log("🔍 Raw Analysis Response:", analysis);

        const insights = await apiClient.getInsights(repositoryId);
        console.log("🔍 Raw Insights Response:", insights);
      } catch (error) {
        console.error("Debug API Error:", error);
      }
    };

    debugApi();
  }, [repositoryId]);
};
