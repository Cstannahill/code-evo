# CURL Commands for API Testing

## Analysis

### curl

```bash
curl http://localhost:8080/api/analysis/status
```

## Test AI Code Analysis

```bash
curl -X POST http://localhost:8080/api/analysis/code \
 -H "Content-Type: application/json" \
 -d "{\"code\": \"const [count, setCount] = useState(0)\", \"language\": \"javascript\"}"
```

## Test Repository Analysis

```bash
curl -X POST http://localhost:8080/api/repositories \
 -H "Content-Type: application/json" \
 -d "{\"url\": \"https://github.com/facebook/react\", \"branch\": \"main\"}"
```

```bash
# Analysis Results
curl http://localhost:8080/api/repositories/[NEW_REPO_ID]/analysis
# Insights
curl http://localhost:8080/api/analysis/insights/[NEW_REPO_ID]
# Patterns
curl http://localhost:8080/api/analysis/patterns
```

## Tests

```bash
curl http://localhost:8080/api/repositories/c92fdf38-e709-4bc6-a479-2d3abb4008b2/analysis
curl http://localhost:8080/api/analysis/insights/c92fdf38-e709-4bc6-a479-2d3abb4008b2
```

## Reload Server

### In Backend Directory

```bash
python -m uvicorn app.main:app --reload --port 8080
```
