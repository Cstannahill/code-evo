import type { AIModel } from "./model";

const defaultModels: AIModel[] = [
  {
    id: "codellama-7b-001",
    name: "codellama:7b",
    display_name: "CodeLlama 7B",
    provider: "Ollama (Local)",
    model_type: "code_analysis",
    context_window: 16384,
    cost_per_1k_tokens: 0.0,
    strengths: ["Fast inference", "Good for basic patterns", "Privacy-focused"],
    is_available: true,
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
  {
    id: "devstral-001",
    name: "devstral",
    display_name: "Devstral",
    provider: "Ollama (Local)",
    model_type: "code_analysis",
    context_window: 128000,
    cost_per_1k_tokens: 0.0,
    strengths: [
      "Better reasoning",
      "Complex pattern detection",
      "Architectural insights",
    ],
    is_available: false, // Will be set to true when detected
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
  {
    id: "gemma3n-001",
    name: "gemma3n",
    display_name: "Gemma 3n",
    provider: "Ollama (Local)",
    model_type: "code_analysis",
    context_window: 32000,
    cost_per_1k_tokens: 0.0,
    strengths: ["Google's code model", "Good performance", "Open source"],
    is_available: false, // Will be set to true when detected
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
  {
    id: "gpt-4-001",
    name: "gpt-4",
    display_name: "GPT-4",
    provider: "OpenAI",
    model_type: "general",
    context_window: 128000,
    cost_per_1k_tokens: 0.03, // Assuming cost is per 1k input tokens or a blended rate
    strengths: [
      "Exceptional reasoning",
      "Detailed explanations",
      "Latest patterns",
    ],
    is_available: false, // Will be set based on API key
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
  {
    id: "claude-3.7-sonnet-001",
    name: "claude-3.7-sonnet", // Example name, adjust if different
    display_name: "Claude 3.7 Sonnet",
    provider: "Anthropic",
    model_type: "general",
    context_window: 200000,
    cost_per_1k_tokens: 0.015, // Example cost, $0.003/1K input, $0.015/1K output for Sonnet
    strengths: ["Code quality focus", "Security analysis", "Best practices"],
    is_available: false, // Will be set based on API key
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
];
export { defaultModels };
export type { AIModel } from "./model";
