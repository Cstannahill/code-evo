import { useState, useEffect, useCallback, useMemo } from "react";

export interface LocalOllamaModel {
  name: string;
  size: number;
  modified_at: string;
  digest: string;
}

export interface LocalOllamaStatus {
  available: boolean;
  models: LocalOllamaModel[];
  version?: string;
  lastChecked: Date;
  baseUrl: string;
  blockedReason?: string;
  errorMessage?: string;
}

const DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434";
const normalizeUrl = (value: string): string =>
  value.endsWith("/") ? value.slice(0, -1) : value;

export const useLocalOllama = () => {
  const resolvedBaseUrl = useMemo(() => {
    const configured =
      (import.meta.env.VITE_OLLAMA_BASE_URL as string | undefined) ??
      DEFAULT_OLLAMA_BASE_URL;
    return normalizeUrl(configured);
  }, []);

  const environmentInfo = useMemo(() => {
    if (typeof window === "undefined") {
      return {
        isSecureContext: false,
        isLocalhost: true,
      };
    }

    const { protocol, hostname } = window.location;
    const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1";

    return {
      isSecureContext: protocol === "https:",
      isLocalhost,
    };
  }, []);

  const [status, setStatus] = useState<LocalOllamaStatus>(() => ({
    available: false,
    models: [],
    baseUrl: resolvedBaseUrl,
    lastChecked: new Date(),
    blockedReason: undefined,
    errorMessage: undefined,
  }));
  const [isChecking, setIsChecking] = useState(false);

  const isLikelyBlockedByBrowser = useMemo(
    () =>
      environmentInfo.isSecureContext &&
      !environmentInfo.isLocalhost &&
      resolvedBaseUrl.startsWith("http://"),
    [environmentInfo, resolvedBaseUrl]
  );

  const checkLocalOllama = useCallback(
    async (timeoutMs = 2000): Promise<boolean> => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);

      try {
        const response = await fetch(`${resolvedBaseUrl}/api/version`, {
          method: "GET",
          mode: "cors",
          signal: controller.signal,
        });

        clearTimeout(timeout);
        return response.ok;
      } catch (err) {
        clearTimeout(timeout);
        console.warn("Local Ollama version check failed:", err);
        return false;
      }
    },
    [resolvedBaseUrl]
  );

  const discoverModels = useCallback(async (): Promise<LocalOllamaModel[]> => {
    try {
      const response = await fetch(`${resolvedBaseUrl}/api/tags`, {
        method: "GET",
        mode: "cors",
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.status}`);
      }

      const data = await response.json();
      return data.models || [];
    } catch (err) {
      console.error("Failed to discover Ollama models:", err);
      return [];
    }
  }, [resolvedBaseUrl]);

  const checkAndUpdateStatus = useCallback(async () => {
    setIsChecking(true);

    try {
      if (isLikelyBlockedByBrowser) {
        const blockedReason =
          "Local Ollama cannot be accessed from a secure (HTTPS) origin because the server is only exposed over HTTP on 127.0.0.1. Run the frontend locally over HTTP, configure VITE_OLLAMA_BASE_URL to point to a secure tunnel, or use the backend-hosted models instead.";
        setStatus({
          available: false,
          models: [],
          baseUrl: resolvedBaseUrl,
          lastChecked: new Date(),
          blockedReason,
          errorMessage: undefined,
        });
        return;
      }

      const isAvailable = await checkLocalOllama();

      if (isAvailable) {
        const models = await discoverModels();
        const versionResponse = await fetch(`${resolvedBaseUrl}/api/version`, {
          method: "GET",
          mode: "cors",
        });
        const versionData = await versionResponse.json();

        setStatus({
          available: true,
          models,
          version: versionData.version,
          lastChecked: new Date(),
          baseUrl: resolvedBaseUrl,
          blockedReason: undefined,
          errorMessage: undefined,
        });
      } else {
        setStatus({
          available: false,
          models: [],
          lastChecked: new Date(),
          baseUrl: resolvedBaseUrl,
          blockedReason: undefined,
          errorMessage:
            "Ollama did not respond on the configured address. Ensure the daemon is running and accessible from your browser.",
        });
      }
    } catch (err) {
      console.error("Error checking local Ollama:", err);
      setStatus({
        available: false,
        models: [],
        lastChecked: new Date(),
        baseUrl: resolvedBaseUrl,
        blockedReason: undefined,
        errorMessage:
          err instanceof Error
            ? err.message
            : "Unknown error while contacting local Ollama.",
      });
    } finally {
      setIsChecking(false);
    }
  }, [
    checkLocalOllama,
    discoverModels,
    isLikelyBlockedByBrowser,
    resolvedBaseUrl,
  ]);

  // Auto-check on mount and every 30 seconds
  useEffect(() => {
    checkAndUpdateStatus();
    const interval = setInterval(checkAndUpdateStatus, 30000);
    return () => clearInterval(interval);
  }, [checkAndUpdateStatus]);

  const generateWithLocalOllama = useCallback(
    async (
      model: string,
      prompt: string,
      options: Record<string, unknown> = {}
    ) => {
      if (!status.available) {
        throw new Error("Local Ollama is not available");
      }

      try {
        const response = await fetch(`${resolvedBaseUrl}/api/generate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          mode: "cors",
          body: JSON.stringify({
            model,
            prompt,
            stream: false,
            ...options,
          }),
        });

        if (!response.ok) {
          throw new Error(`Ollama API error: ${response.status}`);
        }

        const data = await response.json();
        return data;
      } catch (err) {
        console.error("Error calling local Ollama:", err);
        throw err;
      }
    },
    [resolvedBaseUrl, status.available]
  );

  const chatWithLocalOllama = useCallback(
    async (
      model: string,
      messages: Array<{ role: string; content: string }>,
      options: Record<string, unknown> = {}
    ) => {
      if (!status.available) {
        throw new Error("Local Ollama is not available");
      }

      try {
        const response = await fetch(`${resolvedBaseUrl}/api/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          mode: "cors",
          body: JSON.stringify({
            model,
            messages,
            stream: false,
            ...options,
          }),
        });

        if (!response.ok) {
          throw new Error(`Ollama API error: ${response.status}`);
        }

        const data = await response.json();
        return data;
      } catch (err) {
        console.error("Error calling local Ollama:", err);
        throw err;
      }
    },
    [resolvedBaseUrl, status.available]
  );

  return {
    status,
    isChecking,
    checkAndUpdateStatus,
    generateWithLocalOllama,
    chatWithLocalOllama,
  };
};
