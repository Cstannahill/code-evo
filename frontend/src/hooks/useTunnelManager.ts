import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";
import type { TunnelConnection, TunnelRequest } from "../types/tunnel";

export interface UseTunnelManagerOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export interface UseTunnelManagerResult {
  // State
  connection: TunnelConnection | null;
  isLoading: boolean;
  error: string | null;
  recentRequests: TunnelRequest[];

  // Actions
  registerTunnel: (tunnelUrl: string) => Promise<boolean>;
  disableTunnel: () => Promise<boolean>;
  refreshStatus: () => Promise<void>;
  refreshRecentRequests: () => Promise<void>;
  clearError: () => void;

  // Computed
  isActive: boolean;
  statusText: string;
  statusColor: "green" | "yellow" | "red" | "gray";
}

export function useTunnelManager(
  options: UseTunnelManagerOptions = {}
): UseTunnelManagerResult {
  const { autoRefresh = true, refreshInterval = 30000 } = options;

  const [connection, setConnection] = useState<TunnelConnection | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
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
    async (tunnelUrl: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await apiClient.registerTunnel(tunnelUrl);
        setConnection(data);
        await refreshRecentRequests(); // Refresh history after registration
        return true;
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to register tunnel";
        setError(message);
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
  const isActive = connection?.status === "active";

  const statusText = connection
    ? connection.status === "active"
      ? "Connected"
      : connection.status === "connecting"
      ? "Connecting..."
      : connection.status === "error"
      ? "Error"
      : "Disabled"
    : "Not Connected";

  const statusColor: "green" | "yellow" | "red" | "gray" = connection
    ? connection.status === "active"
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
