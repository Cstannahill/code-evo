import axios from "axios";
import axiosRetry from "axios-retry";
import type {
  Repository,
  RepositoryAnalysis,
  CodeAnalysisResult,
  Insight,
} from "../types/api";
import logger from "../lib/logger";

class ApiClient {
  private client: any; // Using any to bypass TypeScript axios typing issues
  private requestIdCounter = 0;

  constructor() {
    // Create axios instance with any type to avoid compilation issues
    this.client = (axios as any).create({
      baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080",
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add request interceptor for logging and correlation tracking
    this.client.interceptors.request.use(
      (config: any) => {
        const requestId = `req_${Date.now()}_${++this.requestIdCounter}`;
        config.metadata = {
          startTime: Date.now(),
          requestId,
        };

        // Add correlation ID to headers
        config.headers["X-Correlation-ID"] = requestId;

        // Log API request
        logger.info("API Request Started", {
          method: config.method?.toUpperCase() || "UNKNOWN",
          url: config.url || "unknown",
          requestId,
          component: "ApiClient",
        });

        return config;
      },
      (error: any) => {
        logger.error("API Request Setup Error", {
          phase: "request_setup",
          component: "ApiClient",
          error: error.message || "Unknown error",
        });
        return Promise.reject(error);
      }
    );

    // Add retry logic with logging
    axiosRetry(this.client, {
      retries: 3,
      retryDelay: axiosRetry.exponentialDelay,
      retryCondition: (error) => {
        const shouldRetry =
          axiosRetry.isNetworkOrIdempotentRequestError(error) ||
          error.response?.status === 429;

        if (shouldRetry) {
          logger.warn("API Request Retry Attempt", {
            method: error.config?.method?.toUpperCase(),
            url: error.config?.url,
            status: error.response?.status,
            attempt: error.config?.["axios-retry"]?.retryCount || 1,
            component: "ApiClient",
          });
        }

        return shouldRetry;
      },
    });

    // Response interceptor for logging and error handling
    this.client.interceptors.response.use(
      (response: any) => {
        const { startTime, requestId } = response.config.metadata || {};
        const duration = startTime ? Date.now() - startTime : undefined;

        // Log successful API response
        logger.info("API Response Received", {
          method: response.config.method?.toUpperCase() || "UNKNOWN",
          url: response.config.url || "unknown",
          statusCode: response.status,
          duration,
          requestId,
          responseSize: JSON.stringify(response.data).length,
          component: "ApiClient",
        });

        return response;
      },
      (error: any) => {
        const { startTime, requestId } = error.config?.metadata || {};
        const duration = startTime ? Date.now() - startTime : undefined;

        // Log API error
        logger.error("API Request Failed", {
          method: error.config?.method?.toUpperCase() || "UNKNOWN",
          url: error.config?.url || "unknown",
          statusCode: error.response?.status,
          duration,
          requestId,
          error: error.message,
          component: "ApiClient",
        });

        if (error.response?.status === 401) {
          logger.warn("Authentication error detected", {
            requestId,
            url: error.config?.url,
            component: "ApiClient",
          });
          // Handle auth error
        }
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async checkHealth() {
    const response = await this.client.get("/health");
    return response.data;
  }

  // Repositories
  async createRepository(data: { url: string; branch?: string }) {
    const response = await this.client.post("/api/repositories", data);
    return response.data as Repository;
  }

  async getRepositories() {
    const response = await this.client.get("/api/repositories");
    return response.data as Repository[];
  }

  async getRepository(id: string) {
    const response = await this.client.get(`/api/repositories/${id}`);
    return response.data as Repository;
  }

  async getRepositoryAnalysis(id: string) {
    const response = await this.client.get(`/api/repositories/${id}/analysis`);
    return response.data as RepositoryAnalysis;
  }

  // Analysis
  async getInsights(repoId: string) {
    const response = await this.client.get(`/api/analysis/insights/${repoId}`);
    return response.data as { insights: Insight[] };
  }

  async analyzeCode(code: string, language: string = "javascript") {
    const response = await this.client.post("/api/analysis/code", {
      code,
      language,
    });
    return response.data as CodeAnalysisResult;
  }

  async getAnalysisStatus() {
    const response = await this.client.get("/api/analysis/status");
    return response.data;
  }
}

export const apiClient = new ApiClient();
