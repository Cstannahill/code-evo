import { useState, useEffect, useCallback } from 'react';

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
}

const OLLAMA_BASE_URL = 'http://127.0.0.1:11434';

export const useLocalOllama = () => {
  const [status, setStatus] = useState<LocalOllamaStatus>({
    available: false,
    models: [],
    lastChecked: new Date()
  });
  const [isChecking, setIsChecking] = useState(false);

  const checkLocalOllama = useCallback(async (timeoutMs = 2000): Promise<boolean> => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
      const response = await fetch(`${OLLAMA_BASE_URL}/api/version`, {
        method: 'GET',
        mode: 'cors',
        signal: controller.signal,
      });
      
      clearTimeout(timeout);
      return response.ok;
    } catch (err) {
      clearTimeout(timeout);
      return false;
    }
  }, []);

  const discoverModels = useCallback(async (): Promise<LocalOllamaModel[]> => {
    try {
      const response = await fetch(`${OLLAMA_BASE_URL}/api/tags`, {
        method: 'GET',
        mode: 'cors',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.status}`);
      }
      
      const data = await response.json();
      return data.models || [];
    } catch (err) {
      console.error('Failed to discover Ollama models:', err);
      return [];
    }
  }, []);

  const checkAndUpdateStatus = useCallback(async () => {
    setIsChecking(true);
    
    try {
      const isAvailable = await checkLocalOllama();
      
      if (isAvailable) {
        const models = await discoverModels();
        const versionResponse = await fetch(`${OLLAMA_BASE_URL}/api/version`, {
          method: 'GET',
          mode: 'cors',
        });
        const versionData = await versionResponse.json();
        
        setStatus({
          available: true,
          models,
          version: versionData.version,
          lastChecked: new Date()
        });
      } else {
        setStatus({
          available: false,
          models: [],
          lastChecked: new Date()
        });
      }
    } catch (err) {
      console.error('Error checking local Ollama:', err);
      setStatus({
        available: false,
        models: [],
        lastChecked: new Date()
      });
    } finally {
      setIsChecking(false);
    }
  }, [checkLocalOllama, discoverModels]);

  // Auto-check on mount and every 30 seconds
  useEffect(() => {
    checkAndUpdateStatus();
    const interval = setInterval(checkAndUpdateStatus, 30000);
    return () => clearInterval(interval);
  }, [checkAndUpdateStatus]);

  const generateWithLocalOllama = useCallback(async (
    model: string,
    prompt: string,
    options: Record<string, any> = {}
  ) => {
    if (!status.available) {
      throw new Error('Local Ollama is not available');
    }

    try {
      const response = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        mode: 'cors',
        body: JSON.stringify({
          model,
          prompt,
          stream: false,
          ...options
        }),
      });

      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error calling local Ollama:', err);
      throw err;
    }
  }, [status.available]);

  const chatWithLocalOllama = useCallback(async (
    model: string,
    messages: Array<{ role: string; content: string }>,
    options: Record<string, any> = {}
  ) => {
    if (!status.available) {
      throw new Error('Local Ollama is not available');
    }

    try {
      const response = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        mode: 'cors',
        body: JSON.stringify({
          model,
          messages,
          stream: false,
          ...options
        }),
      });

      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error calling local Ollama:', err);
      throw err;
    }
  }, [status.available]);

  return {
    status,
    isChecking,
    checkAndUpdateStatus,
    generateWithLocalOllama,
    chatWithLocalOllama,
  };
};
