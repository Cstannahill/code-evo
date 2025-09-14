export interface AIModel {
  id: string;
  name: string; // e.g., 'codellama:7b'
  display_name: string; // e.g., 'CodeLlama 7B'
  provider: string;
  model_type: "code_analysis" | "general" | string; // Allows specific known types plus any others
  context_window: number;
  cost_per_1k_tokens: number;
  strengths: string[];
  is_available: boolean;
  created_at: string; // ISO 8601 date string (e.g., "2023-10-26T10:00:00.000Z")
  usage_count: number;
  size_gb?: number; // Optional backend-provided size in GB for Ollama models
}
