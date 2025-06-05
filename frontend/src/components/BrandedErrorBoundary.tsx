import type { ReactNode } from "react";
import ErrorBoundary from "./ErrorBoundary";

export const BrandedErrorBoundary: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  return (
    <ErrorBoundary
      fallbackComponent={({ error, retry }) => (
        <div className="min-h-screen bg-ctan-dark-bg flex items-center justify-center">
          <div className="ctan-card p-8 max-w-md text-center">
            <div className="w-16 h-16 mx-auto mb-4 text-ctan-gold ctan-icon">
              {/* Your cat icon */}
            </div>
            <h2 className="text-xl font-bold text-ctan-text-primary mb-2">
              Evolution Interrupted
            </h2>
            <p className="text-ctan-text-secondary mb-4">{error.message}</p>
            <button onClick={retry} className="ctan-button">
              Resume Evolution
            </button>
          </div>
        </div>
      )}
    >
      {children}
    </ErrorBoundary>
  );
};
