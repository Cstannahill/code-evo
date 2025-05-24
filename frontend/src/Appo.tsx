import { useState, useEffect } from "react";
import { Dashboard } from "./components/features/Dashboard";
// import { apiClient } from "./api/client";

function AppCheck() {
  const [healthStatus, setHealthStatus] = useState<string>("Checking...");

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch("http://localhost:8080/health");
      const data = await response.json();
      setHealthStatus(data.status === "ok" ? "Connected ✅" : "Error ❌");
    } catch (error: unknown) {
      if (error instanceof Error) {
        setHealthStatus(`Backend not running ❌: ${error.message}`);
      } else {
        setHealthStatus(`Backend not running ❌: ${String(error)}`);
      }
    }
  };

  return (
    <div className="flex border border-slate-100 w-screen items-center justify-center h-screen">
      <div className="container mx-auto p-4">
        <div className="mb-4 text-sm text-muted-foreground text-blue-500">
          Backend Status: {healthStatus}
        </div>
        <Dashboard />
      </div>
    </div>
  );
}

export default AppCheck;
