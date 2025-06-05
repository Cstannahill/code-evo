import { useCallback, useMemo, useRef } from "react";
import type {
  ComponentProps,
  LogContext,
  UserActionContext,
  PerformanceContext,
  ErrorLogContext,
  ApiLogContext,
} from "../types/logging";
import logger from "../lib/logger";

/**
 * React hook for component-level logging integration
 * Provides memoized logging functions with automatic component context enrichment
 *
 * @param componentName - Name of the component using the logger
 * @param componentProps - Optional props to include in log context
 * @returns Memoized logging interface for the component
 */
export function useLogger(
  componentName: string,
  componentProps?: ComponentProps
) {
  const renderCountRef = useRef(0);
  renderCountRef.current += 1;

  // Memoize the base context to avoid recreating on every render
  const baseContext = useMemo(
    () => ({
      component: componentName,
      renderCount: renderCountRef.current,
      ...(componentProps && { props: componentProps }),
    }),
    [componentName, componentProps]
  );

  // Memoized logging functions
  const logInfo = useCallback(
    (message: string, context?: LogContext) => {
      logger.info(message, { ...baseContext, ...context });
    },
    [baseContext]
  );

  const logWarn = useCallback(
    (message: string, context?: LogContext) => {
      logger.warn(message, { ...baseContext, ...context });
    },
    [baseContext]
  );

  const logError = useCallback(
    (message: string, error?: Error, context?: LogContext) => {
      logger.error(message, {
        ...baseContext,
        ...context,
        error: error?.message,
        errorStack: error?.stack,
      });
    },
    [baseContext]
  );

  const logDebug = useCallback(
    (message: string, context?: LogContext) => {
      logger.debug(message, { ...baseContext, ...context });
    },
    [baseContext]
  );

  // User action tracking with automatic timing
  const logUserAction = useCallback(
    (
      action: string,
      target?: string,
      additionalContext?: Omit<
        UserActionContext,
        "action" | "target" | "timestamp" | "component"
      >
    ) => {
      const userActionContext: UserActionContext = {
        action,
        target,
        timestamp: new Date().toISOString(),
        component: componentName,
        ...additionalContext,
      };

      logger.userAction(userActionContext, `User action: ${action}`);
    },
    [componentName]
  );

  // Performance measurement with automatic timing
  const measurePerformance = useCallback(
    (
      operation: string,
      startTime: number,
      additionalContext?: Omit<
        PerformanceContext,
        "operation" | "duration" | "timestamp" | "component"
      >
    ) => {
      const duration = Date.now() - startTime;
      const performanceContext: PerformanceContext = {
        operation,
        duration,
        startTime,
        endTime: Date.now(),
        timestamp: new Date().toISOString(),
        component: componentName,
        ...additionalContext,
      };

      logger.performance(
        performanceContext,
        `Performance: ${operation} completed in ${duration}ms`,
        { duration }
      );
    },
    [componentName]
  );

  // Lifecycle logging helpers
  const logMount = useCallback(
    (context?: LogContext) => {
      logger.debug(`Component ${componentName} mounted`, {
        ...baseContext,
        lifecycle: "mount",
        ...context,
      });
    },
    [componentName, baseContext]
  );

  const logUnmount = useCallback(
    (context?: LogContext) => {
      logger.debug(`Component ${componentName} unmounting`, {
        ...baseContext,
        lifecycle: "unmount",
        ...context,
      });
    },
    [componentName, baseContext]
  );

  const logUpdate = useCallback(
    (reason?: string, context?: LogContext) => {
      logger.debug(`Component ${componentName} updated`, {
        ...baseContext,
        lifecycle: "update",
        reason,
        ...context,
      });
    },
    [componentName, baseContext]
  );

  // Effect logging helper
  const logEffect = useCallback(
    (effectName: string, type: "run" | "cleanup", context?: LogContext) => {
      const level = type === "cleanup" ? "debug" : "debug";
      logger[level](`Effect ${effectName} ${type}`, {
        ...baseContext,
        effect: effectName,
        type,
        ...context,
      });
    },
    [baseContext]
  );

  // Error boundary logging helper
  const logErrorBoundary = useCallback(
    (error: Error, errorInfo?: { componentStack?: string }) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { component, ...restBaseContext } = baseContext;
      const errorContext: ErrorLogContext = {
        errorType: error.name,
        stackTrace: error.stack,
        component: componentName,
        ...restBaseContext,
        errorInfo,
      };

      logger.errorBoundary(
        errorContext,
        `Error boundary caught error in ${componentName}`,
        error
      );
    },
    [componentName, baseContext]
  );

  // API call logging with correlation
  const logApiCall = useCallback(
    (
      endpoint: string,
      method: string,
      options?: {
        requestId?: string;
        startTime?: number;
        statusCode?: number;
        responseTime?: number;
        requestSize?: number;
        responseSize?: number;
        error?: Error;
      }
    ) => {
      const { startTime, statusCode, responseTime, error, ...restOptions } =
        options || {};

      if (error) {
        const apiContext: ApiLogContext = {
          method,
          url: endpoint,
          statusCode,
          duration:
            responseTime || (startTime ? Date.now() - startTime : undefined),
          component: componentName,
          error: error.message,
          ...restOptions,
        };
        logger.apiCall(apiContext, `API call failed: ${method} ${endpoint}`);
      } else {
        const apiContext: ApiLogContext = {
          method,
          url: endpoint,
          statusCode,
          duration:
            responseTime || (startTime ? Date.now() - startTime : undefined),
          component: componentName,
          ...restOptions,
        };
        logger.apiCall(apiContext, `API call: ${method} ${endpoint}`);
      }
    },
    [componentName]
  );

  return {
    // Basic logging
    info: logInfo,
    warn: logWarn,
    error: logError,
    debug: logDebug,

    // Specialized logging
    userAction: logUserAction,
    performance: measurePerformance,
    apiCall: logApiCall,
    errorBoundary: logErrorBoundary,

    // Lifecycle logging
    mount: logMount,
    unmount: logUnmount,
    update: logUpdate,
    effect: logEffect,

    // Context information
    componentName,
    renderCount: renderCountRef.current,
  } as const;
}

/**
 * Hook for performance measurement with automatic cleanup
 * Returns a function to mark the end of the operation
 *
 * @param componentName - Name of the component
 * @param operation - Name of the operation being measured
 * @returns Function to call when operation completes
 */
export function usePerformanceMeasure(
  componentName: string,
  operation: string
) {
  const startTimeRef = useRef<number>(0);

  const startMeasure = useCallback(() => {
    startTimeRef.current = Date.now();
  }, []);

  const endMeasure = useCallback(
    (
      additionalContext?: Omit<
        PerformanceContext,
        "operation" | "duration" | "timestamp" | "component"
      >
    ) => {
      if (startTimeRef.current) {
        const duration = Date.now() - startTimeRef.current;
        const performanceContext: PerformanceContext = {
          operation,
          duration,
          startTime: startTimeRef.current,
          endTime: Date.now(),
          timestamp: new Date().toISOString(),
          component: componentName,
          ...additionalContext,
        };

        logger.performance(
          performanceContext,
          `Performance: ${operation} completed in ${duration}ms`,
          { duration }
        );
        startTimeRef.current = 0;
      }
    },
    [componentName, operation]
  );

  return { startMeasure, endMeasure };
}

/**
 * Hook for API call tracking with automatic correlation
 *
 * @param componentName - Name of the component making API calls
 * @returns Functions for tracking API calls
 */
export function useApiLogger(componentName: string) {
  const { apiCall } = useLogger(componentName);

  const trackApiCall = useCallback(
    async <T>(
      endpoint: string,
      method: string,
      apiCallFn: () => Promise<T>,
      requestId?: string
    ): Promise<T> => {
      const startTime = Date.now();

      try {
        logger.debug(`Starting API call: ${method} ${endpoint}`, {
          endpoint,
          method,
          component: componentName,
          requestId,
          startTime,
        });

        const result = await apiCallFn();
        const responseTime = Date.now() - startTime;

        apiCall(endpoint, method, {
          requestId,
          startTime,
          responseTime,
          statusCode: 200, // Assume success if no error thrown
        });

        return result;
      } catch (error) {
        const responseTime = Date.now() - startTime;

        apiCall(endpoint, method, {
          requestId,
          startTime,
          responseTime,
          statusCode:
            error instanceof Error &&
            "status" in error &&
            typeof (error as { status: unknown }).status === "number"
              ? (error as { status: number }).status
              : 500,
          error: error instanceof Error ? error : new Error(String(error)),
        });

        throw error;
      }
    },
    [componentName, apiCall]
  );

  return { trackApiCall };
}
