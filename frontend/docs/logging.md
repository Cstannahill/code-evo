# Pino Logging Implementation Guide

## Overview

This document outlines the comprehensive implementation of a production-ready Pino-based logging system for the Code Evolution Tracker frontend. The logging system provides structured logging, error handling, file rotation, and observability for React components and API interactions.

## Architecture

### Core Components

1. **Central Logger** (`src/lib/logger.ts`) - Main logging configuration and factory
2. **Type Definitions** (`src/types/logging.ts`) - TypeScript interfaces and types
3. **API Logging** - Decorators for existing API client methods
4. **UI Logging** - React hook (`useLogger`) for component-level logging
5. **File Management** - Hourly rotation with separate streams
6. **Error Enhancement** - Enhanced ErrorBoundary with structured logging

### Log Levels and Usage

```typescript
// Log Levels (in order of severity)
- debug: Development debugging, verbose output
- info: General information, user actions, API responses
- warn: Deprecation warnings, performance concerns
- error: Exceptions, API failures, critical issues
```

### File Structure

```
frontend/
├── src/
│   ├── lib/
│   │   └── logger.ts           # Core logger implementation
│   ├── types/
│   │   └── logging.ts          # TypeScript definitions
│   ├── hooks/
│   │   └── useLogger.ts        # React logging hook
│   ├── api/
│   │   └── client.ts           # Enhanced with logging
│   └── components/
│       └── ErrorBoundary.tsx   # Enhanced error handling
├── logs/                       # Log output directory
│   ├── api.log                 # API interaction logs
│   ├── ui.log                  # UI component logs
│   ├── errors.log              # Error-only logs
│   └── debug.log               # Development debugging
└── docs/
    └── logging.md              # This documentation
```

## Implementation Plan

### Phase 1: Package Installation and Configuration

#### Step 1.1: Install Required Packages

```bash
npm install pino pino-web pino-pretty pino-transport
npm install -D @types/pino
```

#### Step 1.2: Vite Configuration Updates

Update `vite.config.ts` for browser compatibility:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  define: {
    global: "globalThis",
  },
  resolve: {
    alias: {
      stream: "stream-browserify",
      util: "util",
    },
  },
  optimizeDeps: {
    include: ["pino", "pino-web"],
  },
});
```

### Phase 2: Core Implementation

#### Step 2.1: Type Definitions (`src/types/logging.ts`)

```typescript
import type { Logger as PinoLogger } from "pino";

/**
 * Log levels supported by the application
 */
export enum LOG_LEVEL {
  DEBUG = "debug",
  INFO = "info",
  WARN = "warn",
  ERROR = "error",
}

/**
 * Log context for enriching log entries
 */
export interface LogContext {
  readonly userId?: string;
  readonly sessionId: string;
  readonly correlationId?: string;
  readonly component?: string;
  readonly action?: string;
  readonly timestamp: string;
}

/**
 * API logging context
 */
export interface ApiLogContext extends LogContext {
  readonly method: string;
  readonly url: string;
  readonly statusCode?: number;
  readonly duration?: number;
}

/**
 * UI logging context
 */
export interface UILogContext extends LogContext {
  readonly component: string;
  readonly action: string;
  readonly elementId?: string;
  readonly elementType?: string;
}

/**
 * Error logging context
 */
export interface ErrorLogContext extends LogContext {
  readonly errorType: string;
  readonly stackTrace?: string;
  readonly userAgent?: string;
  readonly url?: string;
}

/**
 * Logger configuration
 */
export interface LoggerConfig {
  readonly level: LOG_LEVEL;
  readonly isDevelopment: boolean;
  readonly enableFileLogging: boolean;
  readonly enableConsoleLogging: boolean;
  readonly fileRotationHours: number;
}

/**
 * Extended Pino logger with custom methods
 */
export interface AppLogger extends PinoLogger {
  apiCall: (context: ApiLogContext, message: string, data?: unknown) => void;
  userAction: (context: UILogContext, message: string, data?: unknown) => void;
  errorBoundary: (
    context: ErrorLogContext,
    message: string,
    error: Error
  ) => void;
  performance: (
    context: LogContext,
    message: string,
    metrics: Record<string, number>
  ) => void;
}

/**
 * Log transport configuration
 */
export interface TransportConfig {
  readonly type: "file" | "console";
  readonly level: LOG_LEVEL;
  readonly target: string;
  readonly options?: Record<string, unknown>;
}
```

#### Step 2.2: Core Logger Implementation (`src/lib/logger.ts`)

```typescript
import pino from "pino";
import type {
  AppLogger,
  LoggerConfig,
  LogContext,
  ApiLogContext,
  UILogContext,
  ErrorLogContext,
  TransportConfig,
  LOG_LEVEL,
} from "../types/logging";

/**
 * Default logger configuration
 */
const DEFAULT_CONFIG: LoggerConfig = {
  level: (import.meta.env.VITE_LOG_LEVEL as LOG_LEVEL) || LOG_LEVEL.INFO,
  isDevelopment: import.meta.env.DEV,
  enableFileLogging: import.meta.env.VITE_ENABLE_FILE_LOGGING === "true",
  enableConsoleLogging: true,
  fileRotationHours: 1,
};

/**
 * Generate session ID for tracking user sessions
 */
const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Generate correlation ID for request tracking
 */
const generateCorrelationId = (): string => {
  return `corr_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Session tracking
 */
class SessionManager {
  private static instance: SessionManager;
  private readonly sessionId: string;
  private correlationCounter: number = 0;

  private constructor() {
    this.sessionId = generateSessionId();
  }

  public static getInstance(): SessionManager {
    if (!SessionManager.instance) {
      SessionManager.instance = new SessionManager();
    }
    return SessionManager.instance;
  }

  public getSessionId(): string {
    return this.sessionId;
  }

  public getNewCorrelationId(): string {
    this.correlationCounter++;
    return `${generateCorrelationId()}_${this.correlationCounter}`;
  }
}

/**
 * Base context enrichment
 */
const enrichContext = (
  additionalContext: Partial<LogContext> = {}
): LogContext => {
  const sessionManager = SessionManager.getInstance();

  return {
    sessionId: sessionManager.getSessionId(),
    timestamp: new Date().toISOString(),
    ...additionalContext,
  };
};

/**
 * Create transport configurations based on environment
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
      },
    });
  }

  // File transports for production
  if (config.enableFileLogging) {
    // General application logs
    transports.push({
      type: "file",
      level: LOG_LEVEL.INFO,
      target: "pino/file",
      options: {
        destination: "./logs/app.log",
        mkdir: true,
      },
    });

    // API-specific logs
    transports.push({
      type: "file",
      level: LOG_LEVEL.DEBUG,
      target: "pino/file",
      options: {
        destination: "./logs/api.log",
        mkdir: true,
      },
    });

    // Error-only logs
    transports.push({
      type: "file",
      level: LOG_LEVEL.ERROR,
      target: "pino/file",
      options: {
        destination: "./logs/errors.log",
        mkdir: true,
      },
    });

    // UI interaction logs
    transports.push({
      type: "file",
      level: LOG_LEVEL.INFO,
      target: "pino/file",
      options: {
        destination: "./logs/ui.log",
        mkdir: true,
      },
    });
  }

  return transports;
};

/**
 * Create the main Pino logger instance
 */
const createPinoLogger = (
  config: LoggerConfig = DEFAULT_CONFIG
): pino.Logger => {
  const transports = createTransports(config);

  const pinoConfig: pino.LoggerOptions = {
    level: config.level,
    browser: {
      asObject: true,
      serialize: true,
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

  // Use transports only in Node.js environment (for file logging)
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
 * Enhanced logger with custom methods
 */
class EnhancedLogger implements AppLogger {
  private readonly baseLogger: pino.Logger;
  private readonly config: LoggerConfig;

  constructor(config: LoggerConfig = DEFAULT_CONFIG) {
    this.config = config;
    this.baseLogger = createPinoLogger(config);
  }

  // Standard Pino methods delegation
  public get level(): string {
    return this.baseLogger.level;
  }
  public set level(level: string) {
    this.baseLogger.level = level;
  }

  public fatal(obj: unknown, msg?: string, ...args: unknown[]): void;
  public fatal(msg: string, ...args: unknown[]): void;
  public fatal(...args: unknown[]): void {
    // @ts-expect-error - Pino overloads are complex
    this.baseLogger.fatal(...args);
  }

  public error(obj: unknown, msg?: string, ...args: unknown[]): void;
  public error(msg: string, ...args: unknown[]): void;
  public error(...args: unknown[]): void {
    // @ts-expect-error - Pino overloads are complex
    this.baseLogger.error(...args);
  }

  public warn(obj: unknown, msg?: string, ...args: unknown[]): void;
  public warn(msg: string, ...args: unknown[]): void;
  public warn(...args: unknown[]): void {
    // @ts-expect-error - Pino overloads are complex
    this.baseLogger.warn(...args);
  }

  public info(obj: unknown, msg?: string, ...args: unknown[]): void;
  public info(msg: string, ...args: unknown[]): void;
  public info(...args: unknown[]): void {
    // @ts-expect-error - Pino overloads are complex
    this.baseLogger.info(...args);
  }

  public debug(obj: unknown, msg?: string, ...args: unknown[]): void;
  public debug(msg: string, ...args: unknown[]): void;
  public debug(...args: unknown[]): void {
    // @ts-expect-error - Pino overloads are complex
    this.baseLogger.debug(...args);
  }

  public trace(obj: unknown, msg?: string, ...args: unknown[]): void;
  public trace(msg: string, ...args: unknown[]): void;
  public trace(...args: unknown[]): void {
    // @ts-expect-error - Pino overloads are complex
    this.baseLogger.trace(...args);
  }

  public silent(): never {
    return this.baseLogger.silent();
  }

  public child(bindings: pino.Bindings): pino.Logger {
    return this.baseLogger.child(bindings);
  }

  public bindings(): pino.Bindings {
    return this.baseLogger.bindings();
  }

  public flush(): void {
    this.baseLogger.flush();
  }

  public isLevelEnabled(level: pino.LevelWithSilent): boolean {
    return this.baseLogger.isLevelEnabled(level);
  }

  // Custom enhanced methods
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
        data,
      },
      message
    );
  }

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
        data,
      },
      message
    );
  }

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
        userAgent: context.userAgent || navigator.userAgent,
        url: context.url || window.location.href,
        error,
      },
      message
    );
  }

  public performance(
    context: LogContext,
    message: string,
    metrics: Record<string, number>
  ): void {
    const enrichedContext = enrichContext(context);
    this.baseLogger.info(
      {
        ...enrichedContext,
        type: "performance",
        metrics,
      },
      message
    );
  }
}

/**
 * Global logger instance
 */
let loggerInstance: AppLogger | null = null;

/**
 * Get or create the global logger instance
 */
export const getLogger = (config?: Partial<LoggerConfig>): AppLogger => {
  if (!loggerInstance) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };
    loggerInstance = new EnhancedLogger(finalConfig);
  }
  return loggerInstance;
};

/**
 * Create a child logger with additional context
 */
export const createChildLogger = (
  bindings: pino.Bindings,
  config?: Partial<LoggerConfig>
): pino.Logger => {
  const logger = getLogger(config);
  return logger.child(bindings);
};

/**
 * Get a new correlation ID for request tracking
 */
export const getNewCorrelationId = (): string => {
  return SessionManager.getInstance().getNewCorrelationId();
};

/**
 * Get the current session ID
 */
export const getSessionId = (): string => {
  return SessionManager.getInstance().getSessionId();
};

/**
 * Default export for convenience
 */
export default getLogger();
```

### Phase 3: React Integration

#### Step 3.1: Logger Hook (`src/hooks/useLogger.ts`)

````typescript
import { useCallback, useMemo } from "react";
import type { AppLogger, UILogContext } from "../types/logging";
import { getLogger, getNewCorrelationId } from "../lib/logger";

/**
 * Hook configuration options
 */
interface UseLoggerOptions {
  readonly component: string;
  readonly enableDebug?: boolean;
}

/**
 * Hook return type
 */
interface UseLoggerReturn {
  readonly logger: AppLogger;
  readonly logUserAction: (
    action: string,
    data?: unknown,
    elementId?: string,
    elementType?: string
  ) => void;
  readonly logPerformance: (
    operation: string,
    metrics: Record<string, number>
  ) => void;
  readonly logError: (error: Error, context?: string) => void;
  readonly createCorrelationId: () => string;
}

/**
 * React hook for component-level logging
 *
 * @param options - Configuration options for the logger
 * @returns Logger utilities for the component
 *
 * @example
 * ```typescript
 * const { logUserAction, logError } = useLogger({
 *   component: 'UserProfile'
 * })
 *
 * const handleButtonClick = () => {
 *   logUserAction('profile_save', { userId: user.id })
 *   // ... rest of handler
 * }
 * ```
 */
export const useLogger = (options: UseLoggerOptions): UseLoggerReturn => {
  const { component, enableDebug = false } = options;

  const logger = useMemo(() => getLogger(), []);

  const logUserAction = useCallback(
    (
      action: string,
      data?: unknown,
      elementId?: string,
      elementType?: string
    ): void => {
      const context: UILogContext = {
        sessionId: "", // Will be enriched by logger
        timestamp: "", // Will be enriched by logger
        component,
        action,
        elementId,
        elementType,
        correlationId: getNewCorrelationId(),
      };

      logger.userAction(
        context,
        `User action: ${action} in ${component}`,
        data
      );

      if (enableDebug) {
        logger.debug(
          {
            component,
            action,
            data,
            elementId,
            elementType,
          },
          `[DEBUG] User action logged`
        );
      }
    },
    [logger, component, enableDebug]
  );

  const logPerformance = useCallback(
    (operation: string, metrics: Record<string, number>): void => {
      const context = {
        sessionId: "", // Will be enriched by logger
        timestamp: "", // Will be enriched by logger
        component,
        correlationId: getNewCorrelationId(),
      };

      logger.performance(
        context,
        `Performance: ${operation} in ${component}`,
        metrics
      );

      if (enableDebug) {
        logger.debug(
          {
            component,
            operation,
            metrics,
          },
          `[DEBUG] Performance metrics logged`
        );
      }
    },
    [logger, component, enableDebug]
  );

  const logError = useCallback(
    (error: Error, context?: string): void => {
      const errorContext = {
        sessionId: "", // Will be enriched by logger
        timestamp: "", // Will be enriched by logger
        component,
        errorType: error.name,
        stackTrace: error.stack,
        correlationId: getNewCorrelationId(),
      };

      const message = context
        ? `Error in ${component} - ${context}: ${error.message}`
        : `Error in ${component}: ${error.message}`;

      logger.errorBoundary(errorContext, message, error);

      if (enableDebug) {
        logger.debug(
          {
            component,
            error: error.message,
            context,
          },
          `[DEBUG] Error logged`
        );
      }
    },
    [logger, component, enableDebug]
  );

  const createCorrelationId = useCallback((): string => {
    return getNewCorrelationId();
  }, []);

  return {
    logger,
    logUserAction,
    logPerformance,
    logError,
    createCorrelationId,
  };
};

export default useLogger;
````

### Phase 4: API Integration

#### Step 4.1: Enhanced API Client

The existing `src/api/client.ts` will be enhanced with logging decorators. Example implementation:

```typescript
// This will be added to the existing API client
import type { ApiLogContext } from "../types/logging";
import { getLogger, getNewCorrelationId } from "../lib/logger";

const logger = getLogger();

/**
 * API logging decorator
 */
const withLogging = <T extends (...args: any[]) => Promise<any>>(
  originalMethod: T,
  methodName: string
): T => {
  return (async (...args: Parameters<T>): Promise<ReturnType<T>> => {
    const correlationId = getNewCorrelationId();
    const startTime = performance.now();

    const context: Partial<ApiLogContext> = {
      correlationId,
      method: methodName,
      url: args[0] || "unknown",
    };

    logger.debug(context, `API call started: ${methodName}`);

    try {
      const result = await originalMethod(...args);
      const duration = performance.now() - startTime;

      const successContext: ApiLogContext = {
        ...context,
        sessionId: "", // Will be enriched
        timestamp: "", // Will be enriched
        method: methodName,
        url: context.url!,
        statusCode: result?.status || 200,
        duration,
      };

      logger.apiCall(successContext, `API call successful: ${methodName}`, {
        duration,
        requestArgs: args,
        responseSize: JSON.stringify(result).length,
      });

      return result;
    } catch (error) {
      const duration = performance.now() - startTime;
      const errorContext: ApiLogContext = {
        ...context,
        sessionId: "", // Will be enriched
        timestamp: "", // Will be enriched
        method: methodName,
        url: context.url!,
        statusCode: (error as any)?.status || 500,
        duration,
      };

      logger.apiCall(errorContext, `API call failed: ${methodName}`, {
        error: (error as Error).message,
        duration,
        requestArgs: args,
      });

      throw error;
    }
  }) as T;
};

// Example usage with existing API methods:
// export const fetchProjects = withLogging(originalFetchProjects, 'fetchProjects')
```

### Phase 5: Error Boundary Enhancement

#### Step 5.1: Enhanced Error Boundary

The existing `src/components/ErrorBoundary.tsx` will be enhanced:

```typescript
// Additions to existing ErrorBoundary component
import { useLogger } from "../hooks/useLogger";
import type { ErrorLogContext } from "../types/logging";

// Add to existing ErrorBoundary component:
const { logError } = useLogger({ component: "ErrorBoundary" });

// In componentDidCatch method:
const errorContext: ErrorLogContext = {
  sessionId: "", // Will be enriched
  timestamp: "", // Will be enriched
  errorType: error.name,
  stackTrace: errorInfo.componentStack,
  userAgent: navigator.userAgent,
  url: window.location.href,
};

logError(error, `Component error boundary triggered`);
```

## Testing Strategy

### Unit Tests

```typescript
// tests/logger.test.ts
describe("Logger Implementation", () => {
  test("should create logger with correct configuration", () => {
    // Test logger creation
  });

  test("should enrich context correctly", () => {
    // Test context enrichment
  });

  test("should handle API logging", () => {
    // Test API logging decorator
  });

  test("should track user actions", () => {
    // Test useLogger hook
  });
});
```

### Integration Tests

```typescript
// tests/integration/logging.test.ts
describe("Logging Integration", () => {
  test("should log complete user journey", () => {
    // Test end-to-end logging flow
  });

  test("should handle error scenarios", () => {
    // Test error logging and recovery
  });
});
```

### Performance Tests

```typescript
// tests/performance/logging.test.ts
describe("Logging Performance", () => {
  test("should not impact application performance", () => {
    // Benchmark logging overhead
  });

  test("should handle high-frequency logging", () => {
    // Test under load
  });
});
```

## Configuration

### Environment Variables

```bash
# .env.development
VITE_LOG_LEVEL=debug
VITE_ENABLE_FILE_LOGGING=false
VITE_ENABLE_CONSOLE_LOGGING=true

# .env.production
VITE_LOG_LEVEL=info
VITE_ENABLE_FILE_LOGGING=true
VITE_ENABLE_CONSOLE_LOGGING=false
```

### Production Configuration

```typescript
// Production-specific configuration
const PRODUCTION_CONFIG: LoggerConfig = {
  level: LOG_LEVEL.INFO,
  isDevelopment: false,
  enableFileLogging: true,
  enableConsoleLogging: false,
  fileRotationHours: 1,
};
```

## Monitoring and Observability

### Log Analysis

1. **Correlation Tracking**: Each request gets a unique correlation ID
2. **Session Tracking**: User sessions are tracked across interactions
3. **Performance Metrics**: API response times and UI interaction latencies
4. **Error Patterns**: Structured error logging for pattern analysis

### Dashboard Integration

The logs can be integrated with external monitoring tools:

- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Splunk**: Enterprise log analysis
- **DataDog**: Application monitoring
- **Custom Dashboards**: Using log file analysis

## Maintenance

### Log Rotation

- Hourly rotation for all log files
- Separate streams for different log types
- Configurable retention policies
- Automated cleanup of old log files

### Performance Monitoring

- Regular performance impact assessment
- Log volume monitoring
- Storage usage tracking
- Network impact analysis for remote logging

## Security Considerations

### Data Protection

- No sensitive data in logs (passwords, tokens, PII)
- Configurable data masking
- Secure log storage and transmission
- Access controls for log files

### Compliance

- GDPR compliance for user data logging
- Retention policy adherence
- Audit trail maintenance
- Privacy-first logging approach

## Conclusion

This comprehensive Pino logging implementation provides production-ready observability for the Code Evolution Tracker frontend. The system balances performance, functionality, and maintainability while providing deep insights into application behavior and user interactions.

The implementation follows TypeScript best practices, React patterns, and modern logging standards to ensure reliability and ease of maintenance.
