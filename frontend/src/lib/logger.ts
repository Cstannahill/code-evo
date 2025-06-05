/**
 * @fileoverview Core Pino logger implementation for the Code Evolution Tracker
 * Provides production-ready logging with session tracking, correlation IDs, and
 * structured logging for API calls, user actions, errors, and performance metrics
 */

import pino from "pino";
import type {
  AppLogger,
  LoggerConfig,
  LogContext,
  ApiLogContext,
  UILogContext,
  ErrorLogContext,
  PerformanceLogContext,
  TransportConfig,
  SessionManager,
  CompleteLoggerConfig,
  LogLevel,
} from "../types/logging";
import {
  LOG_LEVEL,
  DEFAULT_LOGGER_CONFIG,
  LOGGER_ENV_KEYS,
} from "../types/logging";

/**
 * Environment-aware configuration builder
 * @returns Configuration based on environment variables and defaults
 */
const buildConfiguration = (): LoggerConfig => {
  const getEnvBoolean = (key: string, defaultValue: boolean): boolean => {
    const value = import.meta.env[key];
    return value !== undefined ? value === "true" : defaultValue;
  };

  const getEnvNumber = (key: string, defaultValue: number): number => {
    const value = import.meta.env[key];
    return value !== undefined
      ? parseInt(value, 10) || defaultValue
      : defaultValue;
  };

  const getEnvLogLevel = (key: string, defaultValue: LogLevel): LogLevel => {
    const value = import.meta.env[key] as LogLevel;
    return Object.values(LOG_LEVEL).includes(value) ? value : defaultValue;
  };

  return {
    level: getEnvLogLevel(
      LOGGER_ENV_KEYS.LOG_LEVEL,
      DEFAULT_LOGGER_CONFIG.level
    ),
    isDevelopment: import.meta.env.DEV,
    enableFileLogging: getEnvBoolean(
      LOGGER_ENV_KEYS.ENABLE_FILE_LOGGING,
      !import.meta.env.DEV
    ),
    enableConsoleLogging: getEnvBoolean(
      LOGGER_ENV_KEYS.ENABLE_CONSOLE_LOGGING,
      import.meta.env.DEV
    ),
    fileRotationHours: getEnvNumber(
      LOGGER_ENV_KEYS.FILE_ROTATION_HOURS,
      DEFAULT_LOGGER_CONFIG.fileRotationHours
    ),
    enableCorrelationTracking: DEFAULT_LOGGER_CONFIG.enableCorrelationTracking,
  };
};

/**
 * Session manager implementation for tracking user sessions and correlation IDs
 * Provides unique identifiers for request correlation and user session tracking
 */
class SessionManagerImpl implements SessionManager {
  private static instance: SessionManagerImpl;
  private readonly sessionId: string;
  private correlationCounter: number = 0;
  private userId?: string;

  private constructor() {
    this.sessionId = this.generateSessionId();
  }

  /**
   * Get singleton instance of session manager
   * @returns SessionManager instance
   */
  public static getInstance(): SessionManagerImpl {
    if (!SessionManagerImpl.instance) {
      SessionManagerImpl.instance = new SessionManagerImpl();
    }
    return SessionManagerImpl.instance;
  }

  /**
   * Generate unique session ID
   * @returns Unique session identifier
   */
  private generateSessionId(): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    return `session_${timestamp}_${random}`;
  }

  /**
   * Get current session ID
   * @returns Current session identifier
   */
  public getSessionId(): string {
    return this.sessionId;
  }

  /**
   * Generate new correlation ID for request tracking
   * @returns Unique correlation identifier
   */
  public getNewCorrelationId(): string {
    this.correlationCounter++;
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    return `corr_${timestamp}_${random}_${this.correlationCounter}`;
  }

  /**
   * Get current user ID
   * @returns User identifier if set
   */
  public getUserId(): string | undefined {
    return this.userId;
  }

  /**
   * Set user ID for session
   * @param userId - User identifier to associate with session
   */
  public setUserId(userId: string): void {
    this.userId = userId;
  }

  /**
   * Clear current session and reset state
   */
  public clearSession(): void {
    this.userId = undefined;
    this.correlationCounter = 0;
  }
}

/**
 * Context enrichment utility
 * Adds session data and timing information to log contexts
 * @param additionalContext - Additional context to merge
 * @returns Enriched log context
 */
const enrichContext = (
  additionalContext: Partial<LogContext> = {}
): LogContext => {
  const sessionManager = SessionManagerImpl.getInstance();

  return {
    sessionId: sessionManager.getSessionId(),
    timestamp: new Date().toISOString(),
    userId: sessionManager.getUserId(),
    ...additionalContext,
  };
};

/**
 * Create transport configurations based on environment and settings
 * @param config - Logger configuration
 * @returns Array of transport configurations
 */
const createTransports = (config: LoggerConfig): TransportConfig[] => {
  const transports: TransportConfig[] = [];

  // Console transport for development
  if (config.enableConsoleLogging && config.isDevelopment) {
    transports.push({
      type: "console",
      level: config.level,
      target: "pino-pretty",
      options: {
        colorize: true,
        translateTime: "HH:MM:ss Z",
        ignore: "pid,hostname",
        messageFormat: "[{level}] {msg}",
        levelFirst: true,
      },
    });
  }

  // Console transport for production (JSON format)
  if (config.enableConsoleLogging && !config.isDevelopment) {
    transports.push({
      type: "console",
      level: config.level,
      target: "pino/file",
      options: {
        destination: 1, // stdout
      },
    });
  }

  return transports;
};

/**
 * Create the main Pino logger instance with browser compatibility
 * @param config - Logger configuration
 * @returns Configured Pino logger
 */
const createPinoLogger = (config: LoggerConfig): pino.Logger => {
  const transports = createTransports(config);

  const pinoConfig: pino.LoggerOptions = {
    level: config.level,
    browser: {
      asObject: true,
      serialize: true,
      formatters: {
        level: (
          label: string,
          number: number
        ): { level: string; levelValue: number } => ({
          level: label,
          levelValue: number,
        }),
        log: (obj: Record<string, unknown>): Record<string, unknown> => {
          // Format log object for browser output
          return {
            ...obj,
            timestamp: obj.timestamp || new Date().toISOString(),
          };
        },
      },
    },
    serializers: {
      error: pino.stdSerializers.err,
      request: pino.stdSerializers.req,
      response: pino.stdSerializers.res,
    },
    timestamp: pino.stdTimeFunctions.isoTime,
    formatters: {
      level: (label: string): { level: string } => ({ level: label }),
    },
  };

  // Use transports for Node.js environments (testing/SSR)
  if (typeof window === "undefined" && transports.length > 0) {
    return pino(
      pinoConfig,
      pino.transport({
        targets: transports.map((t) => ({
          level: t.level,
          target: t.target,
          options: t.options,
        })),
      })
    );
  }

  // Browser-only logger
  return pino(pinoConfig);
};

/**
 * Enhanced logger implementation with custom methods for different contexts
 * Provides structured logging with automatic context enrichment
 */
class EnhancedLogger implements AppLogger {
  private readonly baseLogger: pino.Logger;
  private readonly config: LoggerConfig;

  constructor(config: LoggerConfig) {
    this.config = config;
    this.baseLogger = createPinoLogger(config);
  }

  // Expose base logger properties
  public get level(): string {
    return this.baseLogger.level;
  }
  public set level(level: string) {
    this.baseLogger.level = level;
  }

  // Basic logging methods (AppLogger interface)
  public info(message: string, context?: LogContext): void {
    if (context) {
      const enrichedContext = enrichContext(context);
      this.baseLogger.info(enrichedContext, message);
    } else {
      this.baseLogger.info(message);
    }
  }

  public warn(message: string, context?: LogContext): void {
    if (context) {
      const enrichedContext = enrichContext(context);
      this.baseLogger.warn(enrichedContext, message);
    } else {
      this.baseLogger.warn(message);
    }
  }

  public error(message: string, context?: LogContext): void {
    if (context) {
      const enrichedContext = enrichContext(context);
      this.baseLogger.error(enrichedContext, message);
    } else {
      this.baseLogger.error(message);
    }
  }

  public debug(message: string, context?: LogContext): void {
    if (context) {
      const enrichedContext = enrichContext(context);
      this.baseLogger.debug(enrichedContext, message);
    } else {
      this.baseLogger.debug(message);
    }
  }

  // Custom enhanced methods for application-specific logging

  /**
   * Log API call with comprehensive context and performance tracking
   */
  public apiCall(
    context: ApiLogContext,
    message: string,
    data?: unknown
  ): void {
    const enrichedContext = enrichContext(context);
    this.baseLogger.info(
      {
        ...enrichedContext,
        type: "api_call",
        method: context.method,
        url: context.url,
        statusCode: context.statusCode,
        duration: context.duration,
        requestId: context.requestId,
        data,
      },
      message
    );
  }

  /**
   * Log user action with UI context and interaction details
   */
  public userAction(
    context: UILogContext,
    message: string,
    data?: unknown
  ): void {
    const enrichedContext = enrichContext(context);
    this.baseLogger.info(
      {
        ...enrichedContext,
        type: "user_action",
        component: context.component,
        action: context.action,
        elementId: context.elementId,
        elementType: context.elementType,
        route: context.route,
        data,
      },
      message
    );
  }

  /**
   * Log error with comprehensive error context and debugging information
   */
  public errorBoundary(
    context: ErrorLogContext,
    message: string,
    error: Error
  ): void {
    const enrichedContext = enrichContext(context);
    this.baseLogger.error(
      {
        ...enrichedContext,
        type: "error_boundary",
        errorType: context.errorType,
        stackTrace: context.stackTrace || error.stack,
        userAgent:
          context.userAgent ||
          (typeof navigator !== "undefined" ? navigator.userAgent : "unknown"),
        url:
          context.url ||
          (typeof window !== "undefined" ? window.location.href : "unknown"),
        severity: context.severity || "medium",
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
      },
      message
    );
  }

  /**
   * Log performance metrics with timing and resource usage data
   */
  public performance(
    context: PerformanceLogContext,
    message: string,
    metrics: Record<string, number>
  ): void {
    const enrichedContext = enrichContext(context);
    const duration = context.endTime
      ? context.endTime - context.startTime
      : undefined;

    this.baseLogger.info(
      {
        ...enrichedContext,
        type: "performance",
        operation: context.operation,
        startTime: context.startTime,
        endTime: context.endTime,
        duration,
        resourceUsage: context.resourceUsage,
        metrics,
      },
      message
    );
  }

  /**
   * Create a child logger with additional context bindings
   */
  public createChild(bindings: Record<string, unknown>): AppLogger {
    const childPinoLogger = this.baseLogger.child(bindings);
    const childLogger = Object.create(EnhancedLogger.prototype);
    childLogger.baseLogger = childPinoLogger;
    childLogger.config = this.config;
    return childLogger as AppLogger;
  }
}

/**
 * Global logger instance
 */
let loggerInstance: AppLogger | null = null;

/**
 * Get or create the global logger instance
 */
export const getLogger = (
  config?: Partial<CompleteLoggerConfig>
): AppLogger => {
  if (!loggerInstance) {
    const baseConfig = buildConfiguration();
    const finalConfig = { ...baseConfig, ...config };
    loggerInstance = new EnhancedLogger(finalConfig) as AppLogger;
  }
  return loggerInstance;
};

/**
 * Create a child logger with additional context
 * @param bindings - Context to bind to child logger
 * @param config - Optional configuration override
 * @returns Child logger instance
 */
export const createChildLogger = (
  bindings: pino.Bindings,
  config?: Partial<CompleteLoggerConfig>
): AppLogger => {
  const logger = getLogger(config);
  return logger.createChild(bindings);
};

/**
 * Get a new correlation ID for request tracking
 * @returns Unique correlation identifier
 */
export const getNewCorrelationId = (): string => {
  return SessionManagerImpl.getInstance().getNewCorrelationId();
};

/**
 * Get the current session ID
 * @returns Current session identifier
 */
export const getSessionId = (): string => {
  return SessionManagerImpl.getInstance().getSessionId();
};

/**
 * Set user ID for the current session
 * @param userId - User identifier
 */
export const setUserId = (userId: string): void => {
  SessionManagerImpl.getInstance().setUserId(userId);
};

/**
 * Get the current user ID
 * @returns Current user identifier if set
 */
export const getUserId = (): string | undefined => {
  return SessionManagerImpl.getInstance().getUserId();
};

/**
 * Clear the current session
 */
export const clearSession = (): void => {
  SessionManagerImpl.getInstance().clearSession();
};

/**
 * Default export for convenience
 */
const logger = getLogger();
export default logger;

/**
 * Named exports for explicit imports
 */
export { LOG_LEVEL } from "../types/logging";
export type {
  AppLogger,
  LogContext,
  ApiLogContext,
  UILogContext,
  ErrorLogContext,
  PerformanceLogContext,
  LoggerConfig,
} from "../types/logging";
