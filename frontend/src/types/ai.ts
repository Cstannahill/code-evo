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
    id: "codellama-13b-001",
    name: "codellama:13b",
    display_name: "CodeLlama 13B",
    provider: "Ollama (Local)",
    model_type: "code_analysis",
    context_window: 16384,
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
    id: "claude-3-sonnet-001",
    name: "claude-3-sonnet", // Example name, adjust if different
    display_name: "Claude 3 Sonnet",
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
