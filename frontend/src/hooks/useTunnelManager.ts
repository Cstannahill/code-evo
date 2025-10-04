import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";
import type { TunnelConnection, TunnelRequest } from "../types/tunnel";

// Minimal shape for validation details returned by the backend
export interface TunnelValidationResult {
  status_code?: number;
  suggestion?: string;
  response_snippet?: string;
  headers?: Record<string, string> | null;
  message?: string;
}

export interface UseTunnelManagerOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export interface TunnelManager {
  connection: TunnelConnection | null;
  isLoading: boolean;
  error: string | null;
  validationResult: TunnelValidationResult | null;
  recentRequests: TunnelRequest[];
  isActive: boolean;
  statusText: string;
  statusColor: "green" | "yellow" | "red" | "gray";
  registerTunnel: (
    tunnelUrl: string,
    tunnelMethod: "cloudflare" | "ngrok"
  ) => Promise<boolean>;
  disableTunnel: () => Promise<boolean>;
  refreshStatus: () => Promise<void>;
  refreshRecentRequests: () => Promise<void>;
  clearError: () => void;
}

export function useTunnelManager(
  options: UseTunnelManagerOptions = {}
): TunnelManager {
  const { autoRefresh = true, refreshInterval = 30000 } = options;

  const [connection, setConnection] = useState<TunnelConnection | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [validationResult, setValidationResult] =
    useState<TunnelValidationResult | null>(null);
  const [recentRequests, setRecentRequests] = useState<TunnelRequest[]>([]);

  // Fetch tunnel status
  const refreshStatus = useCallback(async () => {
    try {
      const data = await apiClient.getTunnelStatus();
      setConnection(data);
      setError(null);
    } catch (err: unknown) {
      // Don't set error for "no active connection" - it's a valid state
      if (err instanceof Error && !err.message.includes("No active tunnel")) {
        setError(err.message);
      } else {
        setConnection(null);
      }
    }
  }, []);

  // Fetch recent requests
  const refreshRecentRequests = useCallback(async () => {
    try {
      const data = await apiClient.getTunnelRecentRequests(50);
      setRecentRequests(data);
    } catch (err: unknown) {
      // Silently fail - not critical
      console.warn("Failed to fetch recent tunnel requests:", err);
    }
  }, []);

  // Register a new tunnel
  const registerTunnel = useCallback(
    async (
      tunnelUrl: string,
      tunnelMethod: "cloudflare" | "ngrok"
    ): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await apiClient.registerTunnel(tunnelUrl, tunnelMethod);
        // API returns { success: true, message, tunnel: { ... } }
        const tunnelData = data?.tunnel ?? null;
        setConnection(tunnelData);
        // clear any previous validation info
        setValidationResult(null);
        // Notify other parts of the app that a tunnel was connected
        try {
          window.dispatchEvent(
            new CustomEvent("tunnel:connected", { detail: tunnelData })
          );
        } catch {
          // ignore if CustomEvent not supported
        }
        await refreshRecentRequests(); // Refresh history after registration
        return true;
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to register tunnel";
        setError(message);
        // If the thrown error had structured validation info attached, capture it for the UI
        try {
          const maybe = err as unknown as {
            validation?: TunnelValidationResult;
          };
          const val = maybe?.validation ?? null;
          if (val) setValidationResult(val);
        } catch {
          // ignore
        }
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [refreshRecentRequests]
  );

  // Disable the active tunnel
  const disableTunnel = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      await apiClient.disableTunnel();
      setConnection(null);
      setRecentRequests([]);
      return true;
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to disable tunnel";
      setError(message);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Clear error state
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-refresh status
  useEffect(() => {
    if (!autoRefresh) return;

    // Initial fetch
    refreshStatus();
    refreshRecentRequests();

    // Set up interval
    const intervalId = setInterval(() => {
      refreshStatus();
      refreshRecentRequests();
    }, refreshInterval);

    return () => clearInterval(intervalId);
  }, [autoRefresh, refreshInterval, refreshStatus, refreshRecentRequests]);

  // Computed values
  const isActive = connection?.status === "connected";

  const statusText = connection
    ? connection.status === "active" || connection.status === "connected"
      ? "Connected"
      : connection.status === "connecting"
      ? "Connecting..."
      : connection.status === "error"
      ? "Error"
      : "Disabled"
    : "Not Connected";

  const statusColor: "green" | "yellow" | "red" | "gray" = connection
    ? connection.status === "active" || connection.status === "connected"
      ? "green"
      : connection.status === "connecting"
      ? "yellow"
      : connection.status === "error"
      ? "red"
      : "gray"
    : "gray";

  return {
    // State
    connection,
    isLoading,
    error,
    validationResult,
    recentRequests,

    // Actions
    registerTunnel,
    disableTunnel,
    refreshStatus,
    refreshRecentRequests,
    clearError,

    // Computed
    isActive,
    statusText,
    statusColor,
  };
}
