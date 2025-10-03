import { useEffect, useState } from "react";
import { apiClient } from "./api/client";
import { LogIn } from "lucide-react";
import ErrorBoundary from "./components/ErrorBoundary";
// import LoggingDemo from "./components/LoggingDemo";
import { useLogger } from "./hooks/useLogger";
import { MultiAnalysisDashboard } from "./components/features/MultiAnalysisDashboard";
import { SimpleThemeToggle } from "./components/ui/ThemeToggle";
import { AuthModal } from "./components/auth/AuthModal";
import { UserMenu } from "./components/auth/UserMenu";
import { TunnelToggle } from "./components/tunnel/TunnelToggle";

// Main App Content Component
function AppContent() {
  const logger = useLogger("App");
  const { mount, unmount, info, error } = logger;
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
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
    mount();

    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          await apiClient.getCurrentUser();
          setIsAuthenticated(true);
        } catch {
          // Invalid/expired token; clear it and treat as unauthenticated
          localStorage.removeItem('auth_token');
          setIsAuthenticated(false);
        }
      }
      setAuthLoading(false);
    };

    const doCheck = async () => {
      info("Checking backend status");

      try {
        const health = await apiClient.checkHealth();
        setBackendStatus(health.status === "healthy" ? "online" : "offline");
        info("Backend health check completed");

        const aiStat = await apiClient.getAnalysisStatus();
        info("AI status check started", { aiStat });

        // Add null safety checks for aiStat and ai_service
        if (aiStat && aiStat.ai_service) {
          setAiStatus({
            available: aiStat.ai_service.ollama_available,
            model: aiStat.ai_service.ollama_model,
          });
          info("AI status check completed");
        } else {
          // Fallback for when AI service is not available
          setAiStatus({
            available: false,
            model: undefined,
          });
          info("AI service not available - using fallback status");
        }
      } catch (err) {
        error("Error checking backend status", err as Error);
        setBackendStatus("offline");
        // Set AI status to unavailable on error
        setAiStatus({
          available: false,
          model: undefined,
        });
      }
    };

    checkAuth();
    doCheck();

    return () => {
      unmount();
    };
  }, [mount, unmount, info, error]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Status Bar */}
      <div className="fixed top-0 left-0 right-0 bg-background border-b z-50 backdrop-blur-sm bg-opacity-90">
        <div className="container mx-auto px-4 py-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span>
                  Backend: {backendStatus === "checking" ? "…" : backendStatus}
                </span>
                <span className="hidden sm:inline">|</span>
                <span>
                  AI: {aiStatus ? (aiStatus.available ? (aiStatus.model || "available") : "unavailable") : "…"}
                </span>
              </div>

            </div>
            <div className="flex items-center gap-4">
              <TunnelToggle />
              <SimpleThemeToggle />

              {/* Authentication UI */}
              {isAuthenticated ? (
                <UserMenu />
              ) : (
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="flex items-center gap-2 px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition-colors"
                >
                  <LogIn className="w-3 h-3" />
                  Login / Register
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="pt-10 main-bg">
        <ErrorBoundary
          onError={(error, _errorInfo) => {
            logger.error("Application Error Boundary triggered", error);
          }}
        >
          <MultiAnalysisDashboard />
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

      {/* Authentication Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </>
  );
}

// Main App Component
function App() {
  return <AppContent />;
}

export default App;
