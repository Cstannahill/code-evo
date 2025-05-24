#!/bin/bash

# Code Evolution Tracker - Recovery Setup Script
# This will get you back to working AI analysis

echo "🚀 Code Evolution Tracker - Recovery Setup"
echo "=========================================="

# 1. Clean up old environment
echo "🧹 Cleaning up old dependencies..."
pip uninstall -y chromadb langchain sentence-transformers numpy
pip cache purge

# 2. Install fixed requirements
echo "📦 Installing fixed dependencies..."
pip install --upgrade pip

# Install in specific order to avoid conflicts
pip install numpy==1.24.3
pip install chromadb==0.4.15
pip install langchain==0.0.342
pip install langchain-community==0.0.5
pip install ollama==0.1.7

# Install remaining requirements
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install python-jose[cryptography]==3.3.0
pip install python-multipart==0.0.6
pip install sqlalchemy==2.0.23
pip install redis==5.0.1
pip install GitPython==3.1.40
pip install sentence-transformers==2.2.2
pip install pydantic==2.5.0
pip install pydantic-settings==2.1.0
pip install python-dotenv==1.0.0
pip install httpx==0.25.2

echo "✅ Dependencies installed successfully"

# 3. Start Redis (if not running)
echo "🗄️  Starting Redis..."
if ! pgrep -x "redis-server" > /dev/null; then
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes
        echo "✅ Redis started"
    else
        echo "⚠️  Redis not installed. Install with:"
        echo "   macOS: brew install redis"
        echo "   Ubuntu: sudo apt install redis-server"
        echo "   Windows: Use Docker or WSL"
    fi
else
    echo "✅ Redis already running"
fi

# 4. Check/Install Ollama
echo "🤖 Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama already installed"
fi

# 5. Start Ollama and download models
echo "📥 Starting Ollama and downloading models..."
ollama serve &
sleep 5

echo "Downloading CodeLlama (this may take a while)..."
ollama pull codellama:7b

# Test Ollama
echo "🧪 Testing Ollama..."
if ollama list | grep -q "codellama"; then
    echo "✅ Ollama working with CodeLlama"
else
    echo "⚠️  Ollama setup incomplete"
fi

# 6. Test Python imports
echo "🧪 Testing Python imports..."
python -c "
try:
    import chromadb
    import langchain
    import ollama
    import redis
    print('✅ All imports working')
except ImportError as e:
    print(f'❌ Import error: {e}')
"

# 7. Initialize database
echo "🗄️  Initializing database..."
cd backend
python -c "
from app.core.database import create_tables
create_tables()
print('✅ Database initialized')
"

# 8. Test the API
echo "🧪 Testing API..."
python -c "
import asyncio
from app.services.ai_service import AIService

async def test():
    ai = AIService()
    status = ai.get_status()
    print(f'AI Service Status: {status}')
    
    if status['ollama_available']:
        result = await ai.analyze_code_pattern('const [count, setCount] = useState(0)', 'javascript')
        print(f'✅ AI Analysis working: {len(result[\"combined_patterns\"])} patterns detected')
    else:
        print('⚠️  AI not available - check Ollama setup')

asyncio.run(test())
"

echo ""
echo "🎉 Recovery Setup Complete!"
echo "=========================="
echo ""
echo "🚀 Start the server:"
echo "   cd backend && python -m uvicorn app.main:app --reload --port 8080"
echo ""
echo "🧪 Test endpoints:"
echo "   http://localhost:8080/health"
echo "   http://localhost:8080/api/repositories"
echo ""
echo "🤖 AI Status check:"
echo "   curl http://localhost:8080/api/analysis/status"
echo ""
echo "📊 Services running:"
echo "   - FastAPI: http://localhost:8080"
echo "   - Redis: localhost:6379"
echo "   - Ollama: http://localhost:11434"
echo "   - SQLite: ./code_evolution.db"
echo "   - ChromaDB: ./chroma_db/"
echo ""