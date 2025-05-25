import axios, { type AxiosInstance, type AxiosResponse } from "axios";
import type {
  Repository,
  RepositoryCreate,
  RepositoryAnalysis,
  CodeAnalysisResult,
  CodeAnalysisRequest,
  TimelineResponse,
  HealthResponse,
  AIServiceStatus,
  Insight,
} from "../types/api";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080",
      timeout: 60000, // 60 seconds for analysis operations
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        const startTime = Date.now();
        const requestId = Math.random().toString(36).substring(7);

        config.metadata = {
          startTime,
          requestId,
        };

        console.log(`🚀 API Request [${requestId}]:`, {
          method: config.method?.toUpperCase(),
          url: config.url,
          data: config.data,
        });

        return config;
      },
      (error) => {
        console.error("❌ API Request Error:", error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for logging
    this.client.interceptors.response.use(
      (response) => {
        const duration =
          Date.now() - (response.config.metadata?.startTime || 0);
        const requestId = response.config.metadata?.requestId;

        console.log(`✅ API Response [${requestId}]:`, {
          status: response.status,
          duration: `${duration}ms`,
          data: response.data,
        });

        return response;
      },
      (error) => {
        const duration = Date.now() - (error.config?.metadata?.startTime || 0);
        const requestId = error.config?.metadata?.requestId;

        console.error(`❌ API Error [${requestId}]:`, {
          status: error.response?.status,
          duration: `${duration}ms`,
          message: error.message,
          data: error.response?.data,
        });

        return Promise.reject(error);
      }
    );
  }

  // Health check
  async checkHealth(): Promise<HealthResponse> {
    const response: AxiosResponse<HealthResponse> = await this.client.get(
      "/health"
    );
    return response.data;
  }

  // Connection test
  async testConnection(): Promise<unknown> {
    const response = await this.client.get("/api/connection-test");
    return response.data;
  }

  // AI service status
  async getAnalysisStatus(): Promise<AIServiceStatus> {
    const response: AxiosResponse<AIServiceStatus> = await this.client.get(
      "/api/analysis/status"
    );
    return response.data;
  }

  // Repository operations
  async getRepositories(): Promise<Repository[]> {
    const response: AxiosResponse<Repository[]> = await this.client.get(
      "/api/repositories/"
    );
    return response.data;
  }

  async getRepository(id: string): Promise<Repository> {
    const response: AxiosResponse<Repository> = await this.client.get(
      `/api/repositories/${id}`
    );
    return response.data;
  }

  async createRepository(data: RepositoryCreate): Promise<Repository> {
    const response: AxiosResponse<Repository> = await this.client.post(
      "/api/repositories/",
      data
    );
    return response.data;
  }

  // Analysis operations
  async getRepositoryAnalysis(repoId: string): Promise<RepositoryAnalysis> {
    const response: AxiosResponse<RepositoryAnalysis> = await this.client.get(
      `/api/repositories/${repoId}/analysis`
    );
    return response.data;
  }

  async getRepositoryTimeline(repoId: string): Promise<TimelineResponse> {
    const response: AxiosResponse<TimelineResponse> = await this.client.get(
      `/api/repositories/${repoId}/timeline`
    );
    return response.data;
  }

  async getInsights(repoId: string): Promise<{ insights: Insight[] }> {
    const response: AxiosResponse<{ insights: Insight[] }> =
      await this.client.get(`/api/analysis/insights/${repoId}`);
    return response.data;
  }

  // Code analysis
  async analyzeCode(request: CodeAnalysisRequest): Promise<CodeAnalysisResult> {
    const response: AxiosResponse<CodeAnalysisResult> = await this.client.post(
      "/api/analysis/code",
      request
    );
    return response.data;
  }

  // Pattern operations
  async getAllPatterns(): Promise<never[]> {
    const response = await this.client.get("/api/analysis/patterns");
    return response.data;
  }

  async getPatternDetails(patternName: string): Promise<any> {
    const response = await this.client.get(
      `/api/analysis/patterns/${patternName}`
    );
    return response.data;
  }

  // Evolution analysis
  async analyzeEvolution(data: {
    old_code: string;
    new_code: string;
    context?: string;
  }): Promise<unknown> {
    const response = await this.client.post("/api/analysis/evolution", data);
    return response.data;
  }

  // Repository comparison
  async compareRepositories(
    repoId1: string,
    repoId2: string
  ): Promise<unknown> {
    const response = await this.client.get(
      `/api/analysis/compare/${repoId1}/${repoId2}`
    );
    return response.data;
  }
}

export const apiClient = new ApiClient();
