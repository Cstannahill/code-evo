import React from "react";

/**
 * MAHeader - Header for MultiAnalysisDashboard
 * Renders the main title and subtitle for the dashboard.
 */
export const MAHeader: React.FC = () => (
    <header className="mb-12 text-center">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4 brand-title">
            Code Evolution
        </h1>
        <p className="text-lg text-ctan-text-secondary">
            AI-powered repository analysis to understand your coding journey
        </p>
    </header>
);
