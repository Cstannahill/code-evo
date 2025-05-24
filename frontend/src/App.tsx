import React, { useEffect, useState } from "react";
import { Dashboard } from "./components/features/Dashboard";
import { apiClient } from "./api/client";
import { AlertCircle, CheckCircle2 } from "lucide-react";
// import type { ErrorPayload } from "vite/types/hmrPayload.js";

function App() {
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "online" | "offline"
  >("checking");
  const [aiStatus, setAiStatus] = useState<{
    available: boolean;
    model?: string;
  } | null>(null);

  useEffect(() => {
    checkBackendStatus();
  }, []);

  const checkBackendStatus = async () => {
    try {
      console.log("Checking backend status...");
      const health = await apiClient.checkHealth();
      console.log("Health check response:", health);
      setBackendStatus(health.status === "healthy" ? "online" : "offline");

      // Check AI status
      const aiStatusResponse = await apiClient.getAnalysisStatus();
      console.log("AI status response:", aiStatusResponse);
      setAiStatus({
        available: aiStatusResponse.ai_service.ollama_available,
        model: aiStatusResponse.ai_service.model,
      });
    } catch (error: ErrorPayload | unknown) {
      console.error("Error checking backend status:", error);
      setBackendStatus("offline");
    }
  };

  return (
    <>
      {/* Status Bar */}
      <div className="fixed top-0 left-0 right-0 bg-background border-b z-50">
        <div className="container mx-auto px-4 py-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                {backendStatus === "online" ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
                <span className="text-muted-foreground">
                  Backend: {backendStatus}
                </span>
              </div>
              {aiStatus && (
                <div className="flex items-center gap-2">
                  {aiStatus.available ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-orange-500" />
                  )}
                  <span className="text-muted-foreground">
                    AI:{" "}
                    {aiStatus.available
                      ? `Active (${aiStatus.model})`
                      : "Not Available"}
                  </span>
                </div>
              )}
            </div>
            {backendStatus === "offline" && (
              <span className="text-destructive">
                Start backend: cd backend && python -m uvicorn app.main:app
                --reload
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="pt-10">
        <Dashboard />
      </div>
    </>
  );
}

export default App;
