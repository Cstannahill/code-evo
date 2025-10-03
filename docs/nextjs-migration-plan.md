# Next.js Migration Blueprint for Code Evolution Tracker

## 1. Purpose and Scope

- **Objective:** Rebuild the current Vite/React frontend as a Next.js 15+ application while preserving (and improving) user-facing capabilities.
- **Out of scope:** A full rewrite of the Python/FastAPI backend. The plan emphasizes reuse of the proven Python services while establishing clear integration patterns from the Next.js stack.
- **Success criteria:** Feature parity with todays dashboards, model controls, and analysis workflows, plus a maintainable hybrid architecture that supports incremental enhancements.

## 2. Current System Highlights (Baseline)

### Frontend Today

- Vite + React 19, TypeScript, Tailwind 4, Radix UI, TanStack Query, Recharts/Visx/ReactFlow.
- Rich dashboard experience: repository timelines, heat maps, AI insights, model comparison.
- Strong state/query patterns already built around REST endpoints.

### Backend Today

- Python FastAPI monolith exposing REST endpoints for repositories, analyses, model discovery, etc.
- AI pipeline implemented in Python (LangChain/Ollama/OpenAI), persistent stores via MongoDB, ChromaDB, Redis.
- Background tasks and analytics depend on Python-specific libraries.

_Takeaway_: We will keep the backend, focusing the migration on the frontend while designing clean API boundaries.

## 3. Target Next.js Architecture Overview

| Area               | Recommendation                                                                                                                                       |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Framework**      | Next.js 15 (App Router, Server Components where appropriate).                                                                                        |
| **Languages**      | TypeScript strict mode, React 19 features.                                                                                                           |
| **Styling**        | Continue Tailwind CSS. Integrate Radix UI via `@radix-ui/react-*` with Next.js-compatible tooling.                                                   |
| **State/Data**     | TanStack Query 5 for client state + Next.js Server Actions where they simplify workflows.                                                            |
| **Routing**        | `src/app` directory with route groups mapping to key dashboards (e.g., `/repositories/[id]`).                                                        |
| **Authentication** | If existing auth flows exist, leverage NextAuth (or keep current JWT flow) with API proxying to FastAPI.                                             |
| **API Layer**      | Use REST clients inside React Query hooks. Optionally add `/api/*` Next.js routes as thin proxies to FastAPI for SSR-friendly cookies/cors handling. |
| **Deployment**     | Vercel (Next.js) + existing Python infrastructure on container host (Railway/Render/Azure). Shared environment variables through secrets management. |

## 4. Application Structure Mapping

### 4.1 Route Map

- `/` Home / introduction
- `/repositories` List page (SSR to improve SEO and first load).
- `/repositories/[id]` Main dashboard (Server Component shell + client slices for interactive charts).
- `/repositories/[id]/models` Model selection + comparison view.
- `/repositories/[id]/timeline` Timeline deep dive (optional sub-route).
- `/settings` (optional) for API key status & configuration summaries.

### 4.2 Component Strategy

- **Server Components**: Fetch repository summaries, available models, stats for SSR/SEO benefits.
- **Client Components**: Visualizations (Recharts, Visx, ReactFlow), interactive filters, AI action panels.
- **Shared UI Library**: Migrate existing reusable atoms/molecules to `src/components/shared/*` with co-located styles.
- **Hooks**: Port `useRepository`, `useRepositories`, etc., to `src/hooks` using React Query + `createClientFetcher` wrappers.

### 4.3 Data Fetching

- **Server Fetchers**: Create typed fetch utilities under `src/lib/api/server.ts` for SSR data (fetch via `fetch` with credentials). Wrap in caching revalidate tags when possible.
- **Client Fetchers**: Retain Axios or use Next.js `fetch`. Provide React Query query keys consistent with existing caching strategy.
- **Error Handling**: Use Next.js error boundaries per route segment. Client components keep toast + logging behavior.

## 5. Handling Python Backend & AI Pipelines

### 5.1 Keep FastAPI as Core Service

- **Why**: AI pipeline, LangChain integrations, Mongo/Chroma orchestration already implemented and production ready.
- **How**: Treat FastAPI as a separate microservice. Next.js communicates over HTTPS (same as current frontend) using service account tokens.

### 5.2 Integration Patterns

1. **Direct REST Consumption (Preferred)**
   - Configure environment variable `NEXT_PUBLIC_API_BASE_URL` to point to FastAPI service.
   - Use `fetch`/Axios inside React Query hooks. Add interceptors for auth tokens.
2. **Next.js API Route Proxy (Optional)**
   - Create `/src/app/api/*` routes to forward requests to FastAPI.
   - Benefits: hide backend URL, inject cookies/tokens server-side, adapt to Vercel Edge if needed.
   - Drawbacks: more maintenance, double hop.
3. **OpenAPI Client Generation**
   - Generate typed clients via `orval` or `openapi-typescript-codegen` using FastAPIs OpenAPI spec for compile-time safety.

### 5.3 Handling Long-Running/Async Workflows

- Continue to trigger background analysis via FastAPI endpoints.
- Use React Query polling or server-sent events via Next.js Edge runtime (if FastAPI supports SSE/websocket).
- Display progress using the existing pattern (status endpoint) but move poll intervals into `useAnalysisStatus` hook.

### 5.4 Python-in-Next Options (When Needed)

- **Run Python scripts server-side**: Avoid running Python inside Next.js lambda; instead call FastAPI endpoints.
- **If direct Python execution is unavoidable**: host a lightweight Python microservice (e.g., Flask worker) invoked via Next.js route. Containerize with Docker Compose to orchestrate Node + Python.
- **Data serialization**: Continue using JSON; for large payloads consider message queue (Redis, RabbitMQ) triggered by Next.js API and processed by Python workers.

## 6. Tooling & Developer Experience

- **Monorepo**: Keep existing pnpm workspace. Add Next.js app under `apps/web-next` or replace current `frontend/`.
- **Linting/Formatting**: ESLint + Prettier with Next.js plugin. Align Tailwind config.
- **Testing**: Playwright for e2e, Vitest/Jest for component tests, React Testing Library.
- **Storybook**: Optional for Radix-based components before integrating into Next.
- **CI/CD**: Add workflows for Next.js build/test (GitHub Actions) alongside backend tests.

## 7. Migration Phases & Deliverables

### Phase 0: Foundations (1 week)

- Scaffold Next.js app (App Router, Tailwind, Radix setup).
- Configure environment variables, API client scaffolding, layout shell, global providers (React Query, Theme, Toasts).

### Phase 1: Core Flows (2 3 weeks)

- Recreate repository listing & detail dashboard with SSR data + client charts.
- Implement model selection UI & integrate with backend endpoints.
- Ensure authentication/authorization parity (if applicable).

### Phase 2: Advanced Visualizations (2 weeks)

- Port heatmaps, timelines, word clouds, ReactFlow diagrams.
- Optimize hydration by splitting charts into dynamic client components.
- Validate performance (Lighthouse, Core Web Vitals).

### Phase 3: Polish & Ops (1 2 weeks)

- Implement settings/status pages, error boundary UX, loading states.
- Set up CI/CD, preview environments, storybook (optional).
- Documentation & knowledge transfer.

_Total estimated effort_: ~6 8 weeks depending on team size and parallelization.

## 8. Testing & QA Strategy

| Level         | Action                                                                                       |
| ------------- | -------------------------------------------------------------------------------------------- |
| Unit          | React component tests using RTL + Vitest/Jest. Hook tests for data fetching logic.           |
| Integration   | API contract tests using MSW or Pact to ensure FastAPI + Next integration.                   |
| E2E           | Playwright scenarios for repository creation, analysis viewing, model switching.             |
| Performance   | Lighthouse runs, React Profiler for heavy charts, backend load tests remain in Python suite. |
| Accessibility | Axe audits, manual keyboard navigation checks.                                               |

## 9. Deployment & Infrastructure Plan

- **Next.js** deployed on Vercel (or existing infrastructure supporting Node 20+). Configure env vars for API base, auth tokens.
- **FastAPI** remains on current host (Railway/Azure). Ensure CORS settings allow Next.js domain.
- **Shared Contracts**: Generate OpenAPI client on CI to keep typings aligned.
- **Observability**: Connect Next.js logs to existing logging pipeline (Pino or Vercel Analytics). Ensure FastAPI monitoring unchanged.

## 10. Risks & Mitigations

| Risk                              | Mitigation                                                                                               |
| --------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Feature parity gaps               | Track components in migration checklist; conduct weekly demos.                                           |
| Data loading performance (charts) | Use dynamic imports, memoization, server component prefetching.                                          |
| Auth/session mismatches           | Standardize token storage (httpOnly cookies or explicit Bearer tokens). Proxy via Next API if necessary. |
| Backend API changes mid-migration | Freeze API contracts; adopt OpenAPI typed clients to detect breaking changes early.                      |
| Python dependency drift           | Containerize backend; lock requirements; integrate tests into CI to catch regressions.                   |

## 11. Immediate Next Steps

1. Approve architectural direction (retain FastAPI backend, build Next.js frontend).
2. Bootstrap Next.js repo/app and set up global providers.
3. Establish API client layer (direct fetch or proxy) with auth strategy.
4. Rebuild repository list + detail page as first milestone.
5. Iterate through dashboards, verifying feature parity and performance.

## 12. Optional Enhancements & Future Opportunities

- Introduce **Edge caching** for read-heavy endpoints using Next.js ISR/revalidation.
- Add **GraphQL gateway** over FastAPI if more complex client queries emerge.
- Consider **Turborepo** for orchestrating Node and Python packages with shared tooling.
- Explore **micro-frontend** segmentation if additional teams contribute simultaneously.

---

Prepared: 2025-10-02
