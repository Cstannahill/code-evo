// src/api/client.ts - Enhanced with model selection and analytics
interface CreateRepositoryRequest {
  url: string;
  branch?: string;
  model_id?: string; // Add model selection support
}

interface MultiModelAnalysisRequest {
  models: string[];
  code: string;
  language?: string;
  repository_id?: string;
}

// Enhanced API client with model selection
export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = "http://localhost:8080") {
    this.baseUrl = baseUrl;
  }

  // Existing methods...
  async checkHealth() {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  async getAnalysisStatus() {
    const response = await fetch(`${this.baseUrl}/api/analysis/status`);
    return response.json();
  }

  // Enhanced repository creation with model selection
  async createRepository(data: CreateRepositoryRequest) {
    // Track analytics
    this.trackModelSelection(data.model_id);

    const response = await fetch(`${this.baseUrl}/api/repositories`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to create repository: ${response.statusText}`);
    }

    const result = await response.json();

    // Track successful analysis start
    this.trackRepositoryAnalysis(data.model_id || "default", data.url);

    return result;
  }

  // Get available AI models
  async getAvailableModels() {
    const response = await fetch(
      `${this.baseUrl}/api/multi-model/models/available`
    );
    if (!response.ok) {
      throw new Error("Failed to fetch available models");
    }
    return response.json();
  }

  // Multi-model analysis endpoints
  async compareModels(data: MultiModelAnalysisRequest) {
    const response = await fetch(
      `${this.baseUrl}/api/multi-model-v2/analyze/compare-enhanced`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Multi-model analysis failed: ${response.statusText}`);
    }

    const result = await response.json();

    // Track multi-model comparison
    this.trackMultiModelComparison(data.models);

    return result;
  }

  async getComparisonResults(comparisonId: string) {
    const response = await fetch(
      `${this.baseUrl}/api/multi-model-v2/comparison/${comparisonId}`
    );
    if (!response.ok) {
      throw new Error("Failed to fetch comparison results");
    }
    return response.json();
  }

  // Analytics tracking methods
  private trackModelSelection(modelId?: string) {
    if (typeof gtag !== "undefined" && modelId) {
      gtag("event", "model_selected", {
        model_name: modelId,
        analysis_type: "single",
      });
    }
  }

  private trackRepositoryAnalysis(modelId: string, repoUrl: string) {
    if (typeof gtag !== "undefined") {
      gtag("event", "repository_analysis_started", {
        model_name: modelId,
        repository_domain: new URL(repoUrl).hostname,
      });
    }
  }

  private trackMultiModelComparison(models: string[]) {
    if (typeof gtag !== "undefined") {
      gtag("event", "multi_model_comparison", {
        models: models.join(","),
        model_count: models.length,
      });
    }
  }

  // Existing methods...
  async getRepositories() {
    const response = await fetch(`${this.baseUrl}/api/repositories`);
    return response.json();
  }

  async getRepository(id: string) {
    const response = await fetch(`${this.baseUrl}/api/repositories/${id}`);
    return response.json();
  }

  async getRepositoryAnalysis(id: string) {
    const response = await fetch(
      `${this.baseUrl}/api/repositories/${id}/analysis`
    );
    return response.json();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Type declarations for gtag (add to src/types/global.d.ts)
declare global {
  function gtag(command: string, targetId: string, config?: any): void;
  function gtag(command: string, action: string, parameters?: any): void;
}
