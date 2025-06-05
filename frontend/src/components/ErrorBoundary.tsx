import React, { type ErrorInfo, type ReactNode } from "react";
import logger from "../lib/logger";

interface Props {
  children: ReactNode;
  fallbackComponent?: React.ComponentType<{ error: Error; retry: () => void }>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
}

class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorInfo: null,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const errorId = `error_${Date.now()}_${Math.random()
      .toString(36)
      .substr(2, 9)}`;

    this.setState({
      error,
      errorInfo,
      errorId,
      retryCount: this.state.retryCount + 1,
    });

    // Enhanced structured error logging
    logger.error("React Error Boundary caught error", {
      errorId,
      component: "ErrorBoundary",
      componentStack: errorInfo.componentStack,
      retryCount: this.state.retryCount,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      error: error.message,
      errorStack: error.stack,
      errorInfo: {
        componentStack: errorInfo.componentStack,
        errorBoundary: true,
      },
    });

    // Call optional error handler prop
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log additional context for debugging
    logger.debug("Error Boundary State", {
      errorId,
      hasError: true,
      retryCount: this.state.retryCount,
      component: "ErrorBoundary",
    });
  }

  private handleRetry = () => {
    logger.info("Error Boundary retry attempted", {
      errorId: this.state.errorId,
      retryCount: this.state.retryCount,
      component: "ErrorBoundary",
    });

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback component if provided
      if (this.props.fallbackComponent) {
        const FallbackComponent = this.props.fallbackComponent;
        return (
          <FallbackComponent
            error={this.state.error!}
            retry={this.handleRetry}
          />
        );
      }

      // Default error UI
      return (
        <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          <h1 className="text-lg font-bold">Something went wrong.</h1>
          <p className="mt-2 text-sm">
            Error ID:{" "}
            <code className="font-mono text-xs">{this.state.errorId}</code>
          </p>
          <details className="mt-2 whitespace-pre-wrap">
            {this.state.error && this.state.error.toString()}
            <br />
            {this.state.errorInfo && this.state.errorInfo.componentStack}
          </details>
          {process.env.NODE_ENV === "development" && (
            <div className="mt-4 space-x-2">
              <button
                onClick={this.handleRetry}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-700"
              >
                Try again ({this.state.retryCount} retries)
              </button>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(
                    JSON.stringify(
                      {
                        error: this.state.error?.toString(),
                        stack: this.state.error?.stack,
                        componentStack: this.state.errorInfo?.componentStack,
                        errorId: this.state.errorId,
                      },
                      null,
                      2
                    )
                  );
                  logger.info("Error details copied to clipboard", {
                    errorId: this.state.errorId,
                    component: "ErrorBoundary",
                  });
                }}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-700"
              >
                Copy Error Details
              </button>
            </div>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
