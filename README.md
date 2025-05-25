# 🧠 Code Evolution Tracker

An AI-powered system that analyzes your Git repositories to discover coding patterns, track technology adoption, and understand your programming evolution over time.

![Code Evolution Tracker](https://img.shields.io/badge/status-MVP%20Ready-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![React](https://img.shields.io/badge/react-18+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green)

## ✨ Features

- **🔍 Pattern Detection**: AI-powered identification of coding patterns (React hooks, async/await, design patterns)
- **📈 Technology Timeline**: Visualize your technology adoption over time
- **🧪 Evolution Analysis**: Track how your coding style and complexity evolves
- **💡 AI Insights**: Get personalized recommendations and learning insights
- **🔄 Real-time Analysis**: Background processing with live updates
- **📊 Rich Visualizations**: Interactive charts and timelines
- **🎯 Pattern Comparison**: Compare patterns across repositories

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Ollama** (for local AI models)
- **Git**

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/Cstannahill/code-evo
cd code-evolution-tracker

# Make scripts executable
chmod +x start.sh stop.sh test_setup.sh
```

### 2. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows - Download from https://ollama.com

# Pull required models (this takes 5-10 minutes)
ollama pull codellama:13b
ollama pull nomic-embed-text
```

### 3. Start Everything

```bash
# One command to start everything!
./start.sh
```

This will:

- Start Docker services (PostgreSQL, Redis, ChromaDB)
- Set up Python virtual environment
- Install all dependencies
- Create database tables
- Start backend API server
- Start React frontend

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

### 5. Test Your Setup

```bash
# Run comprehensive tests
./test_setup.sh
```

### 6. Analyze Your First Repository

1. Open http://localhost:3000
2. Enter a GitHub repository URL (e.g., `https://github.com/facebook/react`)
3. Click "Analyze Repository"
4. Wait 2-5 minutes for analysis to complete
5. Explore the results!

## 🏗️ Architecture

```
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

### Coding Patterns

- **React Patterns**: Hooks (useState, useEffect), Context, Memoization
- **JavaScript Patterns**: Async/await, Promises, ES6+ features
- **Python Patterns**: Decorators, Context managers, List comprehensions
- **Architecture Patterns**: Factory, Observer, Strategy patterns
- **Anti-patterns**: Code smells and problematic patterns

### Technology Evolution

- **Languages**: JavaScript, TypeScript, Python, Java, Go, Rust, etc.
- **Frameworks**: React, Angular, Vue, Django, Flask, Express, etc.
- **Libraries**: Tracks adoption and usage patterns
- **Tools**: Build tools, testing frameworks, CI/CD systems

### Insights Generated

- **Learning Velocity**: How quickly you adopt new technologies
- **Complexity Trends**: Whether your code complexity increases over time
- **Pattern Maturity**: How sophisticated your patterns become
- **Technology Recommendations**: What to learn next based on your evolution

## 🔧 Configuration

### Environment Variables

Create `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://codetracker:codetracker@localhost:5432/codetracker

# AI Models
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=codellama:13b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Optional: OpenAI for advanced features
OPENAI_API_KEY=your-openai-key

# Optional: GitHub token for private repos
GITHUB_TOKEN=your-github-token
```

### Customizing Analysis

Edit `backend/app/services/ai_service.py` to:

- Add new pattern detection rules
- Customize AI prompts
- Add support for new languages
- Modify complexity scoring

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

### Project Structure

```
code-evolution-tracker/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, database, security
│   │   ├── api/           # FastAPI endpoints
│   │   ├── models/        # SQLAlchemy models
│   │   ├── services/      # Business logic
│   │   ├── schemas/       # Pydantic schemas
│   │   └── agents/        # AI agents (future)
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utilities
│   └── package.json
├── docker-compose.yml     # Services
├── start.sh              # Startup script
├── stop.sh               # Shutdown script
└── test_setup.sh         # Test script
```

### Adding New Features

1. **New Pattern Detection**: Add rules to `ai_service.py`
2. **New Visualizations**: Create React components in `frontend/src/components`
3. **New API Endpoints**: Add to `backend/app/api/`
4. **New AI Models**: Update Ollama configuration

### Running in Development

```bash
# Backend only
cd backend
source venv/bin/activate
python -m app.main

# Frontend only
cd frontend
npm start

# Watch mode with auto-reload
# Backend: FastAPI auto-reloads on file changes
# Frontend: React auto-reloads on file changes
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

**Frontend won't start**

```bash
# Check Node version
node --version  # Should be 18+

# Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Ollama issues**

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

**Analysis stuck**

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
- Use smaller Ollama models (codellama:7b instead of 13b)
- Limit commit history (reduce `max_commits` parameter)

**High memory usage**

- Restart Ollama periodically
- Clear Redis cache: `redis-cli FLUSHALL`
- Limit concurrent analyses

## 📚 Learning Resources

### Understanding the Tech Stack

- **FastAPI**: https://fastapi.tiangolo.com/tutorial/
- **LangChain**: https://python.langchain.com/docs/get_started/introduction
- **Ollama**: https://github.com/ollama/ollama
- **ChromaDB**: https://docs.trychroma.com/
- **React**: https://react.dev/learn

### AI & ML Concepts

- **Vector Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **Pattern Recognition**: https://en.wikipedia.org/wiki/Pattern_recognition
- **Code Analysis**: https://en.wikipedia.org/wiki/Static_program_analysis

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
