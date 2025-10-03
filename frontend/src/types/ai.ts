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
  // GPT-5 Series (Updated October 2025)
  {
    id: "gpt-5-001",
    name: "gpt-5",
    display_name: "GPT-5",
    provider: "OpenAI",
    model_type: "general",
    context_window: 400000,
    cost_per_1k_tokens: 0.00125,
    strengths: [
      "Advanced reasoning",
      "Code analysis",
      "Vision",
      "Agentic workflows",
    ],
    is_available: false, // Will be set based on API key
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
  {
    id: "gpt-5-mini-001",
    name: "gpt-5-mini",
    display_name: "GPT-5 Mini",
    provider: "OpenAI",
    model_type: "general",
    context_window: 400000,
    cost_per_1k_tokens: 0.00025,
    strengths: ["Code", "Fast", "Efficient", "Cost-effective"],
    is_available: false, // Will be set based on API key
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
  {
    id: "gpt-5-nano-001",
    name: "gpt-5-nano",
    display_name: "GPT-5 Nano",
    provider: "OpenAI",
    model_type: "general",
    context_window: 400000,
    cost_per_1k_tokens: 0.00005,
    strengths: ["Fast", "Lightweight", "Classification", "Summarization"],
    is_available: false, // Will be set based on API key
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
  // Claude 4 Series (Updated October 2025)
  {
    id: "claude-sonnet-4.5-001",
    name: "claude-sonnet-4.5",
    display_name: "Claude Sonnet 4.5",
    provider: "Anthropic",
    model_type: "general",
    context_window: 200000,
    cost_per_1k_tokens: 0.003,
    strengths: [
      "Code quality",
      "Security analysis",
      "Best practices",
      "Long context",
    ],
    is_available: false, // Will be set based on API key
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
  {
    id: "claude-opus-4-001",
    name: "claude-opus-4",
    display_name: "Claude Opus 4",
    provider: "Anthropic",
    model_type: "general",
    context_window: 200000,
    cost_per_1k_tokens: 0.015,
    strengths: ["Advanced reasoning", "Complex tasks", "Code", "Research"],
    is_available: false, // Will be set based on API key
    created_at: new Date().toISOString(),
    usage_count: 0,
  },
];
export { defaultModels };
export type { AIModel } from "./model";
