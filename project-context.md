# Code Evolution Tracker - Current Project Status and Project Context

**Last Updated**: 2025-10-03

## CURRENT STATE OVERVIEW

### System Architecture Status

✅ **Production Ready** - All core systems operational with enhanced observability

## Recent Updates ✅

### GPT-5 Model Update + Dropdown Fix (2025-10-03) ✅ COMPLETE

**What Changed**: Updated OpenAI models to GPT-5 series and fixed dropdown selection issue

**GPT-5 Model Series**:

- **GPT-5** ($0.00125/1k) - Flagship model with 400K context, advanced reasoning
- **GPT-5 Mini** ($0.00025/1k) - Balanced performance and cost
- **GPT-5 Nano** ($0.00005/1k) - Ultra-fast, cost-effective (99.5% cheaper than GPT-4 Turbo)

**Critical Temperature Restriction**:

- All GPT-5 models require `temperature=1` (default)
- **DO NOT** include temperature parameter in API calls
- Marked with `temperature_locked: true` flag in backend
- Sending custom temperature values returns 400 Bad Request

**Dropdown Selection Fixed**:

- **Before**: Unavailable models were disabled (greyed out, unclickable)
- **After**: All models selectable, availability checked before analysis
- Error message: "🔒 GPT-5 requires an API key. Please add your OpenAI API key in Settings"

**Files Modified**:

- `backend/app/api/analysis.py` - GPT-5 models with temperature_locked flag
- `frontend/src/components/ai/ModelSelect.tsx` - Removed disabled state
- `frontend/src/components/features/MultiAnalysisDashboard.tsx` - Added availability check
- `frontend/src/types/modelAvailability.ts` - Added temperature_locked field
- `docs/GPT5_MODEL_UPDATE.md`, `docs/DROPDOWN_SELECT_ISSUE.md` - Comprehensive documentation

**Status**: ✅ Ready for production deployment

### Model Display Fix - Always Show All Models (2025-10-03) ✅ FIXED

**Issue**: No models displayed in production even after adding API keys

**Root Cause**: Backend only returned models when API keys were detected, resulting in empty model list for users without keys

**Impact**:

- Users couldn't see what models existed
- No indication of how to unlock cloud models
- Confusing empty state in model selection UI
- Poor discoverability of available AI models

**Fix Applied**:

1. ✅ Backend now **always returns all models** with `available` flag:
   - OpenAI models (GPT-4o, GPT-4o Mini, GPT-4 Turbo) always visible
   - Anthropic models (Claude Sonnet 4.5, Opus 4) always visible
   - Ollama models shown when Ollama is running
2. ✅ Added `requires_api_key` field to indicate locked models
3. ✅ Frontend displays unavailable models as greyed out with warning
4. ✅ Updated to **Claude Sonnet 4.5 and Opus 4** (latest, same cost as 3.x)

**Model List** (Always Displayed):

- **OpenAI**: GPT-5 ($0.00125/1k), GPT-5 Mini ($0.00025/1k), GPT-5 Nano ($0.00005/1k)
- **Anthropic**: Claude Sonnet 4.5 ($0.003/1k), Claude Opus 4 ($0.015/1k)
- **Ollama**: Dynamic based on local installation (Free)

**GPT-5 Series Temperature Restriction**:

- All GPT-5 models (GPT-5, GPT-5 Mini, GPT-5 Nano) require `temperature=1` (default)
- DO NOT include temperature parameter in API calls to GPT-5 models
- Backend marks these with `temperature_locked: true` flag
- Sending custom temperature values will result in 400 Bad Request errors

**User Experience**:

- All models always visible (before: empty list without API keys)
- Locked models greyed out with "⚠️ Requires API Key" badge
- Clear indication of what can be unlocked
- Models become available immediately after adding API key

**Files Modified**:

- `backend/app/api/analysis.py` - Always return all models with availability flags
- `frontend/src/components/ai/ModelSelection.tsx` - Handle unavailable models UI
- `frontend/src/types/modelAvailability.ts` - Add `requires_api_key` field
- `docs/MODEL_DISPLAY_FIX.md` - Comprehensive documentation

**Status**: Production-ready, all models now visible with clear availability status

### Tunnel API Route Fix (2025-10-03) ✅ FIXED

**Issue**: Tunnel endpoints returning 404 errors in production (Vercel frontend)

**Root Cause**: `useTunnelManager` hook was using hardcoded `/api/tunnel/*` URLs instead of the centralized `ApiClient` with `getApiBaseUrl()` helper

**Impact**:

- Tunnel registration failing with 404 Not Found
- Status checks returning 404
- Recent requests endpoint unreachable
- Frontend making requests to `https://code-evo.vercel.app/api/tunnel/*` instead of Railway backend

**Fix Applied**:

1. ✅ Added tunnel methods to `ApiClient` class:
   - `getTunnelStatus()` - Fetch tunnel connection status
   - `registerTunnel(tunnelUrl)` - Register new tunnel
   - `disableTunnel()` - Disable active tunnel
   - `getTunnelRecentRequests(limit)` - Fetch request history
2. ✅ Updated `useTunnelManager` hook to use `apiClient` instead of raw fetch
3. ✅ All tunnel requests now properly route through `getApiBaseUrl()` helper

**Benefits**:

- Consistent API routing across all environments (localhost, Railway, Vercel)
- Automatic authentication header injection via `authenticatedFetch()`
- Centralized error handling and retry logic
- Proper base URL resolution for production deployments

**Files Modified**:

- `frontend/src/api/client.ts` - Added 4 tunnel methods
- `frontend/src/hooks/useTunnelManager.ts` - Replaced fetch calls with apiClient calls

**Status**: Production-ready, tunnel endpoints now accessible from deployed frontend

### Secure Ollama Tunnel System (2025-10-03) ✅ NEW

**Feature**: Production deployment solution for local Ollama access via secure tunnels

**Problem**: Deployed backend cannot access `localhost:11434` Ollama instances, blocking AI analysis in production environments

**Solution**: Implemented comprehensive secure tunnel infrastructure with full transparency and user consent

**Backend Implementation**:

- `SecureTunnelService` (421 lines) - Core tunnel management with token-based auth
- API endpoints: `/api/tunnel/register`, `/status`, `/disable`, `/proxy`, `/requests/recent`
- Security: 24-hour token expiration, rate limiting (60 requests/min), request audit logging
- Validation: Tunnel URL verification, health checks, automatic connection monitoring

**Frontend Implementation**:

- `useTunnelManager` hook - State management and API integration
- `TunnelToggle` component - Compact nav bar control with status indicator
- `RiskDisclosureDialog` - Full transparency with 3 risk categories and source code links
- `TunnelSetupWizard` - Step-by-step guides for Cloudflare Tunnel and ngrok

**Security Measures**:

- Token-based authentication with automatic expiration
- Rate limiting per user to prevent abuse
- Comprehensive audit logging (last 1000 requests)
- Request validation and sanitization
- Explicit user consent with risk disclosure

**Transparency Features**:

- Direct links to source code (backend service, API, frontend hook)
- Risk disclosure dialog with 3 categories (exposure, bandwidth, security)
- Recent request history viewer for monitoring
- Status indicators and connection diagnostics

**Tunnel Providers Supported**:

- **Cloudflare Tunnel**: Free, secure, no account required for quick tunnels (recommended)
- **ngrok**: Quick setup, free tier with signup, persistent URLs

**UI/UX Design**:

- Toggle placed in nav bar between AI status and Theme Toggle (clean, uncluttered)
- Visual status indicator: Green (active), Yellow (connecting), Red (error), Gray (disconnected)
- Animated ping effect on active connection
- Dropdown menu with connection stats and actions
- Error messaging with actionable feedback

**Components Created**:

- `backend/app/services/secure_tunnel_service.py` - Tunnel management service
- `backend/app/api/tunnel.py` - FastAPI router with 6 endpoints
- `frontend/src/hooks/useTunnelManager.ts` - React hook for state/API
- `frontend/src/components/tunnel/TunnelToggle.tsx` - Nav bar component
- `frontend/src/components/tunnel/RiskDisclosureDialog.tsx` - Risk disclosure UI
- `frontend/src/components/tunnel/TunnelSetupWizard.tsx` - Setup wizard UI
- `frontend/src/types/tunnel.ts` - TypeScript type definitions

**Status**: Backend infrastructure complete, frontend components integrated, ready for testing
**Next**: End-to-end testing with real Ollama instance + Cloudflare Tunnel

### Chart Tooltip Overlay Fix (2025-10-03) ✅

**Fixed**: All chart tooltip overlays now have solid dark backgrounds for better readability

**Issue**: Multiple chart tooltips used semi-transparent `bg-popover` or `hsl(var(--popover))` backgrounds, making text hard to read over busy chart visualizations

**Solution**: Converted all tooltips to use solid dark backgrounds (`#111827` / `bg-gray-900`) with proper contrast

- **Color Scheme**: Dark gray background (#111827), gray border (#374151), white text (#ffffff)
- **Consistency**: All tooltips now match the professional appearance shown in tech timeline tooltips

**Components Updated**:

- `PatternTimeline.tsx` - CustomTooltip with solid bg-gray-900
- `TechnologyTimeline.tsx` - CustomTooltip with solid bg-gray-900
- `LearningProgressionChart.tsx` - Tooltip contentStyle updated
- `ComplexityEvolutionChart.tsx` - Tooltip contentStyle updated
- `TechStackComposition.tsx` - Both tooltip instances updated
- `TechnologyEvolutionChart.tsx` - Tooltip contentStyle updated
- `TechRadar.tsx` - Tooltip contentStyle added

**Result**: All 7 chart components now have fully readable, professional tooltips with solid backgrounds

### Pattern Analysis Tab Optimization (2025-10-03)

**Fixed**: Pattern Heatmap centering and Pattern Deep Dive scroll issues

**Phase 4 - Pattern Tab Full-Width Layout**:

- **Issues**:
  - Pattern Heatmap had fixed width (600px) in 2-column grid causing alignment issues
  - Pattern Deep Dive list had `max-h-96 overflow-y-auto` causing unnecessary vertical scroll
- **Solution**: Full-width stacked layout for all pattern analysis components
- **Changes Made**:
  - Removed `xl:grid-cols-2` wrapper div from Pattern Analysis tab
  - Changed PatternHeatmap width prop from fixed `600px` to `"100%"` responsive default
  - Updated PatternHeatmap interface to accept `width?: number | string`
  - Added intelligent width calculation handling for percentage-based widths
  - Added `minHeight` to heatmap for consistent height with responsive width
  - Removed `max-h-96 overflow-y-auto` from Pattern Deep Dive pattern list
  - Pattern list now flows naturally without scroll constraints
  - All three sections (Heatmap, Timeline, Deep Dive) now full-width stacked

**Components Modified**:

- `frontend/src/components/features/AnalysisDashboard.tsx` - Pattern tab layout restructure
- `frontend/src/components/charts/PatternHeatmap.tsx` - Responsive width improvements
- `frontend/src/components/features/PatternDeepDive.tsx` - Removed scroll constraint

**Status**: Pattern Analysis tab now fully responsive and scroll-free
**Result**: Clean, professional layout with better space utilization and no cramped scrolling

### Analysis Dashboard Layout Optimization (2025-10-03)

**Fixed**: Overview tab layout and Pattern Distribution centering issues

**Phase 3 - Full-Width Row Layout**:

- **Issue**: Code Quality Metrics and Pattern Distribution squeezed side-by-side caused alignment issues
- **Solution**: Changed from 2-column grid to full-width stacked rows
- **Changes Made**:
  - Removed `lg:grid-cols-2` wrapper div from Overview tab
  - Each section now gets full width for better content display
  - Pattern Distribution now properly centered and responsive
  - Code Quality Metrics has more room for 6 metric cards to breathe
  - Improved overall UX with clearer visual hierarchy
  - Enhanced PatternWordCloud to use `width="100%"` by default
  - Increased gap spacing in word cloud from `gap-2` to `gap-3`
  - Increased padding in word cloud from `p-4` to `p-6` for better spacing

**Components Modified**:

- `frontend/src/components/features/AnalysisDashboard.tsx` - Layout restructure
- `frontend/src/components/charts/PatternWordCloud.tsx` - Full-width responsive improvements

**Status**: Layout is now clean, centered, and responsive across all screen sizes
**Result**: Better readability, improved visual balance, professional dashboard appearance

### Code Quality Metrics UI Enhancement (2025-10-03)

**Fixed**: Layout alignment and responsiveness issues in `CodeQualityMetrics` component

**Phase 1 - Circle Alignment**:

- **Issue**: Circular progress circles were misaligned and pushed right out of their category cards
- **Solution**: Restructured MetricCard component with proper flexbox centering
- **Changes**: Added flex container with proper alignment, removed mx-auto, proper width distribution

**Phase 2 - Title & Icon Layout**:

- **Issue**: Titles were truncating/wrapping awkwardly (e.g., "Maintainab...", "Evolution Score" wrapping), icons cramped
- **Solution**: Vertical stacked layout with centered icon and title
- **Changes Made**:
  - Moved icon above title in centered vertical stack
  - Increased icon size from `w-5 h-5` to `w-6 h-6` for better visibility
  - Changed title to centered alignment with `leading-tight` for better text flow
  - Reduced card padding from `p-6` to `p-4` for tighter, cleaner appearance
  - Added `gap-2` between icon and title for proper spacing
  - Added `leading-snug` and `px-1` to description for better text wrapping
  - Full titles now display cleanly without truncation
  - Added proper TypeScript typing with `LucideIcon` and `PatternInfo` types

**Component**: `frontend/src/components/charts/CodeQualityMetrics.tsx`
**Status**: All TypeScript errors resolved, layout properly centered and responsive
**Result**: Clean card layout with icon-on-top design, full title visibility, better mobile responsiveness

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
- Frontend API integrations now standardize on the `getApiBaseUrl` helper, eliminating relative `/api` calls that previously broke production authentication and ancillary requests like API key management.
- The `useLocalOllama` hook detects secure-origin mixed content blocking, surfaces actionable guidance to the user, and supports a configurable `VITE_OLLAMA_BASE_URL` for tunneling a remotely accessible Ollama endpoint.
- `ENVIRONMENT_SETUP.md` documents the new Ollama configuration variable alongside the existing API base URL guidance so deployments know how to expose local models safely.
- `/api/analysis/models/available` now accepts optional Bearer auth and inspects per-user API keys, enabling guest-supplied OpenAI credentials to populate the model picker even when the global environment lacks cloud keys.
- `ModelSelection` displays contextual empty-state guidance, prompting users to add API keys when no cloud models are available, and surfaces Ollama browser-blocking warnings inline.
- Model availability flow shares a dedicated TypeScript contract, and `ApiClient.getAvailableModels` now always forwards bearer tokens via the authenticated fetch helper so guest/user API keys unlock OpenAI results consistently across the UI.
- MongoDB connection layer now actively consumes TLS-related environment variables (`MONGODB_TLS`, `MONGODB_TLS_ALLOW_INVALID_CERTIFICATES`, `MONGODB_TLS_CA_FILE`, `MONGODB_TLS_DISABLE_OCSP`, `MONGODB_APP_NAME`) and feeds them into the Motor client, adding validation for CA bundle presence and rich diagnostic logging on connection failures.
- PyMongo/Motor client configuration now receives server selection, connect, and socket timeout settings (plus pool sizing) from env configuration, eliminating the premature asyncio cancellation and ensuring full `ServerSelectionTimeoutError` diagnostics reach the logs. Sanitized connection URIs and node topology snapshots are emitted whenever a connection attempt fails.
- Docker image no longer overrides `SSL_CERT_FILE` with the AWS RDS bundle; instead it installs Debian's `ca-certificates`, allowing the default trust store (which already includes the MongoDB Atlas chain) to validate TLS handshakes. Deployments must remove any stale `MONGODB_TLS_CA_FILE=/app/certs/rds-combined-ca-bundle.pem` environment variable so the driver falls back to the system bundle. If that variable is still present at runtime, the backend now logs a warning and automatically ignores the missing file rather than aborting initialization.
- CORS defaults now include the deployed frontend origin (`https://code-evo-frontend-z2cx.vercel.app`) alongside localhost entries. Additional domains can be supplied at runtime via the comma-separated `CORS_ORIGINS` environment variable without code changes.
- All Pylance errors in `backend/app/api/analysis.py` and `backend/app/tasks/analysis_tasks.py` related to service method usage, type safety, and parameter passing have been resolved.
- API and background task layers now use correct service and model utility functions, with explicit type conversions and robust error handling.
- Background analysis, status, and cancel flows are now type-safe and consistent with backend contracts.
- AIService now includes a utility to select the correct OpenAI token parameter (`max_completion_tokens` for new models, `max_tokens` for legacy models) with robust error handling and logging. All relevant calls to the multi-model service in `analyze_code_pattern` and `analyze_code_quality` now use this utility, ensuring compatibility with both old and new OpenAI models.

Session additions:

- Backend: Added enhanced analysis bundle retrieval and per-model listing/fetch endpoints.
- Frontend: Added API client methods for models and by-model fetch; created a reusable `ModelSelector` and integrated it into `MAResultsSection` header. The selector fetches repository models and allows an override to reflect context; deeper section wiring is planned.

## Railway Deployment Dependencies Fix (2025-10-03) ✅ NEW

**Issue**: Railway deployment was using incomplete `requirements.railway.txt` missing critical dependencies

**Fixed Dependencies**:

- ✅ `bcrypt==4.2.1` - Added explicit version (was just `bcrypt`)
- ✅ `websockets==13.1` - CRITICAL - Used by ollama_tunnel_service.py
- ✅ `rich==14.0.0` - CRITICAL - Used for logging in main.py
- ✅ All authentication dependencies verified (bcrypt, passlib, PyJWT, cryptography)

**Documentation**: Created `backend/REQUIREMENTS_COMPARISON.md` with comprehensive analysis

- Full comparison of local vs Railway requirements
- Identified safe removals (PyTorch, dev tools, unused services)
- Verified all critical imports present
- Deployment size reduced from ~5-8GB to ~500MB-1GB

**Status**: requirements.railway.txt is production-ready with all vital dependencies

## Immediate Next Steps

- Stage and commit updated `backend/requirements.railway.txt` with complete dependencies and redeploy to Railway
- Monitor Railway deployment logs for any missing dependency errors
- Stage and commit `backend/app/utils/token_logger.py` (now unignored) and redeploy so the backend includes the token logging module in production builds.
- When hosting the frontend on a secure domain, either run the UI locally or configure `VITE_OLLAMA_BASE_URL` to an HTTPS-accessible tunnel so local Ollama models remain available; update deployment secrets accordingly before the next release.
- After supplying an OpenAI API key (guest or authenticated user), confirm the refreshed model list includes GPT options in production; if not, inspect backend logs for `/api/analysis/models/available` to verify Bearer tokens are forwarded and cache entries resolve.
- Smoke-test `ModelSelection`, `ModelSelectComponent`, and the multi-analysis tabs to confirm the shared model types behave as expected after redeploy (local models listed, auth-protected cloud models appear once keys are supplied).
- Update Railway (and any other hosted environments) to set `MONGODB_TLS=true` and, if using self-signed certs, `MONGODB_TLS_ALLOW_INVALID_CERTIFICATES=true` or provide `MONGODB_TLS_CA_FILE`, then redeploy to verify MongoDB health check passes. After redeploy, review the enhanced MongoDB connection logs to capture detailed failure diagnostics if the handshake continues to fail. The logs now print sanitized Mongo URIs, all applied client options, and any server-selection details reported by PyMongo to speed up Atlas troubleshooting. If you previously pointed `MONGODB_TLS_CA_FILE` at `/app/certs/rds-combined-ca-bundle.pem`, remove that variable so the deployment uses the refreshed system CA bundle.
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
