import React, { useState, useEffect } from "react";
import { getApiBaseUrl } from "../config/environment";

interface AvailableModel {
  name?: string;
  display_name?: string;
  available?: boolean;
  cost_per_1k_tokens?: number;
}

interface AvailableModelsResponse {
  available_models?: Record<string, AvailableModel>;
}

const ModelDebugTest: React.FC = () => {
  const [models, setModels] = useState<AvailableModelsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        console.log("Fetching models...");
        const apiBaseUrl = getApiBaseUrl();
        const response = await fetch(
          `${apiBaseUrl}/api/analysis/models/available`
        );
        console.log("Response status:", response.status);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Raw API data:", data);
        console.log("Available models:", data.available_models);
        console.log("Model keys:", Object.keys(data.available_models || {}));

        setModels(data);
      } catch (err) {
        console.error("Error fetching models:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  const availableModels = models?.available_models ?? {};
  const modelKeys = Object.keys(availableModels);

  return (
    <div style={{ padding: "20px", fontFamily: "monospace" }}>
      <h1>Model Debug Test</h1>
      <h2>API Response Status: {models ? "SUCCESS" : "FAILED"}</h2>
      <h3>Model Count: {modelKeys.length}</h3>
      <h3>Model Keys:</h3>
      <ul>
        {modelKeys.map((key) => (
          <li key={key}>
            <strong>{key}</strong>: {availableModels[key]?.name}(
            {availableModels[key]?.available ? "Available" : "Not Available"})
          </li>
        ))}
      </ul>

      <h3>Devstral Status:</h3>
      <p>
        Present in response: {availableModels["codellama:13b"] ? "YES" : "NO"}
      </p>
      {availableModels["codellama:13b"] && (
        <pre>{JSON.stringify(availableModels["codellama:13b"], null, 2)}</pre>
      )}

      <h3>Local Models (cost = 0):</h3>
      <ul>
        {Object.entries(availableModels)
          .filter(([, model]) => (model.cost_per_1k_tokens ?? 0) === 0)
          .map(([key, model]) => (
            <li key={key}>
              {key}: {model.name ?? "Unknown"}
            </li>
          ))}
      </ul>

      <h3>Full Response:</h3>
      <pre
        style={{
          background: "#f0f0f0",
          padding: "10px",
          maxHeight: "300px",
          overflow: "auto",
        }}
      >
        {JSON.stringify(models, null, 2)}
      </pre>
    </div>
  );
};

export default ModelDebugTest;
