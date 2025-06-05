/**
 * @fileoverview TypeScript definitions for the Pino logging system
 * Provides comprehensive type safety for all logging contexts and configurations
 */

/**
 * Log levels supported by the application
 * Ordered by severity: debug < info < warn < error
 */
export const LOG_LEVEL = {
  DEBUG: "debug",
  INFO: "info",
  WARN: "warn",
  ERROR: "error",
} as const;

export type LogLevel = (typeof LOG_LEVEL)[keyof typeof LOG_LEVEL];

/**
 * Base log context for enriching log entries with session and timing data
 */
export interface LogContext {
  readonly userId?: string;
  readonly sessionId?: string;
  readonly correlationId?: string;
  readonly component?: string;
  readonly action?: string;
  readonly timestamp?: string;
  // Allow additional custom properties
  readonly [key: string]: unknown;
}

/**
 * API logging context with HTTP-specific information
 * Used for tracking API requests, responses, and performance metrics
 */
export interface ApiLogContext extends LogContext {
  readonly method: string;
  readonly url: string;
  readonly statusCode?: number;
  readonly duration?: number;
  readonly requestId?: string;
}

/**
 * UI logging context for component interactions and user actions
 * Captures user behavior and component-level events
 */
export interface UILogContext extends LogContext {
  readonly component: string;
  readonly action: string;
  readonly elementId?: string;
  readonly elementType?: string;
  readonly route?: string;
}

/**
 * Error logging context with comprehensive error information
 * Includes stack traces, user environment, and error categorization
 */
export interface ErrorLogContext extends LogContext {
  readonly errorType: string;
  readonly stackTrace?: string;
  readonly userAgent?: string;
  readonly url?: string;
  readonly severity?: "low" | "medium" | "high" | "critical";
}

/**
 * Performance logging context for timing and metrics
 * Tracks application performance and resource usage
 */
export interface PerformanceLogContext extends LogContext {
  readonly operation: string;
  readonly startTime: number;
  readonly endTime?: number;
  readonly resourceUsage?: Record<string, number>;
}

/**
 * Additional types for React hooks and components
 */
export interface ComponentProps {
  readonly [key: string]: unknown;
}

export interface UserActionContext extends UILogContext {
  readonly userTriggered?: boolean;
}

export interface PerformanceContext extends PerformanceLogContext {
  readonly componentName?: string;
}

/**
 * Logger configuration for environment-specific settings
 */
export interface LoggerConfig {
  readonly level: LogLevel;
  readonly isDevelopment: boolean;
  readonly enableFileLogging: boolean;
  readonly enableConsoleLogging: boolean;
  readonly fileRotationHours: number;
  readonly maxFileSize?: number;
  readonly enableCorrelationTracking: boolean;
}

/**
 * Enhanced logger interface with custom application-specific methods
 * Provides typed logging methods for different contexts
 */
export interface AppLogger {
  // Basic logging methods
  info: (message: string, context?: LogContext) => void;
  warn: (message: string, context?: LogContext) => void;
  error: (message: string, context?: LogContext) => void;
  debug: (message: string, context?: LogContext) => void;

  // Enhanced context-specific methods
  apiCall: (context: ApiLogContext, message: string, data?: unknown) => void;
  userAction: (context: UILogContext, message: string, data?: unknown) => void;
  errorBoundary: (
    context: ErrorLogContext,
    message: string,
    error: Error
  ) => void;
  performance: (
    context: PerformanceLogContext,
    message: string,
    metrics: Record<string, number>
  ) => void;

  // Child logger creation
  createChild: (bindings: Record<string, unknown>) => AppLogger;
}

/**
 * Log transport configuration for different output targets
 */
export interface TransportConfig {
  readonly type: "file" | "console";
  readonly level: LogLevel;
  readonly target: string;
  readonly options?: Record<string, unknown>;
}

/**
 * Log entry structure for consistent log formatting
 */
export interface LogEntry {
  readonly level: LogLevel;
  readonly timestamp: string;
  readonly message: string;
  readonly context: LogContext;
  readonly data?: unknown;
  readonly type:
    | "api_call"
    | "user_action"
    | "error_boundary"
    | "performance"
    | "general";
}

/**
 * Session management interface for tracking user sessions
 */
export interface SessionManager {
  getSessionId(): string;
  getNewCorrelationId(): string;
  getUserId(): string | undefined;
  setUserId(userId: string): void;
  clearSession(): void;
}

/**
 * Log aggregation configuration for batching and performance
 */
export interface LogAggregationConfig {
  readonly batchSize: number;
  readonly flushInterval: number;
  readonly enableBatching: boolean;
  readonly bufferSize: number;
}

/**
 * Log filter configuration for controlling what gets logged
 */
export interface LogFilterConfig {
  readonly excludeRoutes?: string[];
  readonly excludeComponents?: string[];
  readonly includeOnlyLevels?: LogLevel[];
  readonly enableSampling?: boolean;
  readonly samplingRate?: number;
}

/**
 * Complete logging system configuration
 */
export interface CompleteLoggerConfig extends LoggerConfig {
  readonly aggregation?: LogAggregationConfig;
  readonly filtering?: LogFilterConfig;
  readonly transports?: TransportConfig[];
}

/**
 * Logger factory function type
 */
export type LoggerFactory = (
  config?: Partial<CompleteLoggerConfig>
) => AppLogger;

/**
 * Log level mapping for runtime configuration
 */
export const LOG_LEVEL_MAP: Record<string, LogLevel> = {
  debug: LOG_LEVEL.DEBUG,
  info: LOG_LEVEL.INFO,
  warn: LOG_LEVEL.WARN,
  error: LOG_LEVEL.ERROR,
} as const;

/**
 * Default configuration constants
 */
export const DEFAULT_LOGGER_CONFIG: LoggerConfig = {
  level: LOG_LEVEL.INFO,
  isDevelopment: false,
  enableFileLogging: true,
  enableConsoleLogging: false,
  fileRotationHours: 1,
  enableCorrelationTracking: true,
} as const;

/**
 * Environment variable keys for logger configuration
 */
export const LOGGER_ENV_KEYS = {
  LOG_LEVEL: "VITE_LOG_LEVEL",
  ENABLE_FILE_LOGGING: "VITE_ENABLE_FILE_LOGGING",
  ENABLE_CONSOLE_LOGGING: "VITE_ENABLE_CONSOLE_LOGGING",
  FILE_ROTATION_HOURS: "VITE_FILE_ROTATION_HOURS",
} as const;

/**
 * Type guards for runtime type checking
 */
export const isLogLevel = (value: string): value is LogLevel => {
  return Object.values(LOG_LEVEL).includes(value as LogLevel);
};

export const isApiLogContext = (
  context: LogContext
): context is ApiLogContext => {
  return "method" in context && "url" in context;
};

export const isUILogContext = (
  context: LogContext
): context is UILogContext => {
  return "component" in context && "action" in context;
};

export const isErrorLogContext = (
  context: LogContext
): context is ErrorLogContext => {
  return "errorType" in context;
};

export const isPerformanceLogContext = (
  context: LogContext
): context is PerformanceLogContext => {
  return "operation" in context && "startTime" in context;
};
