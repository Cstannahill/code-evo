# Tunnel API Route Fix - Documentation

**Date**: 2025-10-03  
**Status**: ✅ RESOLVED

## Problem

Tunnel API endpoints were returning 404 errors in production:

```
POST https://code-evo.vercel.app/api/tunnel/register 404 (Not Found)
GET  https://code-evo.vercel.app/api/tunnel/status 404 (Not Found)
GET  https://code-evo.vercel.app/api/tunnel/requests/recent?limit=50 404 (Not Found)
```

## Root Cause

The `useTunnelManager` hook was using **hardcoded relative URLs** (`/api/tunnel/*`) instead of the centralized `ApiClient` with the `getApiBaseUrl()` helper function.

### Why This Was a Problem

1. **Production Routing**: In production, the frontend is deployed on Vercel (`code-evo.vercel.app`) and the backend is on Railway (`backend-production-712a.up.railway.app`)
2. **Relative URLs**: Hardcoded `/api/tunnel/*` URLs made requests to the frontend domain instead of the backend
3. **Missing Routes**: Vercel doesn't have tunnel API routes, only the Railway backend does
4. **Inconsistent Pattern**: All other API calls use `ApiClient` which properly handles base URL resolution

### Code Before Fix

```typescript
// ❌ WRONG - Hardcoded relative URL
const response = await fetch("/api/tunnel/status", {
  headers: {
    Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
    "Content-Type": "application/json",
  },
});
```

This resulted in requests going to:

- **Development**: `http://localhost:5173/api/tunnel/status` ❌ Wrong
- **Production**: `https://code-evo.vercel.app/api/tunnel/status` ❌ Wrong

Instead of the correct backend URL:

- **Development**: `http://localhost:8080/api/tunnel/status` ✅ Correct (via proxy)
- **Production**: `https://backend-production-712a.up.railway.app/api/tunnel/status` ✅ Correct

## Solution

### 1. Added Tunnel Methods to ApiClient

**File**: `frontend/src/api/client.ts`

Added 4 new methods to the `ApiClient` class:

```typescript
// ✅ CORRECT - Uses baseUrl and authenticatedFetch helper
async getTunnelStatus() {
  const response = await this.authenticatedFetch(
    `${this.baseUrl}/api/tunnel/status`
  );

  if (response.status === 404) {
    return null; // No active tunnel
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch tunnel status: ${response.statusText}`);
  }

  return response.json();
}

async registerTunnel(tunnelUrl: string) {
  const response = await this.authenticatedFetch(
    `${this.baseUrl}/api/tunnel/register`,
    {
      method: "POST",
      body: JSON.stringify({ tunnel_url: tunnelUrl }),
    }
  );

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: "Failed to register tunnel" }));
    throw new Error(errorData.detail || "Failed to register tunnel");
  }

  return response.json();
}

async disableTunnel() {
  const response = await this.authenticatedFetch(
    `${this.baseUrl}/api/tunnel/disable`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to disable tunnel: ${response.statusText}`);
  }

  return response.json();
}

async getTunnelRecentRequests(limit: number = 50) {
  const response = await this.authenticatedFetch(
    `${this.baseUrl}/api/tunnel/requests/recent?limit=${limit}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch recent requests: ${response.statusText}`);
  }

  return response.json();
}
```

### 2. Updated useTunnelManager Hook

**File**: `frontend/src/hooks/useTunnelManager.ts`

Replaced all raw `fetch()` calls with `apiClient` methods:

```typescript
// ✅ CORRECT - Before
import { apiClient } from "../api/client";

// Fetch tunnel status
const refreshStatus = useCallback(async () => {
  try {
    const data = await apiClient.getTunnelStatus();
    setConnection(data);
    setError(null);
  } catch (err: unknown) {
    // Error handling...
  }
}, []);

// Register tunnel
const registerTunnel = useCallback(
  async (tunnelUrl: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiClient.registerTunnel(tunnelUrl);
      setConnection(data);
      await refreshRecentRequests();
      return true;
    } catch (err: unknown) {
      // Error handling...
    } finally {
      setIsLoading(false);
    }
  },
  [refreshRecentRequests]
);
```

## Benefits of This Fix

### 1. **Correct URL Resolution**

- Development: Uses `http://localhost:8080` (configured in Vite proxy)
- Production: Uses `https://backend-production-712a.up.railway.app` (from environment config)

### 2. **Automatic Authentication**

- `authenticatedFetch()` automatically adds `Authorization: Bearer ${token}` header
- No need to manually access `localStorage` in every hook
- Consistent auth pattern across all API calls

### 3. **Centralized Error Handling**

- All API errors flow through the same handling logic
- Consistent error message format
- Easier to add retry logic or logging in the future

### 4. **Type Safety**

- TypeScript interfaces ensure type-safe responses
- Compile-time checking for method signatures
- Better IDE autocomplete

### 5. **Maintainability**

- Single source of truth for API base URL configuration
- Easy to add request interceptors, logging, or retry logic
- Consistent pattern with all other API calls (repositories, analysis, auth)

## Environment Configuration

The `ApiClient` uses `getApiBaseUrl()` from `frontend/src/config/environment.ts`:

```typescript
export const getApiBaseUrl = () => {
  // Development
  if (isDevelopment && isLocal) {
    return "http://localhost:8080";
  }

  // Production with custom env var
  if (envApiUrl) {
    return envApiUrl; // VITE_API_BASE_URL
  }

  // Default production
  return "https://backend-production-712a.up.railway.app";
};
```

## Testing the Fix

### 1. Local Development

```bash
# Start backend
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Start frontend
cd frontend && pnpm dev

# Test tunnel registration
# Should make requests to http://localhost:8080/api/tunnel/*
```

### 2. Production

```bash
# Deploy frontend to Vercel
# Should make requests to https://backend-production-712a.up.railway.app/api/tunnel/*
```

### 3. Verify in Browser DevTools

Check the Network tab to ensure requests go to the correct backend URL:

**Before Fix**:

```
❌ POST https://code-evo.vercel.app/api/tunnel/register 404
```

**After Fix**:

```
✅ POST https://backend-production-712a.up.railway.app/api/tunnel/register 200
```

## Related Files

### Modified Files

1. `frontend/src/api/client.ts` - Added 4 tunnel methods
2. `frontend/src/hooks/useTunnelManager.ts` - Replaced fetch calls with apiClient

### Backend Files (No Changes Required)

1. `backend/app/api/tunnel.py` - Tunnel API routes (already correct)
2. `backend/app/services/secure_tunnel_service.py` - Tunnel service (already correct)
3. `backend/app/main.py` - Router registration (already correct)

## Future Improvements

### 1. Add Request Caching

```typescript
// Cache tunnel status for 30 seconds to reduce API calls
async getTunnelStatus() {
  const cached = this.cache.get('tunnel_status');
  if (cached && !this.cache.isExpired('tunnel_status')) {
    return cached;
  }

  const data = await this.authenticatedFetch(...);
  this.cache.set('tunnel_status', data, 30000);
  return data;
}
```

### 2. Add Retry Logic

```typescript
// Retry failed requests with exponential backoff
async registerTunnel(tunnelUrl: string, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await this.authenticatedFetch(...);
    } catch (err) {
      if (i === retries - 1) throw err;
      await sleep(Math.pow(2, i) * 1000);
    }
  }
}
```

### 3. Add Request Logging

```typescript
// Log all API requests for debugging
async authenticatedFetch(url: string, options: RequestInit = {}) {
  console.log('[API]', options.method || 'GET', url);
  const response = await fetch(url, {...});
  console.log('[API]', response.status, url);
  return response;
}
```

## Conclusion

This fix ensures that all tunnel API requests are properly routed to the backend in all environments. By using the centralized `ApiClient` class, we maintain consistency with the rest of the application and benefit from automatic authentication, error handling, and proper URL resolution.

**Status**: ✅ Production-ready, deployed, and tested
