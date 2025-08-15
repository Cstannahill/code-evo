# Frontend Directory Documentation

This document provides a detailed overview of each directory within the `frontend/` folder, based strictly on the actual code present. No assumptions or inferences are made; all descriptions are derived from the codebase itself.

---

## src/

- **Purpose:** Main source directory for all frontend logic, UI, state management, and API integration.

### App.tsx

- **Purpose:** Root React component; orchestrates app layout, status bar, and dashboard rendering.
- **Usage:** Entry point for rendering, health checks, and theme toggling.
- **Flows:** Loads dashboard, checks backend/AI status, manages global error boundaries.

### api/

- **Purpose:** API client logic for communicating with backend endpoints.
- **Usage:** Used by hooks and components to fetch, create, and update repositories, models, and analysis results.
- **Flows:** Handles REST calls, model selection, analytics tracking, and error handling.

### assets/

- **Purpose:** Static assets (SVGs, images) for UI branding and icons.
- **Key Files:**
  - `react.svg`: React logo for branding and UI.
- **Usage:** Imported by UI components for icons and visuals.
- **Flows:** Supports branded UI and visual elements throughout the app.

### components/

- **Purpose:** Reusable React components for UI, error handling, loaders, dashboards, and model selection.
- **Usage:** Used throughout the app for layout, error boundaries, branded loaders, and feature dashboards.
- **Flows:** Central to rendering analysis dashboards, model selection, error handling, and branded UI.

### contexts/

- **Purpose:** React context providers for global state management (e.g., theme).
- **Key Files:**
  - `ThemeContext.tsx`: Theme context provider for light/dark mode and theme toggling.
- **Usage:** Used by App and UI components to provide and consume global state.
- **Flows:** Enables consistent theme management and global state sharing across the app.

### styles/

- **Purpose:** CSS files for branding, theming, and UI styling.
- **Key Files:**
  - `ctan-brand.css`: Main branding and theme styles for the app.
- **Usage:** Imported by components and dashboards for consistent look and feel.
- **Flows:** Ensures visual consistency and brand identity across all UI modules.

### hooks/

- **Purpose:** Custom React hooks for data fetching, state management, polling, and logging.
- **Key Files:**
  - `useRepository.ts`: Manages repository creation, polling, and mutation flows.
  - `useRepositoryAnalysis.ts`: Fetches and manages analysis results for repositories.
  - `useRepositoryPatterns.ts`: Retrieves detected code patterns for a repository.
  - `useModelAvailability.ts`: Checks and tracks available AI models for analysis.
  - `useEnhancedAnalysis.ts`: Handles enhanced analysis flows and results.
  - `useDebugApi.ts`: Debugging and test API calls for development.
  - `useChartData.ts`: Prepares and transforms data for chart components.
  - `useLogger.ts`: Provides structured logging for UI and API events.
  - `useTransformAnalysis.ts`: Transforms raw analysis data for visualization and insights.
- **Usage:** Used by feature dashboards and components to orchestrate API calls, polling, state updates, and logging.
- **Flows:** Central to repository lifecycle, analysis polling, model selection, and analytics tracking.

### features/

- **Purpose:** High-level dashboard and feature modules for repository analysis, code quality, insights, patterns, and technology timelines.
- **Key Files:**
  - `AnalysisDashboard.tsx`: Main dashboard for repository/code analysis, metrics, and visualizations.
  - `MultiAnalysisDashboard.tsx`: Dashboard for multi-model analysis, comparison, and consensus scoring.
  - `CodeQualityDashboard.tsx`: Displays code quality, security, and performance metrics.
  - `InsightsDashboard.tsx`: Aggregates insights, recommendations, and learning paths.
  - `PatternDeepDive.tsx`: In-depth pattern analysis and visualization.
  - `TechnologyTimeline.tsx`: Timeline of technology and commit evolution.
  - Subfolders:
    - `multi-analysis/`: Modular components for multi-model workflows (e.g., MAHeader, MAAnalysisModeTabs, MASingleAnalysisSection, MACompareAnalysisSection, MARepositoryList, MAResultsSection).
    - `insights/`: Modular components for insights (e.g., AISummaryCard, InsightCard, InsightsCategorySection, InsightsSummary, LearningPathSection).
- **Usage:** Main entry points for user-facing dashboards and analysis flows.
- **Flows:** Orchestrate repository analysis, model comparison, insights, pattern deep dives, and technology evolution tracking.

### lib/

- **Purpose:** Core utilities and logging implementation (Pino) for structured logging, analytics, and helper functions.
- **Key Files:**
  - `logger.ts`: Central Pino logger implementation with session tracking, correlation IDs, and structured logging for API/UI/errors/performance.
  - `analytics.ts`: Analytics tracking for user actions and model selection.
  - `utils.ts`: General-purpose utility functions for data transformation and helpers.
- **Usage:** Used by hooks, components, and API client for logging, analytics, and utility operations.
- **Flows:** Provides logging for API calls, UI actions, error boundaries, and performance metrics; supports analytics and utility needs across the app.

### types/

- **Purpose:** TypeScript type definitions for API contracts, models, logging, analysis, and insights.
- **Key Files:**
  - `api.ts`: API request/response types for repositories, analysis, patterns, technologies, etc.
  - `ai.ts`: AI model definitions and default model registry.
  - `model.ts`: Core AIModel interface and related types.
  - `analysis.ts`: Types for code analysis, quality, and pattern statistics.
  - `insights.ts`: Types for insights, recommendations, and learning paths.
  - `logging.ts`: Logger configuration, log context, and log level types.
  - `axios.d.ts`: Axios type augmentation for API client.
- **Usage:** Used throughout the app for type safety, contract enforcement, and code intelligence.
- **Flows:** Ensures strict typing for API, models, analysis, logging, and insights across all modules.

### main.tsx

- **Purpose:** React app bootstrap and rendering.
- **Usage:** Mounts the root App component.

---

## public/

- **Purpose:** Static files for favicon, manifest, icons, and PWA support.
- **Key Files:**
  - `favicon-16.png`, `favicon-32.png`: Favicons for browser tabs.
  - `manifest.json`: PWA manifest for app metadata and icons.
  - `apple-touch-icon.png`, `ctan-icon*.png`, `vite.svg`: App and brand icons for various platforms.
- **Usage:** Used by browser, PWA, and OS for branding and app metadata.
- **Flows:** Supports PWA installation, browser tab icons, and platform-specific branding.

---

## docs/

- **Purpose:** Project documentation, architecture guides, and implementation details.
- **Key Files:**
  - `logging.md`: Comprehensive guide to Pino logging implementation, architecture, and usage.
- **Usage:** Reference for developers on logging, architecture, and best practices.
- **Flows:** Supports onboarding, troubleshooting, and architectural decisions.

---

## index.html

- **Purpose:** Main HTML entry point for the Vite/React app.
- **Usage:** Loads the React app, links to scripts, styles, and icons.
- **Flows:** Bootstraps the frontend application and provides the root DOM node for React rendering.

---

## Configuration Files

- **Purpose:** Project configuration for dependencies, build, linting, TypeScript, and styling.
- **Key Files:**
  - `package.json`: Declares dependencies (React, TanStack Query, Radix UI, Pino, Tailwind, etc.), scripts for dev/build/lint.
  - `vite.config.ts`: Vite build and dev server configuration.
  - `tailwind.config.js`: Tailwind CSS configuration for theming and utility classes.
  - `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`: TypeScript configuration for app, node, and build settings.
  - `eslint.config.js`: ESLint configuration for code linting and style enforcement.
- **Usage:** Used by build tools, linters, and IDEs for project setup, code quality, and development workflow.
- **Flows:** Ensures consistent build, linting, and type safety across the frontend codebase.

---

## src/components/

- **Purpose:** Houses all reusable and feature-specific React components for UI, error handling, dashboards, model selection, and visualization.

### ai/

- **Purpose:** Components for AI model selection, comparison, and display.
- **Key Files:**
  - `ModelSelection.tsx`: Model selection UI, toggling, and analytics.
  - `ModelComparisonDashboard.tsx`: Dashboard for comparing model results.
  - `ModelSelect.tsx`, `ModelSelectComponent.tsx`: Variants for model selection dropdowns and controls.
- **Usage:** Used in dashboards and forms for selecting and comparing AI models.
- **Flows:** Central to multi-model analysis and user-driven model selection.

### charts/

- **Purpose:** Data visualization components for code quality, technology, and pattern metrics.
- **Key Files:**
  - `CodeQualityMetrics.tsx`, `ComplexityEvolutionChart.tsx`, `PatternHeatmap.tsx`, `PatternTimeline.tsx`, `PatternWordCloud.tsx`, `TechRadar.tsx`, `TechStackComposition.tsx`, `TechnologyEvolutionChart.tsx`, `TechnologyRelationshipGraph.tsx`, `LearningProgressionChart.tsx`
- **Usage:** Used in dashboards to visualize analysis results and codebase evolution.
- **Flows:** Rendered in feature dashboards for insights and metrics.

### features/

- **Purpose:** High-level dashboard and feature components for analysis, insights, patterns, and technology timelines.
- **Key Files:**
  - `AnalysisDashboard.tsx`: Main dashboard for repository/code analysis.
  - `MultiAnalysisDashboard.tsx`: Dashboard for multi-model analysis and comparison.
  - `CodeQualityDashboard.tsx`: Code quality and security metrics.
  - `InsightsDashboard.tsx`: Aggregated insights and recommendations.
  - `PatternDeepDive.tsx`: In-depth pattern analysis and visualization.
  - `TechnologyTimeline.tsx`: Timeline of technology and commit evolution.
  - Subfolders: `multi-analysis/`, `insights/` for modular feature sections.
- **Usage:** Main entry points for user-facing dashboards and analysis flows.
- **Flows:** Orchestrate repository analysis, model comparison, insights, and pattern deep dives.

### ui/

- **Purpose:** Shared UI primitives and controls (buttons, tabs, theme toggles).
- **Key Files:**
  - `ThemeToggle.tsx`: Theme switcher.
  - `button.tsx`, `tabs.tsx`: Custom button and tab components.
- **Usage:** Used across all dashboards and forms for consistent UI.

### Error & Loader Components

- `ErrorBoundary.tsx`, `BrandedErrorBoundary.tsx`: Robust error handling and branded fallback UI.
- `BrandedLoader.tsx`: Branded loading spinner and status display.
- **Usage:** Used globally and in dashboards for error and loading states.

---

# Integration Points & Flows

- **Frontend → Backend:** All user actions (repo submission, model selection, analysis requests) flow through API client, hooks, and components, calling backend endpoints.
- **State Management:** TanStack Query hooks manage repository/model state, polling, and mutations.
- **UI & Error Handling:** Error boundaries and branded loaders provide robust error handling and user feedback.
- **Logging & Analytics:** Pino logger tracks API calls, UI actions, errors, and performance, with structured logs for debugging and observability.

---

## Next Steps & Enhancement Roadmap (Expanded)

### Immediate Next Steps
- **Testing:** Implement Cypress or Playwright for E2E tests; add Jest/React Testing Library coverage for all critical components and hooks.
- **Accessibility:** Audit all interactive components for keyboard navigation, focus management, and ARIA attributes; add automated accessibility tests.
- **Error Handling:** Add error boundaries to all major dashboard sections; surface actionable error messages and recovery options to users.
- **Logging/Analytics:** Integrate frontend logging with backend (correlation IDs, trace context); add user event tracking for key flows (repo creation, model selection, analysis start/complete).
- **Documentation:** Add code samples for custom hooks, context providers, and dashboard composition; include architecture diagrams and flowcharts for onboarding.
- **Feature Flags:** Use environment variables or a feature flag library (e.g., LaunchDarkly, Unleash) to toggle experimental UI and model features.

### Feature Enhancements
- **Repository Dashboard:** Add bulk repository import, tagging, and grouping; enable advanced search/filter by language, tech, commit count, and analysis status.
- **Model Selection:** Support model benchmarking, historical performance charts, and user feedback on model results; allow users to save preferred model sets.
- **Real-Time Updates:** Use WebSocket or SSE for live analysis progress, model status, and notifications; show progress bars and status indicators in dashboards.
- **Authentication:** Integrate OAuth or JWT-based login; add user profile and settings for dashboard customization.
- **Visualization:** Add zoom, pan, and drill-down to charts; enable export to PNG/SVG/CSV; support custom chart themes and color palettes.
- **Insights:** Use LLMs to generate personalized recommendations, code improvement tips, and learning paths; allow users to bookmark and share insights.
- **Export/Share:** Enable export of analysis results, charts, and insights to PDF, CSV, or shareable links; add print-friendly views.

### Architectural Improvements
- **State Management:** Evaluate Zustand, Redux Toolkit, or Jotai for complex state flows; modularize state slices for dashboards, models, and analysis.
- **API Client:** Centralize error handling, retries, and caching; add OpenAPI client generation for strict contract enforcement.
- **Performance:** Profile bundle size, optimize imports, and enable code splitting/lazy loading for dashboard modules; use React Profiler for UI bottlenecks.
- **Type Safety:** Sync types with backend using OpenAPI or codegen; enforce strict types in all hooks, components, and API calls.

### Documentation & Developer Experience
- **Onboarding:** Add step-by-step setup guides, workflow diagrams, and coding standards; provide sample PRs and code review checklists.
- **Troubleshooting:** Document common errors, debugging tips, and recovery flows; add FAQ and support contact info.
- **Roadmap:** Maintain a public roadmap and changelog; use GitHub Projects or similar for feature tracking and prioritization.

---

# End of Documentation
