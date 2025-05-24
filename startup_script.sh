#!/bin/bash

# Code Evolution Tracker - Complete Startup Script
# Run this from the project root directory

echo "🚀 Starting Code Evolution Tracker..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the project root directory."
    exit 1
fi

# Step 1: Start Docker services
print_status "Starting Docker services (PostgreSQL, Redis, ChromaDB)..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    print_error "Docker services failed to start. Please check Docker installation and try again."
    exit 1
fi

print_success "Docker services are running"

# Step 2: Check if Ollama is running
print_status "Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    print_error "Ollama not found. Please install Ollama first:"
    echo "curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# Check if required models are available
print_status "Checking Ollama models..."
if ! ollama list | grep -q "codellama:13b"; then
    print_warning "CodeLlama model not found. Pulling now..."
    ollama pull codellama:13b
fi

if ! ollama list | grep -q "nomic-embed-text"; then
    print_warning "Nomic embedding model not found. Pulling now..."
    ollama pull nomic-embed-text
fi

print_success "Ollama models are ready"

# Step 3: Setup and start backend
print_status "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
print_status "Installing backend dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://codetracker:codetracker@localhost:5432/codetracker
ASYNC_DATABASE_URL=postgresql+asyncpg://codetracker:codetracker@localhost:5432/codetracker

# Redis
REDIS_URL=redis://localhost:6379

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_DIR=./chroma_db

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=codellama:13b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
APP_NAME=Code Evolution Tracker
DEBUG=true
VERSION=1.0.0
EOF
fi

# Test backend
print_status "Testing backend connection..."
python -c "
import sys
sys.path.append('.')
try:
    from app.core.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    print_error "Backend setup failed. Please check the error messages above."
    exit 1
fi

# Start backend in background
print_status "Starting backend server..."
nohup python -m app.main > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid

# Wait for backend to start
sleep 5

# Test backend health
if curl -s http://localhost:8080/health > /dev/null; then
    print_success "Backend is running on http://localhost:8080"
else
    print_error "Backend failed to start. Check backend.log for details."
    exit 1
fi

# Step 4: Setup and start frontend
print_status "Setting up frontend..."
cd ../frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
print_status "Starting frontend server..."
nohup npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid

# Wait for frontend to start
sleep 10

print_success "🎉 Code Evolution Tracker is now running!"
echo ""
echo "📋 Service Status:"
echo "   • Backend API: http://localhost:8080"
echo "   • Frontend UI: http://localhost:3000"
echo "   • Database: PostgreSQL on localhost:5432"
echo "   • Cache: Redis on localhost:6379"
echo "   • Vector DB: ChromaDB on localhost:8000"
echo ""
echo "📝 Quick Start:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Enter a GitHub repository URL (e.g., https://github.com/facebook/react)"
echo "   3. Click 'Analyze Repository' and wait for analysis to complete"
echo "   4. Explore the patterns, timeline, and insights!"
echo ""
echo "🔧 Troubleshooting:"
echo "   • Backend logs: tail -f backend.log"
echo "   • Frontend logs: tail -f frontend.log"
echo "   • Stop services: ./stop.sh"
echo ""
echo "⚡ Happy analyzing!"

# Return to project root
cd ..

# Create a simple stop script
cat > stop.sh << 'EOF'
#!/bin/bash
echo "Stopping Code Evolution Tracker..."

# Stop backend
if [ -f "backend.pid" ]; then
    kill $(cat backend.pid) 2>/dev/null
    rm backend.pid
    echo "Backend stopped"
fi

# Stop frontend  
if [ -f "frontend.pid" ]; then
    kill $(cat frontend.pid) 2>/dev/null
    rm frontend.pid
    echo "Frontend stopped"
fi

# Stop Docker services
docker-compose down
echo "Docker services stopped"

echo "All services stopped"
EOF

chmod +x stop.sh

print_success "Startup complete! Use ./stop.sh to stop all services."