import React, { useEffect, useState } from "react";
import {
  useLogger,
  usePerformanceMeasure,
  useApiLogger,
} from "../hooks/useLogger";

const LoggingDemo: React.FC = () => {
  const [count, setCount] = useState(0);
  const [error, setError] = useState<Error | null>(null);
  const logger = useLogger("LoggingDemo", { initialCount: count });
  const { startMeasure, endMeasure } = usePerformanceMeasure(
    "LoggingDemo",
    "expensive-operation"
  );
  const { trackApiCall } = useApiLogger("LoggingDemo");

  useEffect(() => {
    logger.mount({ initialCount: count });

    return () => {
      logger.unmount();
    };
  }, [logger, count]);

  useEffect(() => {
    logger.effect("count-change", "run", { newCount: count });

    return () => {
      logger.effect("count-change", "cleanup", { count });
    };
  }, [count, logger]);

  const handleIncrement = () => {
    logger.userAction("increment", "button", { currentCount: count });
    setCount((prev) => prev + 1);
  };

  const handleExpensiveOperation = async () => {
    startMeasure();

    // Simulate expensive operation
    await new Promise((resolve) =>
      setTimeout(resolve, 1000 + Math.random() * 2000)
    );

    endMeasure({
      operationType: "simulation",
      itemsProcessed: count * 10,
    });

    logger.info("Expensive operation completed", {
      itemsProcessed: count * 10,
      duration: "measured-above",
    });
  };

  const handleApiTest = async () => {
    try {
      await trackApiCall("/test/endpoint", "GET", async () => {
        // Simulate API call
        await new Promise((resolve) => setTimeout(resolve, 500));

        if (Math.random() > 0.7) {
          throw new Error("Simulated API error");
        }

        return { success: true, data: "test" };
      });

      logger.info("API test completed successfully");
    } catch (error) {
      logger.error(
        "API test failed",
        error instanceof Error ? error : new Error(String(error))
      );
    }
  };

  const handleError = () => {
    const testError = new Error("This is a test error for logging");
    setError(testError);
    logger.error("Test error triggered", testError, {
      userTriggered: true,
      errorType: "manual",
    });
  };

  const handleWarning = () => {
    logger.warn("This is a test warning", {
      warningType: "user-action",
      context: "demo",
    });
  };

  const handleDebug = () => {
    logger.debug("Debug information", {
      currentState: { count, hasError: !!error },
      debugLevel: "verbose",
      timestamp: new Date().toISOString(),
    });
  };

  if (error) {
    throw error; // This will be caught by ErrorBoundary
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-4">Logging System Demo</h2>

      <div className="space-y-4">
        <div>
          <p className="text-lg">Count: {count}</p>
          <button
            onClick={handleIncrement}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Increment (+1)
          </button>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">Logging Tests:</h3>

          <button
            onClick={handleExpensiveOperation}
            className="block w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Test Performance Logging
          </button>

          <button
            onClick={handleApiTest}
            className="block w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
          >
            Test API Logging
          </button>

          <button
            onClick={handleWarning}
            className="block w-full px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
          >
            Test Warning Log
          </button>

          <button
            onClick={handleDebug}
            className="block w-full px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Test Debug Log
          </button>

          <button
            onClick={handleError}
            className="block w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Test Error (Triggers ErrorBoundary)
          </button>
        </div>

        <div className="text-sm text-gray-600">
          <p>Check the browser console to see structured logs.</p>
          <p>Component: {logger.componentName}</p>
          <p>Render Count: {logger.renderCount}</p>
        </div>
      </div>
    </div>
  );
};

export default LoggingDemo;
