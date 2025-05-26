import { useCallback, useEffect, useState } from "react";
import { Dashboard } from "./components/features/Dashboard";
import { apiClient } from "./api/client";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import ErrorBoundary from "./components/ErrorBoundary";
// import LoggingDemo from "./components/LoggingDemo";
import { useLogger } from "./hooks/useLogger";

function App() {
  const logger = useLogger("App");
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "online" | "offline"
  >("checking");
  const [aiStatus, setAiStatus] = useState<
    | {
        available: boolean;
        model?: string;
      }
    | undefined
  >(undefined);

  useEffect(() => {
    logger.mount();

    const doCheck = async () => {
      logger.info("Checking backend status");

      try {
        const health = await apiClient.checkHealth();
        setBackendStatus(health.status === "healthy" ? "online" : "offline");
        logger.info("Backend health check completed");

        const aiStat = await apiClient.getAnalysisStatus();
        logger.info("AI status check started", { aiStat });
        setAiStatus({
          available: aiStat.ai_service.ollama_available,
          model: aiStat?.ai_service?.ollama_model,
        });
        logger.info("AI status check completed");
      } catch (err) {
        logger.error("Error checking backend status", err as Error);
        setBackendStatus("offline");
      }
    };

    doCheck();

    return () => {
      logger.unmount();
    };
  }, []);
  return (
    <>
      {/* Status Bar */}
      <div className="fixed top-0 left-0 right-0 bg-background border-b z-50 backdrop-blur-sm bg-opacity-90">
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
        <ErrorBoundary
          onError={(error, _errorInfo) => {
            logger.error("Application Error Boundary triggered", error);
          }}
        >
          <Dashboard />
        </ErrorBoundary>

        {/* Development Mode: Logging Demo */}
        {/* {import.meta.env.DEV && (
          <div className="container mx-auto px-4 py-8">
            <div className="border-t pt-8">
              <h2 className="text-xl font-bold mb-4">
                Development: Logging System Demo
              </h2>
              <LoggingDemo />
            </div>
          </div>
        )} */}
      </div>
    </>
  );
}

export default App;
