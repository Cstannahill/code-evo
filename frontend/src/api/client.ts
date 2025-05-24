import type { AxiosInstance } from "axios";
import axios from "axios";
import axiosRetry from "axios-retry";
import type {
  Repository,
  RepositoryAnalysis,
  CodeAnalysisResult,
  Insight,
} from "../types/api";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080",
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add retry logic
    axiosRetry(this.client, {
      retries: 3,
      retryDelay: axiosRetry.exponentialDelay,
      retryCondition: (error) => {
        return (
          axiosRetry.isNetworkOrIdempotentRequestError(error) ||
          error.response?.status === 429
        );
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle auth error
        }
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async checkHealth() {
    const response = await this.client.get("/health");
    // console.log("Health check response:", response);
    return response.data;
  }

  // Repositories
  async createRepository(data: { url: string; branch?: string }) {
    const response = await this.client.post<Repository>(
      "/api/repositories",
      data
    );
    return response.data;
  }

  async getRepositories() {
    const response = await this.client.get<Repository[]>("/api/repositories");
    return response.data;
  }

  async getRepository(id: string) {
    const response = await this.client.get<Repository>(
      `/api/repositories/${id}`
    );
    return response.data;
  }

  async getRepositoryAnalysis(id: string) {
    const response = await this.client.get<RepositoryAnalysis>(
      `/api/repositories/${id}/analysis`
    );
    return response.data;
  }

  // Analysis
  async getInsights(repoId: string) {
    const response = await this.client.get<{ insights: Insight[] }>(
      `/api/analysis/insights/${repoId}`
    );
    return response.data;
  }

  async analyzeCode(code: string, language: string = "javascript") {
    const response = await this.client.post<CodeAnalysisResult>(
      "/api/analysis/code",
      {
        code,
        language,
      }
    );
    return response.data;
  }

  async getAnalysisStatus() {
    const response = await this.client.get("/api/analysis/status");
    return response.data;
  }
}

export const apiClient = new ApiClient();
