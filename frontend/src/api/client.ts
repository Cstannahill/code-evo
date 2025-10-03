// src/api/client.ts - Enhanced with model selection and analytics
import { getApiBaseUrl } from "../config/environment";
import type { ModelAvailabilityResponse } from "../types";

interface CreateRepositoryRequest {
  url: string;
  branch?: string;
  model_id?: string; // Add model selection support
}

// Enhanced API client with model selection
export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || getApiBaseUrl();
  }

  // Helper method to get auth headers
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem("auth_token");
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  }

  // Helper method for authenticated requests
  private async authenticatedFetch(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const headers = this.getAuthHeaders();

    // Merge with any existing headers
    const mergedHeaders = {
      ...headers,
      ...options.headers,
    };

    return fetch(url, {
      ...options,
      headers: mergedHeaders,
    });
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

    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/repositories`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to create repository: ${response.statusText}`);
    }

    const result = await response.json();

    // Track successful analysis start
    this.trackRepositoryAnalysis(data.model_id || "default", data.url);

    return result;
  }

  // Get available AI models
  async getAvailableModels(): Promise<ModelAvailabilityResponse> {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/analysis/models/available`
    );
    if (!response.ok) {
      throw new Error("Failed to fetch available models");
    }

    const payload = (await response.json()) as ModelAvailabilityResponse;
    return payload;
  }

  // Multi-model analysis endpoints
  async compareModels(data: {
    models: string[];
    code: string;
    language?: string;
  }) {
    const response = await fetch(
      `${this.baseUrl}/api/multi-model/analyze/compare`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Comparison failed: ${response.statusText}`);
    }

    return response.json();
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

  // Existing methods...
  async getRepositories() {
    const response = await fetch(`${this.baseUrl}/api/repositories`);
    return response.json();
  }

  async getGlobalRepositories(
    params: {
      limit?: number;
      offset?: number;
      tag?: string;
      language?: string;
    } = {}
  ): Promise<unknown> {
    const { limit = 50, offset = 0, tag, language } = params;
    const searchParams = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    if (tag) {
      searchParams.append("tag", tag);
    }

    if (language) {
      searchParams.append("language", language);
    }

    const response = await fetch(
      `${this.baseUrl}/api/repositories/global?${searchParams.toString()}`
    );

    if (!response.ok) {
      throw new Error(
        `Failed to fetch global repositories: ${response.statusText}`
      );
    }

    return response.json();
  }

  async getUserRepositories() {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/repositories/user/my-repositories`
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch user repositories: ${response.statusText}`
      );
    }
    return response.json();
  }

  async getUserRelevantRepositories(limit: number = 20) {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/repositories/user/relevant?limit=${limit}`
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch user relevant repositories: ${response.statusText}`
      );
    }
    return response.json();
  }

  async addRepositoryToUser(data: CreateRepositoryRequest) {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/repositories/user/add-repository`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to add repository to user: ${response.statusText}`
      );
    }

    return response.json();
  }

  async removeRepositoryFromUser(repoId: string) {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/repositories/user/repositories/${repoId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to remove repository from user: ${response.statusText}`
      );
    }

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
    if (!response.ok) {
      throw new Error(
        `Failed to fetch repository analysis: ${response.statusText}`
      );
    }
    return response.json();
  }

  async getRepositoryInsights(repositoryId: string): Promise<unknown> {
    const response = await fetch(
      `${this.baseUrl}/api/analysis/insights/${encodeURIComponent(
        repositoryId
      )}`
    );

    if (!response.ok) {
      throw new Error(
        `Failed to fetch repository insights: ${response.statusText}`
      );
    }

    return response.json();
  }

  // Get enhanced analysis results with all new analysis types
  async getEnhancedRepositoryAnalysis(id: string) {
    const response = await fetch(
      `${this.baseUrl}/api/repositories/${id}/analysis/enhanced`
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch enhanced analysis: ${response.statusText}`
      );
    }
    return response.json();
  }

  // List available analyses grouped by model for a repository
  async getRepositoryModels(id: string) {
    const response = await fetch(
      `${this.baseUrl}/api/repositories/${id}/analyses/models`
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch repository models: ${response.statusText}`
      );
    }
    return response.json();
  }

  // Fetch latest analyses for a repository filtered by model identifier
  async getRepositoryAnalysisByModel(id: string, model: string) {
    const response = await fetch(
      `${
        this.baseUrl
      }/api/repositories/${id}/analysis/by-model?model=${encodeURIComponent(
        model
      )}`
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch repository analysis by model: ${response.statusText}`
      );
    }
    return response.json();
  }

  // Get security analysis results
  async getSecurityAnalysis(id: string) {
    const response = await fetch(
      `${this.baseUrl}/api/repositories/${id}/security`
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch security analysis: ${response.statusText}`
      );
    }
    return response.json();
  }

  // Get performance analysis results
  async getPerformanceAnalysis(id: string) {
    const response = await fetch(
      `${this.baseUrl}/api/repositories/${id}/performance`
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch performance analysis: ${response.statusText}`
      );
    }
    return response.json();
  }

  // Get architectural analysis results
  async getArchitecturalAnalysis(id: string) {
    const response = await fetch(
      `${this.baseUrl}/api/repositories/${id}/architecture`
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch architectural analysis: ${response.statusText}`
      );
    }
    return response.json();
  }

  async getRepositoryPatterns(id: string, includeOccurrences = true) {
    const response = await fetch(
      `${this.baseUrl}/api/repositories/${id}/patterns?include_occurrences=${includeOccurrences}`
    );
    return response.json();
  }

  // Authentication methods
  async login(credentials: { username: string; password: string }) {
    const response = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      throw new Error(`Login failed: ${response.statusText}`);
    }

    return response.json();
  }

  async register(userData: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }) {
    const response = await fetch(`${this.baseUrl}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      throw new Error(`Registration failed: ${response.statusText}`);
    }

    return response.json();
  }

  async createGuestSession() {
    const response = await fetch(`${this.baseUrl}/api/auth/guest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Guest session creation failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getCurrentUser() {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/auth/me`
    );
    if (!response.ok) {
      throw new Error(`Failed to get current user: ${response.statusText}`);
    }
    return response.json();
  }

  async getUserApiKeys() {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/auth/api-keys`
    );
    if (!response.ok) {
      throw new Error(`Failed to get API keys: ${response.statusText}`);
    }
    return response.json();
  }

  async createApiKey(apiKeyData: {
    provider: string;
    key_name?: string;
    api_key: string;
  }) {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/auth/api-keys`,
      {
        method: "POST",
        body: JSON.stringify(apiKeyData),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to create API key: ${response.statusText}`);
    }

    return response.json();
  }

  async deleteApiKey(keyId: string) {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/auth/api-keys/${keyId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to delete API key: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Type declarations for gtag (add to src/types/global.d.ts)
declare global {
  function gtag(
    command: string,
    targetId: string,
    config?: Record<string, unknown>
  ): void;
  function gtag(
    command: string,
    action: string,
    parameters?: Record<string, unknown>
  ): void;
}
