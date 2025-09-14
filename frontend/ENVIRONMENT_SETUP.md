# Environment Configuration Guide

This guide explains how to configure the frontend to automatically switch between local development and production backends.

## Automatic Environment Detection

The application automatically detects your environment and configures the backend URL accordingly:

### Local Development
- **When**: Running on `localhost` or `127.0.0.1`
- **Backend URL**: `http://localhost:8080` (default)
- **Vite Proxy**: Enabled for `/api` routes

### Production
- **When**: Running on any other hostname
- **Backend URL**: `https://backend-production-712a.up.railway.app`
- **Vite Proxy**: Not applicable (static build)

## Environment Variables

You can override the default backend URL using environment variables:

### For Local Development
Create a `.env.local` file in the frontend directory:

```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8080
VITE_ENVIRONMENT=development
```

### For Production Builds
Set environment variables before building:

```bash
# Build with custom backend
VITE_API_BASE_URL=https://your-custom-backend.com npm run build

# Or build with default Railway backend
npm run build
```

## Configuration File

The environment configuration is handled by `src/config/environment.ts`:

```typescript
import { config } from '../config/environment';

// Access configuration
console.log(config.apiBaseUrl);    // Current backend URL
console.log(config.environment);   // 'development' or 'production'
console.log(config.isLocal);       // true if running locally
```

## Development Workflow

### 1. Local Development with Local Backend
```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: Start frontend
cd frontend
npm run dev
```
- Frontend: `http://localhost:3001`
- Backend: `http://localhost:8080`
- API calls: Automatically proxied through Vite

### 2. Local Development with Remote Backend
```bash
# Create .env.local
echo "VITE_API_BASE_URL=https://backend-production-712a.up.railway.app" > .env.local

# Start frontend
npm run dev
```
- Frontend: `http://localhost:3001`
- Backend: Railway production backend
- API calls: Direct to Railway (no proxy)

### 3. Production Deployment
```bash
# Build for production (uses Railway backend by default)
npm run build

# Or build with custom backend
VITE_API_BASE_URL=https://your-backend.com npm run build
```

## Troubleshooting

### Backend Not Connecting
1. Check if backend is running: `curl http://localhost:8080/health`
2. Verify environment config in browser console
3. Check network tab for failed requests

### CORS Issues
- Local development: Vite proxy should handle CORS
- Production: Ensure backend CORS is configured for your domain

### Environment Variables Not Working
- Ensure `.env.local` is in the frontend directory
- Restart the dev server after changing environment variables
- Check that variables start with `VITE_` prefix

## Configuration Examples

### Multiple Environments
```bash
# Development
VITE_API_BASE_URL=http://localhost:8080

# Staging
VITE_API_BASE_URL=https://staging-backend.railway.app

# Production
VITE_API_BASE_URL=https://backend-production-712a.up.railway.app
```

### Debug Mode
The configuration logs to console in development mode:
```
🔧 Environment Config: {
  apiBaseUrl: "http://localhost:8080",
  environment: "development",
  isLocal: true,
  hostname: "localhost",
  dev: true
}
```
