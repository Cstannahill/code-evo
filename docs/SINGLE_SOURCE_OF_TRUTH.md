# Single Source of Truth - Model Definitions

## Problem Identified

**Issue**: Old GPT-4 models showing in production dropdown despite backend being updated to GPT-5.

**Root Cause**: Multiple model definition sources without proper synchronization:

1. Backend API (`backend/app/api/analysis.py`) ← **Primary source** ✓
2. Frontend fallback (`frontend/src/types/ai.ts`) ← **Secondary source** (outdated)
3. Production backend ← **Deployed version** (not yet deployed)

## Solution: Single Source of Truth Architecture

### Principle

**The backend API is the ONLY authoritative source for model definitions.**

### Data Flow

```
Backend API (analysis.py)
    ↓ HTTP GET /api/analysis/models/available
    ↓
Frontend Hook (useModelAvailability)
    ↓ Transform to AIModel[]
    ↓
UI Components (ModelSelect, ModelSelection)
    ↓ Display to user

IF API FAILS:
    ↓ Fallback to defaultModels (should match backend)
```

## Model Definition Rules

### ✅ DO:

1. **Define models ONCE in backend** (`backend/app/api/analysis.py`)
2. **Update frontend fallback to MATCH backend** (keep in sync)
3. **Use API response as primary data source**
4. **Version model definitions together** (single commit for both)

### ❌ DON'T:

1. **Don't define models independently in frontend**
2. **Don't add models only in frontend fallback**
3. **Don't use different model names/prices in different places**
4. **Don't forget to update fallback when updating backend**

## Current Model Definitions (October 2025)

### Backend Source (`backend/app/api/analysis.py`)

```python
openai_models = {
    "gpt-5": {
        "name": "gpt-5",
        "display_name": "GPT-5",
        "cost_per_1k_tokens": 0.00125,
        "context_window": 400000,
        # ...
    },
    "gpt-5-mini": { ... },
    "gpt-5-nano": { ... },
}

anthropic_models = {
    "claude-sonnet-4.5": { ... },
    "claude-opus-4": { ... },
}
```

### Frontend Fallback (`frontend/src/types/ai.ts`)

```typescript
const defaultModels: AIModel[] = [
  // Ollama models...
  {
    id: "gpt-5-001",
    name: "gpt-5", // MUST match backend
    display_name: "GPT-5", // MUST match backend
    cost_per_1k_tokens: 0.00125, // MUST match backend
    context_window: 400000, // MUST match backend
    // ...
  },
  // ... other GPT-5 and Claude models
];
```

## Synchronization Checklist

When updating models, follow this process:

### Step 1: Update Backend First

```bash
# Edit backend/app/api/analysis.py
# Add/modify model definitions in get_available_models()
```

### Step 2: Update Frontend Fallback

```bash
# Edit frontend/src/types/ai.ts
# Update defaultModels to EXACTLY match backend definitions
```

### Step 3: Verify Match

```bash
# Check that these match:
# - model name
# - display_name
# - cost_per_1k_tokens
# - context_window
# - provider
# - strengths (order doesn't matter)
```

### Step 4: Commit Together

```bash
git add backend/app/api/analysis.py frontend/src/types/ai.ts
git commit -m "feat: Update to GPT-5 models (single source of truth)"
git push
```

### Step 5: Deploy Both

- Railway deploys backend automatically
- Vercel deploys frontend automatically
- **Both must be deployed** for consistency

## Why Fallback Exists

The `defaultModels` array serves as:

1. **Loading state placeholder** - Shown while API loads
2. **Error recovery** - Shown if API fails
3. **Offline development** - Works when backend is down

**Important**: Fallback should ALWAYS match production backend models.

## Testing Single Source of Truth

### Test 1: API Response

```bash
curl https://backend-production-712a.up.railway.app/api/analysis/models/available
# Should show GPT-5 models
```

### Test 2: Frontend Display

1. Open browser DevTools → Network tab
2. Reload page
3. Check API call to `/api/analysis/models/available`
4. Verify response has GPT-5 models
5. Verify UI shows GPT-5 models (not GPT-4)

### Test 3: Fallback Consistency

1. Block API call in DevTools (Network → Offline)
2. Reload page
3. Should show same GPT-5 models (from fallback)
4. No GPT-4 models should appear

## Current Status (October 3, 2025)

### ✅ Fixed

- Backend API updated to GPT-5 models
- Frontend fallback updated to match
- Temperature restrictions documented

### ⏳ Pending Deployment

- Backend needs Railway deployment
- Frontend needs Vercel deployment
- Until deployed, production shows old GPT-4 models

### 🎯 After Deployment

- Production API will return GPT-5 models
- Frontend will display GPT-5 models
- Fallback matches production (single source of truth achieved)

## Future Model Updates

When adding/updating models in the future:

### 1. Update Backend (`analysis.py`)

```python
# Add new model
"gpt-6": {
    "name": "gpt-6",
    "display_name": "GPT-6",
    "cost_per_1k_tokens": 0.001,
    # ...
}
```

### 2. Update Frontend Fallback (`ai.ts`)

```typescript
// Add matching model
{
  id: "gpt-6-001",
  name: "gpt-6",  // EXACT match
  display_name: "GPT-6",  // EXACT match
  cost_per_1k_tokens: 0.001,  // EXACT match
  // ...
}
```

### 3. Consider Future Automation

**Ideal Future State**: Generate frontend fallback from backend OpenAPI schema.

```bash
# Future automation script
npm run generate-models
# Reads backend OpenAPI spec
# Generates frontend/src/types/ai.generated.ts
# Ensures perfect synchronization
```

## File Ownership

| File                                      | Purpose                   | Update Frequency        |
| ----------------------------------------- | ------------------------- | ----------------------- |
| `backend/app/api/analysis.py`             | **PRIMARY SOURCE**        | When models change      |
| `frontend/src/types/ai.ts`                | **FALLBACK (must match)** | When models change      |
| `frontend/src/types/modelAvailability.ts` | Type definitions          | When API schema changes |

## Common Mistakes to Avoid

### ❌ Mistake 1: Only updating backend

```python
# Backend updated to GPT-5 ✓
# Frontend fallback still has GPT-4 ✗
# Result: API fails → Shows old GPT-4 models
```

### ❌ Mistake 2: Different prices

```python
# Backend: cost_per_1k_tokens: 0.00125
# Frontend: cost_per_1k_tokens: 0.00130  # ← WRONG!
# Result: Inconsistent pricing displayed
```

### ❌ Mistake 3: Different names

```python
# Backend: "gpt-5-mini"
# Frontend: "gpt5-mini"  # ← Missing hyphen!
# Result: Frontend can't match backend model
```

### ✅ Correct: Always sync together

```bash
git diff backend/app/api/analysis.py
git diff frontend/src/types/ai.ts
# Both files show GPT-5 updates ✓
```

## Validation Script (Future Enhancement)

```typescript
// scripts/validate-models.ts
import { defaultModels } from "../frontend/src/types/ai";
import backendModels from "../backend/app/api/analysis.py"; // Parse Python

function validateSync() {
  for (const frontendModel of defaultModels) {
    const backendModel = findBackendModel(frontendModel.name);

    assert(frontendModel.name === backendModel.name);
    assert(
      frontendModel.cost_per_1k_tokens === backendModel.cost_per_1k_tokens
    );
    // ... validate all fields
  }
}

// Run in CI/CD before deployment
```

## Summary

**Single Source of Truth** means:

1. ✅ Backend defines all models authoritatively
2. ✅ Frontend fallback exactly mirrors backend
3. ✅ Updates happen together in same commit
4. ✅ API response is always preferred over fallback
5. ✅ Consistency validated before deployment

**Result**: Users always see correct, up-to-date models regardless of API status.
