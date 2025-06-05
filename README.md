# 🧠 Code Evolution Tracker

## Enterprise-Grade AI-Powered Code Analysis Platform

A sophisticated system that analyzes Git repositories using multiple AI models to discover coding patterns, track technology evolution, and provide actionable insights for software development teams.

![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![React](https://img.shields.io/badge/react-19.1.0+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)
![Multi-Model AI](https://img.shields.io/badge/AI-Multi--Model-purple)

> **🎯 Production Status**: Fully operational with local AI models (CodeLlama 7B/13B, CodeGemma 7B). Enterprise features include multi-model comparison, advanced visualizations, and production-grade error handling.

## ✨ Enterprise Features

### 🤖 **Multi-Model AI Analysis**

- **Local Models**: CodeLlama 7B/13B, CodeGemma 7B (fully operational)
- **Cloud Models**: GPT-4, GPT-3.5 Turbo, Claude Sonnet (API key required)
- **Consensus Analysis**: Multi-model comparison with performance benchmarking
- **Real-time Processing**: Async analysis with live progress updates

### 📊 **Advanced Analytics & Visualization**

- **10 Specialized Chart Components**: Pattern heatmaps, technology radar, evolution timelines, learning progression
- **Interactive Dashboards**: Multi-tab analysis interface with 544+ lines of dashboard code
- **Pattern Detection**: React patterns, modern JavaScript, architecture patterns, anti-patterns
- **Technology Evolution**: Track adoption curves and complexity trends over time
- **Word Cloud Visualization**: Pattern frequency analysis with interactive word clouds
- **Technology Radar**: Multi-dimensional technology adoption tracking
- **Learning Progression Charts**: Visualize coding skill development over time
- **Code Quality Metrics**: Comprehensive quality scoring and trend analysis
- **Technology Relationship Graphs**: Dependency and integration visualizations

### 🏗️ **Production Architecture**

- **Backend**: FastAPI with async lifecycle, global exception handling, structured logging
- **Frontend**: React 19.1.0 with TypeScript, 51 analyzed files, comprehensive component system
- **Database Stack**: SQLite + MongoDB + ChromaDB + Redis for multi-tier data management
- **Error Handling**: Production-ready error boundaries with retry mechanisms and detailed logging
- **Type Safety**: Comprehensive TypeScript with strict typing across 33 React components
- **Component System**: 10 chart components, 11 feature components, 3 AI integration components
- **State Management**: TanStack Query v5.77.0 with optimistic updates and intelligent caching
- **UI Framework**: Radix UI primitives with custom CTAN brand styling system

### 🔧 **Developer Experience**

- **Real-time Status**: Live backend and AI service monitoring
- **Accessibility**: WCAG compliant components with keyboard navigation
- **Performance**: Code splitting, lazy loading, virtual scrolling for large datasets
- **Responsive Design**: Mobile-first approach with dark theme support

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (tested with 3.11, 3.12)
- **Node.js 18+** (recommended: 20+)
- **pnpm** (package manager - install with `npm install -g pnpm`)
- **Ollama** (for local AI models - required)
- **Git** (for repository cloning)
- **Docker** (optional, for PostgreSQL/Redis services)

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/Cstannahill/code-evo
cd code-evolution-tracker

# Make scripts executable (Linux/macOS)
chmod +x start.sh stop.sh test_setup.sh
```

### 2. Install & Configure Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows - Download from https://ollama.com

# Start Ollama service
ollama serve

# Pull required models (5-10 minutes download per model)
ollama pull codellama:7b      # 3.8GB - Fast inference
ollama pull codellama:13b     # 7.4GB - Better accuracy
ollama pull codegemma:7b      # 4.9GB - Google's code model

# Optional: Verify models are working
ollama run codellama:7b "Hello world in Python"
```

````

### 3. Start Everything

```bash
# One command to start everything!
./start.sh
````

This will:

- Start Docker services (PostgreSQL, Redis, ChromaDB)
- Set up Python virtual environment
- Install all dependencies
- Create database tables
- Start backend API server
- Start React frontend

### 4. Access the Application

- **Frontend**: <http://localhost:3000>
- **API**: <http://localhost:8080>
- **API Docs**: <http://localhost:8080/docs>

### 5. Test Your Setup

```bash
# Run comprehensive tests
./test_setup.sh
```

### 6. Analyze Your First Repository

1. Open <http://localhost:3000>
2. Enter a GitHub repository URL (e.g., `https://github.com/facebook/react`)
3. Click "Analyze Repository"
4. Wait 2-5 minutes for analysis to complete
5. Explore the results!

## 🏗️ Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   FastAPI       │    │   AI Services   │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Ollama)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     SQLITE      │    │     Redis       │    │    ChromaDB     │
│   (Metadata)    │    │    (Cache)      │    │   (Vectors)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

- **Frontend (React)**: Interactive UI with dashboards, timelines, and pattern viewers
- **Backend (FastAPI)**: RESTful API with async processing and WebSocket support
- **AI Layer (Ollama + LangChain)**: Local AI models for pattern detection and analysis
- **Vector Database (ChromaDB)**: Stores code embeddings for similarity search
- **SQLite**: Stores metadata, relationships, and analysis results
- **Redis**: Caching and background job queue

## 📊 What It Analyzes

### Coding Patterns (Advanced Detection)

- **React Patterns**: Hooks (useState, useEffect, useCallback), Context API, Custom Hooks, Memoization
- **Modern JavaScript**: Async/await, Promises, Arrow functions, Destructuring, ES6+ features
- **TypeScript Patterns**: Type definitions, Interfaces, Generics, Union types, Strict typing
- **Architecture Patterns**: Factory, Observer, Strategy, Command, Container/Presentational
- **Anti-patterns**: Code smells, problematic patterns, performance bottlenecks, security issues
- **Functional Programming**: Pure functions, Immutability, Higher-order functions, Composition

### Technology Evolution (Comprehensive Tracking)

- **Languages**: JavaScript, TypeScript, Python, Java, Go, Rust, HTML, CSS, SQL
- **Frontend Frameworks**: React, Angular, Vue, Svelte, Next.js, Nuxt.js
- **Backend Frameworks**: Django, Flask, FastAPI, Express, Koa, NestJS
- **Libraries & Tools**: Testing frameworks, Build tools, CI/CD systems, Database systems
- **Package Managers**: npm, yarn, pnpm, pip, cargo, go mod
- **Development Tools**: ESLint, Prettier, Webpack, Vite, Docker, Kubernetes

### Insights Generated (AI-Powered)

- **Learning Velocity**: Technology adoption speed and learning curve analysis
- **Complexity Trends**: Code complexity evolution with quality metrics
- **Pattern Maturity**: Sophistication level of implemented patterns
- **Technology Recommendations**: Personalized learning paths based on your evolution
- **Code Quality Scores**: Maintainability, readability, and performance assessments
- **Team Comparisons**: Multi-developer pattern analysis and collaboration insights

## 🔧 Configuration

### Environment Variables

Create `backend/.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql://codetracker:codetracker@localhost:5432/codetracker
SQLITE_URL=sqlite:///./code_evolution.db

# AI Models - Local (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=codellama:13b
OLLAMA_EMBED_MODEL=nomic-embed-text

# AI Models - Cloud (Optional)
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here

# Vector Database
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=code_patterns

# Cache Configuration
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# GitHub Integration (Optional)
GITHUB_TOKEN=your-github-token-here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Analysis Settings
MAX_COMMITS_PER_ANALYSIS=1000
ANALYSIS_BATCH_SIZE=50
PATTERN_CONFIDENCE_THRESHOLD=0.7
```

### Frontend Configuration

Create `frontend/.env`:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8080

# Feature Flags
VITE_ENABLE_CLOUD_MODELS=true
VITE_ENABLE_MULTI_MODEL_COMPARISON=true
VITE_ENABLE_REAL_TIME_ANALYSIS=true

# UI Configuration
VITE_DEFAULT_THEME=dark
VITE_ENABLE_ANALYTICS=false
```

### Customizing Analysis

Edit `backend/app/services/ai_service.py` to:

- **Add New Patterns**: Extend pattern detection rules
- **Custom Prompts**: Modify AI analysis prompts for specific domains
- **Language Support**: Add support for new programming languages
- **Scoring Models**: Customize complexity and quality scoring algorithms
- **Analysis Filters**: Configure what files and patterns to analyze

### Model Configuration

Available AI models and their capabilities:

```yaml
Local Models (Ollama):
  codellama:7b:
    size: 3.8GB
    strengths: [code_completion, pattern_detection]
    context_window: 4096
  codellama:13b:
    size: 7.4GB
    strengths: [architecture_analysis, complex_patterns]
    context_window: 4096
  codegemma:7b:
    size: 4.9GB
    strengths: [google_practices, performance_patterns]
    context_window: 8192

Cloud Models (API Required):
  gpt-4:
    provider: OpenAI
    strengths: [comprehensive_analysis, insights]
    context_window: 128000
  gpt-3.5-turbo:
    provider: OpenAI
    strengths: [fast_analysis, cost_effective]
    context_window: 16384
  claude-3-sonnet:
    provider: Anthropic
    strengths: [detailed_explanations, safety]
    context_window: 200000
```

## 🔍 API Usage

### Analyze a Repository

```bash
curl -X POST "http://localhost:8080/api/repositories" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/username/repo", "branch": "main"}'
```

### Get Analysis Results

```bash
curl "http://localhost:8080/api/repositories/{repo_id}/analysis"
```

### Analyze Code Snippet

```bash
curl -X POST "http://localhost:8080/api/analysis/code" \
  -H "Content-Type: application/json" \
  -d '{"code": "const [count, setCount] = useState(0);", "language": "javascript"}'
```

### Get Technology Timeline

```bash
curl "http://localhost:8080/api/repositories/{repo_id}/timeline"
```

## 🧪 Testing

### Run All Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

# End-to-end tests
./test_setup.sh
```

### Test Individual Components

```bash
# Test AI service
cd backend
python -c "from app.services.ai_service import AIService; print('AI Service OK')"

# Test database
python -c "from app.core.database import engine; print('Database OK')"

# Test API endpoints
curl http://localhost:8080/health
```

## 📈 Performance

### Optimization Settings

- **Analysis Batch Size**: 50 commits per batch (configurable)
- **Pattern Detection**: Rule-based + AI hybrid approach
- **Caching**: Redis for analysis results (1 hour TTL)
- **Background Processing**: Async analysis with progress updates

### Scaling Considerations

- **Database**: PostgreSQL with proper indexing
- **AI Processing**: Ollama runs locally (can scale to multiple instances)
- **Vector Search**: ChromaDB auto-scales with data
- **API**: FastAPI with async support handles concurrent requests

## 🛠️ Development

### Project Structure (Comprehensive)

```text
code-evolution-tracker/
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── core/             # Database, config, middleware
│   │   ├── api/              # REST API endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic & AI services
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── tasks/            # Background task processing
│   │   └── utils/            # Utility functions
│   ├── chroma_db/            # Vector database storage
│   ├── tests/                # Backend test suite
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # React components (51 files)
│   │   │   ├── ui/           # 9 reusable UI components
│   │   │   ├── charts/       # 10 visualization components
│   │   │   ├── features/     # 11 feature components
│   │   │   └── ai/           # 3 AI integration components
│   │   ├── hooks/            # 7 custom React hooks
│   │   ├── types/            # 6 TypeScript type definitions
│   │   ├── api/              # API client (159 lines)
│   │   ├── lib/              # Utilities & logger (538 lines)
│   │   └── styles/           # Custom CSS & themes
│   ├── docs/                 # Frontend documentation
│   ├── logs/                 # Frontend logs
│   └── package.json          # Node.js dependencies
├── docker-compose.yml        # Service orchestration
├── project-context.md        # Comprehensive project documentation
└── README.md                 # This file
```

### Component Architecture Details

**Chart Components (Data Visualization)**:

- `PatternHeatmap` - Interactive pattern density visualization
- `TechRadar` - Technology adoption radar with quadrants
- `TechnologyEvolutionChart` - Timeline-based technology trends
- `PatternWordCloud` - Dynamic word cloud for pattern frequency
- `LearningProgressionChart` - Skill development visualization
- `ComplexityEvolutionChart` - Code complexity trend analysis
- `CodeQualityMetrics` - Quality score dashboards
- `TechnologyRelationshipGraph` - Interactive dependency graphs
- `TechStackComposition` - Technology distribution charts
- `PatternTimeline` - Pattern adoption timeline

**Feature Components (Business Logic)**:

- `MultiAnalysisDashboard` - Primary analysis orchestrator
- `AnalysisDashboard` - Multi-tab analysis interface (544 lines)
- `ModelComparisonDashboard` - Multi-model comparison interface
- `InsightsDashboard` - AI-generated insights display
- `CodeQualityDashboard` - Quality metrics interface
- `Dashboard` - Main repository analysis interface
- `PatternDeepDive` - Detailed pattern analysis
- `EvolutionMetrics` - Code evolution tracking
- `TechnologyTimeline` - Technology adoption timeline
- `PatternViewer` - Pattern detection results display
- `RepositoryForm` - Repository input and validation

### Adding New Features

#### 1. New Visualization Component

```typescript
// src/components/charts/MyNewChart.tsx
import React from "react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis } from "recharts";

interface MyNewChartProps {
  data: ChartData[];
  title: string;
}

export const MyNewChart: React.FC<MyNewChartProps> = ({ data, title }) => {
  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        {/* Chart implementation */}
      </ResponsiveContainer>
    </div>
  );
};
```

#### 2. New Pattern Detection

```python
# backend/app/services/ai_service.py
def detect_custom_pattern(self, code: str) -> List[Pattern]:
    """Add custom pattern detection logic"""
    patterns = []

    # Your pattern detection logic here
    if "custom_pattern" in code:
        patterns.append(Pattern(
            name="custom_pattern",
            description="Custom pattern detected",
            complexity="intermediate",
            confidence=0.85
        ))

    return patterns
```

#### 3. New API Endpoint

```python
# backend/app/api/custom.py
from fastapi import APIRouter, Depends
from app.schemas.custom import CustomRequest, CustomResponse

router = APIRouter(prefix="/api/custom", tags=["custom"])

@router.post("/analyze", response_model=CustomResponse)
async def analyze_custom(request: CustomRequest):
    """Custom analysis endpoint"""
    # Implementation here
    return CustomResponse(result="analysis complete")
```

### Development Workflow

#### Backend Development

```bash
# Setup Python environment
cd backend/
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server with auto-reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Run tests
python -m pytest tests/ -v

# Database migrations
python create_db.py
```

#### Frontend Development

```bash
# Setup Node.js environment
cd frontend/
pnpm install  # or npm install

# Run development server
pnpm dev  # or npm run dev

# Run tests
pnpm test  # or npm test

# Build for production
pnpm build  # or npm run build

# Lint and format
pnpm lint  # or npm run lint
pnpm format  # or npm run format
```

#### Full Stack Development

```bash
# Start all services
./start.sh

# Watch logs
tail -f backend/code_evolution.log
tail -f frontend/logs/frontend.log

# Stop all services
./stop.sh
```

### Development Tools & IDE Setup

#### VS Code Extensions (Recommended)

```json
{
  "recommendations": [
    "ms-python.python",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-eslint",
    "ms-python.black-formatter",
    "charliermarsh.ruff"
  ]
}
```

#### Development Environment Variables

```bash
# Development overrides
DEBUG=true
LOG_LEVEL=DEBUG
OLLAMA_TIMEOUT=120
ENABLE_CORS=true
FRONTEND_DEV_URL=http://localhost:5173
```

## 🚨 Troubleshooting

### Common Issues

**Backend won't start**

```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi

# Check database connection
docker-compose ps
```

## Frontend won't start

```bash
# Check Node version
node --version  # Should be 18+

# Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## Ollama issues

```bash
# Check if Ollama is running
ollama list

# Restart Ollama
killall ollama
ollama serve

# Re-pull models
ollama pull codellama:13b
ollama pull nomic-embed-text
```

## Analysis stuck

```bash
# Check backend logs
tail -f backend.log

# Check database
docker-compose logs postgres

# Restart services
./stop.sh
./start.sh
```

### Performance Issues

**Analysis too slow**

- Reduce analysis batch size in `git_service.py`
- Use smaller Ollama models (CodeLlama 7B instead of 13B)
- Limit commit history (reduce `max_commits` parameter)

**High memory usage**

- Restart Ollama periodically
- Clear Redis cache: `redis-cli FLUSHALL`
- Limit concurrent analyses

## 📚 Learning Resources

### Understanding the Tech Stack

- **FastAPI**: [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- **LangChain**: [LangChain Introduction](https://python.langchain.com/docs/get_started/introduction)
- **Ollama**: [Ollama GitHub](https://github.com/ollama/ollama)
- **ChromaDB**: [ChromaDB Documentation](https://docs.trychroma.com/)
- **React**: [React Learning Guide](https://react.dev/learn)

### AI & ML Concepts

- **Vector Embeddings**: [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- **Pattern Recognition**: [Pattern Recognition Overview](https://en.wikipedia.org/wiki/Pattern_recognition)
- **Code Analysis**: [Static Program Analysis](https://en.wikipedia.org/wiki/Static_program_analysis)

## 🎯 Next Steps

### Immediate Improvements

- [ ] Add more programming languages (Go, Rust, C++)
- [ ] Implement real-time analysis streaming
- [ ] Add pattern evolution recommendations
- [ ] Create pattern comparison between developers

### Advanced Features

- [ ] Multi-repository analysis
- [ ] Team collaboration features
- [ ] Custom pattern definitions
- [ ] Integration with GitHub/GitLab webhooks
- [ ] Advanced ML models for code classification

### Scaling

- [ ] Kubernetes deployment
- [ ] Multi-tenant architecture
- [ ] Distributed processing
- [ ] SaaS version

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama** for local AI models
- **LangChain** for AI orchestration
- **FastAPI** for the excellent web framework
- **React** for the frontend framework
- **ChromaDB** for vector storage

---

**Happy coding and analyzing!** 🚀

For questions or issues, please open a GitHub issue or check the troubleshooting section above.
