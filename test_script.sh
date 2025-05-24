#!/bin/bash

# Code Evolution Tracker - Comprehensive Test Script
# Tests the entire setup end-to-end

echo "🧪 Testing Code Evolution Tracker Setup..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    print_test "$test_name"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        print_pass "$test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_fail "$test_name"
        return 1
    fi
}

# Test 1: Docker Services
print_test "Checking Docker services..."
run_test "PostgreSQL is running" "docker-compose ps | grep postgres | grep -q Up"
run_test "Redis is running" "docker-compose ps | grep redis | grep -q Up"
run_test "ChromaDB is running" "docker-compose ps | grep chromadb | grep -q Up"

# Test 2: Database Connection
print_test "Testing database connection..."
run_test "Database connection" "cd backend && source venv/bin/activate && python -c 'from app.core.database import engine; from sqlalchemy import text; engine.connect().execute(text(\"SELECT 1\"))'"

# Test 3: Ollama
print_test "Testing Ollama..."
run_test "Ollama is installed" "command -v ollama"
run_test "CodeLlama model is available" "ollama list | grep -q codellama"
run_test "Embedding model is available" "ollama list | grep -q nomic-embed-text"

# Test 4: Backend API
print_test "Testing backend API..."
run_test "Backend health check" "curl -s http://localhost:8080/health | grep -q healthy"
run_test "Backend repositories endpoint" "curl -s http://localhost:8080/api/repositories | python -c 'import json, sys; json.load(sys.stdin)'"

# Test 5: Frontend
print_test "Testing frontend..."
run_test "Frontend is accessible" "curl -s http://localhost:3000 | grep -q 'Code Evolution Tracker'"

# Test 6: End-to-End Analysis Test
print_test "Running end-to-end analysis test..."

# Create test repository analysis
TEST_REPO="https://github.com/octocat/Hello-World"
ANALYSIS_RESULT=$(curl -s -X POST "http://localhost:8080/api/repositories" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$TEST_REPO\", \"branch\": \"master\"}")

if echo "$ANALYSIS_RESULT" | grep -q "id"; then
    REPO_ID=$(echo "$ANALYSIS_RESULT" | python -c "import json, sys; print(json.load(sys.stdin)['id'])")
    print_pass "Repository analysis initiated (ID: ${REPO_ID:0:8}...)"
    
    # Wait for analysis to complete (up to 2 minutes)
    print_test "Waiting for analysis to complete..."
    for i in {1..24}; do
        sleep 5
        STATUS=$(curl -s "http://localhost:8080/api/repositories/$REPO_ID" | python -c "import json, sys; print(json.load(sys.stdin).get('status', 'unknown'))")
        
        if [ "$STATUS" = "completed" ]; then
            print_pass "Analysis completed successfully"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            break
        elif [ "$STATUS" = "failed" ]; then
            print_fail "Analysis failed"
            break
        fi
        
        if [ $i -eq 24 ]; then
            print_warn "Analysis timeout (may still be processing)"
        fi
    done
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
else
    print_fail "Repository analysis failed to start"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

# Test 7: Pattern Detection
print_test "Testing pattern detection..."
CODE_SNIPPET='const [count, setCount] = useState(0);'
PATTERN_RESULT=$(curl -s -X POST "http://localhost:8080/api/analysis/code" \
  -H "Content-Type: application/json" \
  -d "{\"code\": \"$CODE_SNIPPET\", \"language\": \"javascript\"}")

run_test "Code pattern analysis" "echo '$PATTERN_RESULT' | grep -q 'pattern_analysis'"

# Test 8: AI Service
print_test "Testing AI integration..."
run_test "Ollama service responds" "curl -s http://localhost:11434/api/tags | python -c 'import json, sys; json.load(sys.stdin)'"

# Test Summary
echo ""
echo "🏁 Test Summary"
echo "==============="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $((TOTAL_TESTS - PASSED_TESTS))"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✅ All tests passed! Your setup is working correctly.${NC}"
    echo ""
    echo "🎯 Ready for Production Use!"
    echo "• Frontend: http://localhost:3000"
    echo "• Backend API: http://localhost:8080"
    echo "• API Docs: http://localhost:8080/docs"
    echo ""
    echo "🔄 Next Steps:"
    echo "1. Try analyzing your own repository"
    echo "2. Explore the patterns and insights"
    echo "3. Check out the technology timeline"
    echo "4. Use the API for custom integrations"
    
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the issues above.${NC}"
    echo ""
    echo "🔧 Common Issues:"
    echo "• Make sure Docker is running: docker-compose up -d"
    echo "• Ensure Ollama is installed and models are pulled"
    echo "• Check if ports 3000, 8080, 5432, 6379, 8000 are available"
    echo "• Verify Python virtual environment is activated"
    echo ""
    echo "📋 Troubleshooting:"
    echo "• Backend logs: tail -f backend.log"
    echo "• Frontend logs: tail -f frontend.log"
    echo "• Docker logs: docker-compose logs"
    
    exit 1
fi