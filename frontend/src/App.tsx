import { useEffect, useState } from "react";
import { apiClient } from "./api/client";
import { AlertCircle, CheckCircle2, LogIn } from "lucide-react";
import ErrorBoundary from "./components/ErrorBoundary";
// import LoggingDemo from "./components/LoggingDemo";
import { useLogger } from "./hooks/useLogger";
import { MultiAnalysisDashboard } from "./components/features/MultiAnalysisDashboard";
import { SimpleThemeToggle } from "./components/ui/ThemeToggle";
import { AuthModal } from "./components/auth/AuthModal";
import { UserMenu } from "./components/auth/UserMenu";

// Main App Content Component
function AppContent() {
  const logger = useLogger("App");
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
    logger.mount();

    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const response = await fetch('/api/auth/me', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          setIsAuthenticated(response.ok);
        } catch (error) {
          setIsAuthenticated(false);
        }
      }
      setAuthLoading(false);
    };

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

    checkAuth();
    doCheck();

    return () => {
      logger.unmount();
    };
  }, []);

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
              <div className="flex items-center gap-2">
                {backendStatus === "online" ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
                <span className="text-stone-400/40">
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
                  <span className="text-stone-400/40">
                    AI: {aiStatus.available ? `Active` : "Not Available"}
                  </span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-4">
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

              {backendStatus === "offline" && (
                <span className="text-destructive">
                  Start backend: cd backend && python -m uvicorn app.main:app
                  --reload
                </span>
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
