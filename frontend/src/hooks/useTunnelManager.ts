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
      // API may return a wrapper { success: true, tunnel: { ... } }
      const conn = ((): TunnelConnection | null => {
        if (!data) return null;
        if (
          typeof data === "object" &&
          (data as Record<string, unknown>)["tunnel"]
        ) {
          const maybe = (data as Record<string, unknown>)["tunnel"];
          return (maybe as TunnelConnection) ?? null;
        }
        return (data as TunnelConnection) ?? null;
      })();
      // Normalize common field names so UI can rely on provider/request_count/tunnel_url
      const normalized = conn
        ? (() => {
            const record = conn as unknown as Record<string, unknown>;
            return {
              ...conn,
              provider:
                (record["provider"] as string) ??
                (record["tunnel_method"] as string) ??
                "custom",
              request_count:
                (record["request_count"] as number) ??
                (record["requests"] as number) ??
                0,
              tunnel_url:
                (record["tunnel_url"] as string) ??
                (record["tunnelUrl"] as string) ??
                (record["ollama_url"] as string) ??
                null,
            } as TunnelConnection;
          })()
        : null;

      setConnection(normalized as TunnelConnection | null);
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
      // API may return wrapper { success: true, requests: [...] }
      const reqs = ((): TunnelRequest[] => {
        if (!data) return [];
        if (
          typeof data === "object" &&
          (data as Record<string, unknown>)["requests"]
        ) {
          const maybe = (data as Record<string, unknown>)["requests"];
          return (maybe as TunnelRequest[]) ?? [];
        }
        return (data as TunnelRequest[]) ?? [];
      })();
      setRecentRequests(reqs ?? []);
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
        // API may return { success: true, message, tunnel: { ... } }
        const tunnelData = data?.tunnel ?? null;

        // clear any previous validation info
        setValidationResult(null);

        // Try to fetch the canonical/updated connection from the backend.
        // Some backends populate additional fields or change 'status' after
        // register completes, so prefer the refreshed object when present.
        let dispatchedConnection: TunnelConnection | null = null;
        try {
          const refreshed = await apiClient.getTunnelStatus();
          // Unwrap wrapper if necessary
          const refreshedConn = ((): TunnelConnection | null => {
            if (!refreshed) return null;
            if (
              typeof refreshed === "object" &&
              (refreshed as Record<string, unknown>)["tunnel"]
            ) {
              const maybe = (refreshed as Record<string, unknown>)["tunnel"];
              return (maybe as TunnelConnection) ?? null;
            }
            return (refreshed as TunnelConnection) ?? null;
          })();
          if (refreshedConn) {
            setConnection(refreshedConn);
            dispatchedConnection = refreshedConn;
          } else {
            setConnection(tunnelData);
            dispatchedConnection = tunnelData;
          }
        } catch {
          // If the follow-up status check fails, fall back to the returned
          // tunnel object from the register call (if any).
          setConnection(tunnelData);
          dispatchedConnection = tunnelData;
        }

        // Notify other parts of the app that a tunnel was connected
        try {
          window.dispatchEvent(
            new CustomEvent("tunnel:connected", {
              detail: dispatchedConnection,
            })
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
      // Notify other hook instances that the tunnel was disconnected
      try {
        window.dispatchEvent(new CustomEvent("tunnel:disconnected"));
      } catch {
        // ignore
      }
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

  // Listen for global tunnel events so separate hook instances stay in sync
  useEffect(() => {
    const onConnected = (e: Event) => {
      try {
        const detail = (e as CustomEvent).detail as TunnelConnection | null;
        if (detail) {
          setConnection(detail);
        } else {
          // If no detail, refresh canonical status
          void refreshStatus();
        }
      } catch {
        void refreshStatus();
      }
    };

    const onDisconnected = () => {
      setConnection(null);
      setRecentRequests([]);
    };

    window.addEventListener("tunnel:connected", onConnected as EventListener);
    window.addEventListener(
      "tunnel:disconnected",
      onDisconnected as EventListener
    );

    return () => {
      window.removeEventListener(
        "tunnel:connected",
        onConnected as EventListener
      );
      window.removeEventListener(
        "tunnel:disconnected",
        onDisconnected as EventListener
      );
    };
  }, [refreshStatus]);

  // Computed values
  // Treat both 'connected' and 'active' as active states (backend may use either)
  const isActive =
    connection?.status === "connected" || connection?.status === "active";

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
