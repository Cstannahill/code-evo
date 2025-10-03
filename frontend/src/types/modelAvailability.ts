/**
 * Model availability response contracts shared between API client and UI.
 * These interfaces describe the FastAPI `/api/analysis/models/available` payload.
 */

/**
 * Describes a single model that can be surfaced in the selection UI.
 */
export interface ModelAvailabilityInfo {
  /** Model identifier such as `codellama:7b`. */
  name: string;
  /** Human-friendly name to display in the UI. */
  display_name: string;
  /** Provider identifier e.g. `ollama` or `openai`. */
  provider: string;
  /** Maximum context window supported by the model. */
  context_window: number;
  /** Listed cost per 1K tokens in USD (0 for free/local models). */
  cost_per_1k_tokens: number;
  /** Descriptive strengths communicated to the user. */
  strengths: string[];
  /** Whether the backend currently marks this model as available. */
  available: boolean;
  /** Optional cost tier classification supplied by the backend. */
  cost_tier?: string;
  /** Indicates whether the provider labels the model as free. */
  is_free?: boolean;
  /** Optional local size information in gigabytes (Ollama). */
  size_gb?: number;
  /** Indicates if this model requires an API key to use (for display purposes). */
  requires_api_key?: boolean;
  /** Indicates if this model has temperature locked to default (GPT-5 series). */
  temperature_locked?: boolean;
}

/**
 * Mapping of model identifiers to their availability metadata.
 */
export type ModelAvailabilityMap = Record<string, ModelAvailabilityInfo>;

/**
 * Payload returned by `/api/analysis/models/available`.
 */
export interface ModelAvailabilityResponse {
  /** Dictionary of available model details keyed by model id. */
  available_models: ModelAvailabilityMap;
  /** Total count for quick summary display. */
  total_count: number;
  /** Indicates whether the backend can reach a local Ollama service. */
  ollama_available: boolean;
  /** Indicates whether OpenAI models are currently unlockable. */
  openai_available: boolean;
  /** Indicates whether Anthropic models are currently unlockable. */
  anthropic_available?: boolean;
  /** Timestamp associated with the AI service status snapshot. */
  timestamp: string;
  /** Optional error message when availability resolution fails. */
  error?: string;
}
