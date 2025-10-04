/**
 * Tunnel-related type definitions for secure Ollama connections
 */

/**
 * Tunnel connection status
 */
export type TunnelStatus =
  | "active"
  | "connected"
  | "connecting"
  | "disconnected"
  | "error";

/**
 * Tunnel provider type
 */
export type TunnelProvider = "cloudflare" | "ngrok" | "custom";

/**
 * Active tunnel connection information
 */
export interface TunnelConnection {
  /** User ID who owns this tunnel */
  user_id: string;

  /** Public tunnel URL (e.g., https://abc123.trycloudflare.com) */
  tunnel_url: string;

  /** Current connection status */
  status: TunnelStatus;

  /** Tunnel provider type */
  provider: TunnelProvider;

  /** When the tunnel was registered */
  created_at: string;

  /** When the tunnel was last verified as working */
  last_verified_at: string | null;

  /** Current authentication token (24-hour expiry) */
  token: string;

  /** Token expiration timestamp */
  token_expires_at: string;

  /** Total number of requests made through this tunnel */
  request_count: number;
}

/**
 * Tunnel request log entry (for transparency)
 */
export interface TunnelRequest {
  /** Unique request ID */
  id: string;

  /** Timestamp of the request */
  timestamp: string;

  /** HTTP method */
  method: string;

  /** Request path */
  path: string;

  /** Response status code */
  status_code: number;

  /** Request duration in milliseconds */
  duration_ms: number;

  /** Error message if request failed */
  error?: string;
}

/**
 * Tunnel registration request payload
 */
export interface TunnelRegistrationRequest {
  /** Public tunnel URL to register */
  tunnel_url: string;
}

/**
 * Tunnel health check response
 */
export interface TunnelHealthCheck {
  /** Whether the tunnel endpoint is reachable */
  healthy: boolean;

  /** Response time in milliseconds */
  response_time_ms: number;

  /** Error message if unhealthy */
  error?: string;
}

/**
 * Tunnel setup step (for wizard)
 */
export interface TunnelSetupStep {
  /** Step number */
  step: number;

  /** Step title */
  title: string;

  /** Detailed instructions */
  instructions: string;

  /** Command to copy (if applicable) */
  command?: string;

  /** Whether this step is complete */
  completed: boolean;
}

/**
 * Tunnel setup wizard state
 */
export interface TunnelSetupState {
  /** Selected provider */
  provider: TunnelProvider | null;

  /** Current step number */
  currentStep: number;

  /** Setup steps for selected provider */
  steps: TunnelSetupStep[];

  /** Generated tunnel URL */
  tunnelUrl: string | null;

  /** Whether setup is complete */
  complete: boolean;
}
