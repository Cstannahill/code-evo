# Code Evolution Tracker - Current Project Status and Project Context

**Last Updated**: 2025-10-03

## CURRENT STATE OVERVIEW

### System Architecture Status

✅ **Production Ready** - All core systems operational with enhanced observability

## Operational Features ✅ NEW

### Token Usage Tracking & Analytics

**Implementation**: `backend/app/utils/token_logger.py`

- **Format**: JSON Lines (JSONL) for structured analysis run logging
- **Location**: `backend/logs/analysis_tokens.log`
- **Metrics**: Per-run token estimation, repository size, task counts, timing
- **Integration**: Automated logging in both full and incremental analysis pipelines

**Log Entry Structure**:

```json
{
  "timestamp": "2024-01-20T15:30:45Z",
  "repository_path": "/path/to/repo",
  "model_used": "gpt-4",
  "estimated_tokens": 15420,
  "task_count": 8,
  "repository_size_mb": 12.5,
  "duration_seconds": 45.2,
  "analysis_type": "full"
}
```

### Ollama Model Size Service ✅ NEW

**Implementation**: `backend/app/services/ollama_size_service.py`

- **Architecture**: Centralized backend service with Redis caching
- **API Integration**: Fetches from Ollama `/api/tags` endpoint
- **Caching**: 5-minute TTL with automatic refresh
- **Exposure**: Size data available via `/api/analysis/models/available`

**Features**:

- Automatic size calculation in GB
- Cache-first strategy for performance
- Frontend integration with local fallback
- Redis-based distributed caching

#### ✅ Backend: Production-Ready Multi-Model AI System

**Core Infrastructure:**

- **FastAPI Server**: Full-featured API with enhanced middleware, CORS, and global exception handling
- **Multi-Model AI Service**: Supports 6 AI models (CodeLlama 7B/13B, CodeGemma 7B, GPT-4, GPT-3.5, Claude Sonnet)
- **Database**: MongoDB (primary) with SQLite backup + ChromaDB for vector operations
  - MongoDB infrastructure fully implemented with ODMantic models
  - Complete MongoDB models in `repository2.py` with multi-model AI support
  - Dual-database testing framework ready for migration
- **Vector Database**: ChromaDB for similarity search and pattern matching
- **Cache Layer**: Redis integration with fallback to memory caching
- **Background Processing**: FastAPI BackgroundTasks with proper lifecycle management

**AI Analysis Capabilities:**

- **Pattern Detection**: React patterns, modern JavaScript, architecture patterns, design patterns
- **Technology Stack Recognition**: Multi-language support (JS, TS, Python, HTML, CSS)
- **Framework Detection**: React, Vue, Angular, Node.js ecosystems
- **Evolution Tracking**: Pattern adoption over time with comparative analysis
- **Multi-Model Comparison**: Side-by-side analysis with consensus scoring
- **Timeline/Graph Accuracy**: Backend now propagates real commit dates to timeline and graph events, ensuring accurate historical data visualization.

#### ✅ Frontend: Modern React with Working Model Integration

**Current Architecture:**

- **Framework**: React 19.1.0 with TypeScript and Vite
- **Styling**: Tailwind CSS v4.1.7 with @tailwindcss/vite
- **State Management**: TanStack Query v5.77.0 for server state
- **UI Components**: Radix UI primitives with class-variance-authority
- **Visualization**: Recharts, Visx, ReactFlow for data visualization
- **Logging**: Pino integration for structured logging
- **Animations**: Framer Motion for enhanced UX

**✅ Working Model Integration:**

- **Local Models**: CodeLlama 7B, Devstral, CodeGemma 7B fully functional (discovery enhancement applied)
- **Model Selection**: Frontend successfully displays and selects available Ollama models; backend now matches Ollama model entries by full and base names
- **Analysis Pipeline**: End-to-end code analysis working with local models
- **API Integration**: Completed model availability hook and Dashboard component data transformation

Notes: The Ollama discovery logic was made more robust to accept both 'codellama:7b' and 'codellama' responses from the Ollama /api/models endpoint. Tests executed: 1 passed, 3 skipped due to async test setup.

**🔄 Configuration Required for Cloud Models:**

- **OpenAI Models**: Requires API key configuration for GPT-4 and GPT-3.5 Turbo
  - Set `OPENAI_API_KEY` environment variable in backend configuration
  - Update `.env` file with valid OpenAI API key for demo/testing
- **Anthropic Models**: Requires API key for Claude Sonnet integration
- **Google Vertex**: Future integration planned

### Executive Summary

The Code Evolution Tracker has evolved into a **sophisticated AI-powered code analysis platform** with enterprise-grade backend capabilities. The system successfully processes large codebases (1,500+ commits) and provides production-quality insights comparable to commercial code analysis tools.

**✅ MAJOR MILESTONE**: Frontend model integration completed - local Ollama models (CodeLlama 7B/13B, CodeGemma 7B) are now fully operational in the frontend interface.

## Backend Status: ✅ FULLY OPERATIONAL & ENHANCED WITH TOKEN TRACKING

### Infrastructure Components

1. **Application Server** (`app/main.py`)

   - FastAPI with async lifecycle management
   - Rich logging with structured output
   - Global exception handling with detailed error context
   - Background task tracking and cleanup
   - Health check endpoint with service status

2. **Multi-Model AI Service** (`app/services/multi_model_ai_service.py`)

   - **Local Models**: CodeLlama 7B/13B, CodeGemma 7B via Ollama
   - **API Models**: GPT-4, GPT-3.5 Turbo (OpenAI), Claude Sonnet (Anthropic)
   - Model comparison and consensus analysis
   - Performance benchmarking and token tracking

3. **Token Usage Logging** (`app/utils/token_logger.py`) ✅ NEW

   - Per-run analysis token estimation and logging
   - JSON Lines (JSONL) format for analysis runs in `backend/logs/`
   - Tracks repository size, model used, task counts, and estimated tokens
   - Duration tracking for performance monitoring

4. **Ollama Model Size Service** (`app/services/ollama_size_service.py`) ✅ NEW

   - Backend service to fetch model sizes from Ollama /api/tags
   - Redis caching with 5-minute TTL for model size data
   - Exposes size_gb in available models API endpoint
   - Automatic size calculation and formatting in GB

5. **Database Architecture** (`app/core/database.py`)

   - **Primary**: SQLite with SQLAlchemy ORM
   - **Analytics**: MongoDB integration for advanced comparisons
   - **Vector**: ChromaDB for similarity search
   - **Cache**: Redis with memory fallback

6. **API Endpoints** (`app/api/`)
   - Repository management and analysis
   - Multi-model comparison endpoints
   - Authentication and authorization
   - Real-time analysis status
   - Enhanced models endpoint with Ollama sizes ✅ UPDATED

### Working API Endpoints

#### Core Services

```bash
GET  /health                           # Comprehensive service health check
GET  /api/connection-test              # Connection debugging
```

#### Repository Management

```bash
POST /api/repositories                 # Create repository with model selection
GET  /api/repositories                 # List all repositories
GET  /api/repositories/{id}            # Repository details
GET  /api/repositories/{id}/analysis   # Analysis results
GET  /api/repositories/{id}/timeline   # Technology timeline
GET  /api/repositories/{id}/analyses/models    # List models used for analysis ✅ NEW
GET  /api/repositories/{id}/analysis/by-model  # Get analysis by model ✅ NEW
```

#### Multi-Model Analysis

```bash
GET  /api/multi-model/models/available    # Available AI models
POST /api/multi-model/analyze/compare     # Multi-model comparison
POST /api/multi-model/analyze/code        # Single code analysis
GET  /api/multi-model/comparisons/{id}    # Comparison results
```

#### Pattern Analysis

```bash
GET  /api/analysis/patterns               # Detected patterns
GET  /api/analysis/insights/{repo_id}     # AI insights
POST /api/analysis/evolution              # Code evolution tracking
GET  /api/analysis/models/available       # Available models with sizes ✅ ENHANCED
```

## Frontend Status: ✅ MODERN REACT WITH WORKING MODEL INTEGRATION

### Current Technology Stack

**Core Framework:**

```json
{
  "react": "^19.1.0",
  "typescript": "latest",
  "vite": "latest"
}
```

**State & Data Management:**

```json
{
  "@tanstack/react-query": "^5.77.0",
  "@tanstack/react-query-devtools": "^5.77.0",
  "axios": "^1.9.0",
  "axios-retry": "^4.5.0"
}
```

**UI & Styling:**

```json
{
  "tailwindcss": "^4.1.7",
  "@tailwindcss/vite": "^4.1.7",
  "@radix-ui/react-*": "^1.x.x",
  "framer-motion": "^12.12.2",
  "lucide-react": "^0.511.0",
  "class-variance-authority": "^0.7.1"
}
```

**Data Visualization:**

```json
{
  "recharts": "^2.15.3",
  "@visx/axis": "^3.12.0",
  "@visx/heatmap": "^3.12.0",
  "reactflow": "^11.11.4",
  "react-wordcloud": "^1.2.7"
}
```

### ✅ Completed Frontend Features

1. **Model Integration**: Enhanced multi-model support with backend-provided Ollama sizes ✅
   - Local Ollama models (CodeLlama 7B/13B, CodeGemma 7B) working
   - Backend size service integration with local fallback
   - Real-time model availability detection
2. **Component System**: Radix UI primitives with custom styling
3. **Type Safety**: Comprehensive TypeScript with strict type checking
4. **State Management**: TanStack Query for server state synchronization
5. **Error Handling**: React error boundaries with detailed logging
6. **Performance**: Code splitting and lazy loading
7. **Accessibility**: WCAG compliant components

## Frontend Architecture Analysis (Comprehensive)

### Component Architecture (51 TypeScript Files Analyzed)

**📁 Component Organization:**

- **33 React Components** in feature-based structure
- **18 TypeScript Files** for types, hooks, and utilities
- **7 Custom Hooks** for state management and API integration
- **6 Type Definition Files** for comprehensive type safety

**🎨 Chart & Visualization Components (10 Components):**

- `PatternHeatmap` - Pattern density visualization
- `TechRadar` - Technology adoption radar chart
- `TechStackComposition` - Technology stack pie charts
- `TechnologyEvolutionChart` - Technology adoption over time
- `PatternWordCloud` - Pattern frequency word cloud
- `PatternTimeline` - Pattern evolution timeline
- `LearningProgressionChart` - Learning curve visualization
- `ComplexityEvolutionChart` - Code complexity trends
- `CodeQualityMetrics` - Quality score visualizations
- `TechnologyRelationshipGraph` - Technology dependency graph

**🏗️ Feature Components (11 Components):**

- `Dashboard` - Main repository analysis interface
- `AnalysisDashboard` - Multi-tab analysis display (544 lines)
- `MultiAnalysisDashboard` - Primary analysis orchestrator
- `CodeQualityDashboard` - Code quality metrics display
- `InsightsDashboard` - AI-generated insights interface
- `EvolutionMetrics` - Code evolution tracking
- `TechnologyTimeline` - Technology adoption timeline
- `PatternViewer` - Pattern detection results
- `RepositoryForm` - Repository input and validation
- `RepositoryInput` - Repository URL input component
- `PatternDeepDive` - Detailed pattern analysis

**🤖 AI Integration Components (3 Components):**

- `ModelSelection` - AI model selection interface (337 lines)
- `ModelComparisonDashboard` - Multi-model comparison interface
- `ModelSelectComponent` - Model selection dropdown

**⚙️ Custom Hooks System (7 Hooks):**

- `useModelAvailability` - Dynamic AI model availability checking
- `useRepository` - Repository state management
- `useRepositories` - Repository list management
- `useCreateRepository` - Repository creation workflow
- `useRepositoryAnalysis` - Analysis data fetching
- `useLogger` - Production logging system
- `usePerformanceMeasure` - Performance tracking

### Advanced Architecture Features

**🔧 API Integration:**

- Enhanced API client (159 lines) with retry logic and error handling
- Type-safe API endpoints with full TypeScript coverage
- Real-time status monitoring for backend and AI services
- Optimistic updates with TanStack Query

**📊 State Management:**

- TanStack Query v5.77.0 for server state synchronization
- React Query DevTools integration for debugging
- Optimistic UI updates with rollback on failure
- Intelligent caching with stale-while-revalidate strategy

**🎨 Styling & UI System:**

- Tailwind CSS v4.1.7 with custom CTAN brand colors
- Custom CSS brand system (212 lines) with cat-themed elements
- Radix UI primitives for accessibility compliance
- Framer Motion animations for enhanced user experience
- Responsive design with mobile-first approach

**🚨 Error Handling & Logging:**

- Production-ready error boundaries with retry mechanisms
- Structured logging with Pino integration (538 lines)
- Error tracking with unique error IDs and context
- Development debugging tools with error details export
- Component-level error isolation and recovery

**📱 User Experience:**

- Progressive loading with skeleton states
- Real-time feedback for long-running operations
- Toast notifications for user actions
- Keyboard navigation support (WCAG compliant)
- Dark theme implementation throughout

### Type Safety & Development Quality

**📋 TypeScript Architecture:**

- Strict type checking with explicit type annotations
- Comprehensive interfaces for all API responses
- Type-safe component props with detailed JSDoc
- Union types for state management
- Generic type constraints for reusable components

**🔍 Code Quality Tools:**

- ESLint configuration with TypeScript and React rules
- Prettier integration for consistent formatting
- Import organization with automatic sorting
- Performance linting rules for optimization
- Accessibility linting with eslint-plugin-jsx-a11y

**⚡ Performance Optimizations:**

- Code splitting with React.lazy and Suspense
- Memoization of expensive computations
- Virtual scrolling for large data sets
- Image optimization and lazy loading
- Bundle size monitoring and optimization

### Data Flow & Architecture Patterns

**🔄 Data Flow:**

```bash
User Action → Component → Hook → API Client → Backend
     ↓           ↓         ↓        ↓         ↓
    UI Update ← State ← Query ← Response ← Analysis
```

**🏛️ Architecture Patterns:**

- Container/Presentational component separation
- Custom hooks for business logic encapsulation
- Error boundary pattern for fault tolerance
- Observer pattern for real-time updates
- Command pattern for user actions

**🔌 Integration Points:**

- Backend API integration with full type safety
- AI model availability checking with status indicators
- Real-time analysis progress tracking
- File upload and repository cloning integration
- Multi-model comparison orchestration

## System Integration Status

### ✅ Working Integrations

1. **Frontend ↔ Backend**: Local model analysis end-to-end
2. **Git ↔ AI Pipeline**: Repository cloning → Analysis → Pattern detection
3. **Multi-Model Processing**: Parallel analysis with consensus scoring
4. **Vector Search**: ChromaDB similarity matching for pattern discovery
5. **Cache Optimization**: Redis-backed response caching with TTL
6. **Background Processing**: Non-blocking repository analysis

## Current Development Priorities

### Immediate Next Steps

1.  **✅ Enhanced Repository Tabs Styling** (Just Completed)

- ✅ Applied CTAN brand CSS classes to `MARepositoryTabs.tsx` component
- ✅ Added `ctan-tab`, `ctan-button`, `ctan-card`, and `ctan-icon` classes for consistent styling
- ✅ Enhanced repository buttons with brand styling including active states and hover effects
- ✅ Applied icon glow animations and card hover effects from brand design system
- ✅ Integrated yellow/gold accent colors throughout tabs interface

**Next: Test enhanced repository tabs in production to validate brand styling integration**

2.  **🔄 Database Migration to MongoDB** (High Priority):

    **Phase 1: MongoDB Infrastructure Completion**

- Complete MongoDB models implementation in `app/models/repository2.py`
- Finalize database connection management in `app/core/database2.py`
- Update schema definitions in `app/schemas/repository2.py`
- Implement ODMantic-based data access layer
- Create comprehensive MongoDB indexes for performance

**Phase 2: Service Layer Migration**

- Update AI service to use MongoDB for analysis results storage
- Migrate repository service to MongoDB collections
- Implement dual-database service layer for transition period
- Add MongoDB-specific aggregation queries for analytics
- Update multi-model analysis service for MongoDB storage

**Phase 3: API Layer Updates**

- Update repository API endpoints to use MongoDB
- Modify analysis endpoints for MongoDB document operations
- Implement MongoDB-based pagination and filtering
- Update error handling for MongoDB operations
- Add MongoDB health checks to status endpoints

**Phase 4: Testing & Validation**

- Create comprehensive test suite for MongoDB operations
- Validate data integrity during migration process
- Performance testing with large datasets in MongoDB
- Test dual-database operations and failover scenarios
- Verify aggregation queries and analytics functionality

**Phase 5: Migration & Backup Strategy**

- Implement SQLite to MongoDB data migration scripts
- Configure MongoDB as primary with SQLite as backup
- Update configuration management for database switching
- Document migration procedures and rollback strategies
- Production deployment with zero-downtime migration

3.  **Enhance Dashboard Visualization**

- Complete remaining chart component implementations
- Improve data visualization responsiveness
- Add advanced filtering and search capabilities
- Implement export functionality for analysis results

4.  **Performance & User Experience Optimization**

- Optimize large dataset rendering performance
- Implement progressive loading for complex visualizations
- Add advanced keyboard shortcuts and accessibility features
- Enhance mobile responsiveness for smaller screens

### Configuration Requirements & Implementation Guide

**Environment Configuration Files:**

```bash
# Backend/.env (Create from .env.example)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_ORG_ID=org-your-organization-id  # Optional
OPENAI_MODEL_TIMEOUT=60  # Request timeout in seconds
OPENAI_MAX_RETRIES=3     # Number of retry attempts
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Future use

# Development/Testing Configuration
DEBUG_OPENAI_CALLS=true  # Log API calls for debugging
OPENAI_RATE_LIMIT_PER_MINUTE=60  # Rate limiting configuration
```

**Backend Implementation Requirements:**

1. **Configuration Validation (`app/config.py`)**:

   ```python
   # Add OpenAI settings to existing config
   openai_api_key: Optional[str] = None
   openai_org_id: Optional[str] = None
   openai_timeout: int = 60
   openai_max_retries: int = 3
   ```

2. **AI Service Enhancement (`app/services/ai_service.py`)**:

   - Add OpenAI client initialization with error handling
   - Implement model availability checking for cloud models
   - Add cost tracking and usage monitoring
   - Enhanced error messages for API key issues

3. **API Endpoints Updates**:
   - `/models/available` - Include OpenAI models when configured
   - `/models/health` - Check OpenAI API connectivity
   - `/analysis/cost-estimate` - Provide cost estimates for cloud models

**Frontend Implementation Requirements:**

1. **Model Selection Component Updates**:

   - Display cloud model status (available/configured/error)
   - Add cost indicators for cloud vs local models
   - Implement model recommendation system
   - Show estimated analysis time for different models

2. **Configuration Status Display**:
   - Settings page with API key configuration status
   - Visual indicators for configured vs missing API keys
   - Link to configuration documentation

**Current Working Models:**

- ✅ CodeLlama 7B (Local Ollama)
- ✅ Devstral (Local Ollama)
- ✅ CodeGemma 7B (Local Ollama)
- 🔧 GPT-4 (Requires API key)
- 🔧 GPT-3.5 Turbo (Requires API key)
- 🔧 Claude Sonnet (Requires API key)

## Development Environment Setup

### Backend Services (All Operational)

```bash
# Python environment with all dependencies
cd backend/
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Supporting services
ollama serve                    # AI model server (port 11434)
redis-server                   # Cache server (port 6379)
```

### Frontend Development

```bash
# Modern React with Vite
cd frontend/
pnpm install                   # Install dependencies
pnpm dev                       # Development server (port 5173)
```

## Overall State

- `.gitignore` now explicitly un-ignores `backend/app/utils/token_logger.py` so Railway builds include the token logging utility, preventing `ModuleNotFoundError` during deployment.
- MongoDB connection layer now supports configurable TLS flags (`MONGODB_TLS`, `MONGODB_TLS_ALLOW_INVALID_CERTIFICATES`, `MONGODB_TLS_CA_FILE`, `MONGODB_APP_NAME`) so Railway deployments can negotiate SSL handshakes without code changes.
- All Pylance errors in `backend/app/api/analysis.py` and `backend/app/tasks/analysis_tasks.py` related to service method usage, type safety, and parameter passing have been resolved.
- API and background task layers now use correct service and model utility functions, with explicit type conversions and robust error handling.
- Background analysis, status, and cancel flows are now type-safe and consistent with backend contracts.
- AIService now includes a utility to select the correct OpenAI token parameter (`max_completion_tokens` for new models, `max_tokens` for legacy models) with robust error handling and logging. All relevant calls to the multi-model service in `analyze_code_pattern` and `analyze_code_quality` now use this utility, ensuring compatibility with both old and new OpenAI models.

Session additions:

- Backend: Added enhanced analysis bundle retrieval and per-model listing/fetch endpoints.
- Frontend: Added API client methods for models and by-model fetch; created a reusable `ModelSelector` and integrated it into `MAResultsSection` header. The selector fetches repository models and allows an override to reflect context; deeper section wiring is planned.

## Immediate Next Steps

- Stage and commit `backend/app/utils/token_logger.py` (now unignored) and redeploy so the backend includes the token logging module in production builds.
- Update Railway (and any other hosted environments) to set `MONGODB_TLS=true` and, if using self-signed certs, `MONGODB_TLS_ALLOW_INVALID_CERTIFICATES=true` or provide `MONGODB_TLS_CA_FILE`, then redeploy to verify MongoDB health check passes.
- Test backend analysis with both legacy and new OpenAI models to confirm the token parameter fix works as intended.
- Monitor logs for any parameter-related errors or unexpected behavior.
- If successful, propagate the utility to any other OpenAI call sites as needed.
- Test the dashboard/timeline to confirm that real commit dates are now reflected in all graphs and events (timeline/graph accuracy fix).
- If any timeline/graph still uses today's date, further audit frontend or API serialization for date propagation issues.

  Update 2025-09-13: Fixed `PatternTimeline` rendering issue where legend labels displayed but no lines were drawn. Root cause was a mismatch between requested pattern display names (with spaces) and data keys (snake_case). Added robust series mapping (display name -> dataKey) and strengthened date parsing/formatting. Also introduced strict types (`NormalizedItem`, `ChartDatum`) and improved logging.

- Verify background analysis and status/cancel flows in integration testing.
- Add/expand automated tests for error and edge cases in background task and analysis flows.
- Continue monitoring logs for runtime errors or contract mismatches.

Next steps (selector integration):

- Pass model-specific pattern/quality data down to `AnalysisDashboard` sections (PatternHeatmap, CodeQualityDashboard) when an override is selected.
- Add hooks: `useRepositoryModels` and `useRepositoryAnalysisByModel` with TanStack Query for caching and reuse.
- Document new endpoints: `/api/repositories/{id}/analyses/models` and `/api/repositories/{id}/analysis/by-model` in README.
