# GPT-5 Model Update - October 2025

## Overview

Updated Code Evolution Tracker to support OpenAI's new GPT-5 model series, replacing the older GPT-4 models with GPT-5, GPT-5 Mini, and GPT-5 Nano.

## What Changed

### Models Replaced

| Old Model                 | New Model                | Price Change       |
| ------------------------- | ------------------------ | ------------------ |
| GPT-4o ($0.005/1k)        | GPT-5 ($0.00125/1k)      | 75% cheaper        |
| GPT-4o Mini ($0.00015/1k) | GPT-5 Mini ($0.00025/1k) | 67% more expensive |
| GPT-4 Turbo ($0.01/1k)    | GPT-5 Nano ($0.00005/1k) | 99.5% cheaper      |

### New Model Specifications

#### GPT-5 (Flagship)

- **Context Window**: 400,000 tokens (3x larger than GPT-4o)
- **Input Pricing**: $1.25 per 1M tokens ($0.00125 per 1k)
- **Output Pricing**: $10.00 per 1M tokens
- **Strengths**: reasoning, code, analysis, vision, agentic workflows
- **Use Cases**: Complex code analysis, architectural reviews, advanced reasoning

#### GPT-5 Mini (Balanced)

- **Context Window**: 400,000 tokens
- **Input Pricing**: $0.25 per 1M tokens ($0.00025 per 1k)
- **Output Pricing**: $2.00 per 1M tokens
- **Strengths**: code, fast processing, efficiency, cost-effectiveness
- **Use Cases**: General code analysis, pattern detection, quick reviews

#### GPT-5 Nano (Ultra-Fast)

- **Context Window**: 400,000 tokens
- **Input Pricing**: $0.05 per 1M tokens ($0.00005 per 1k)
- **Output Pricing**: $0.40 per 1M tokens
- **Strengths**: fast, lightweight, classification, summarization
- **Use Cases**: Bulk processing, simple classification, code categorization

## Critical: Temperature Parameter Restriction

### The Problem

GPT-5 series models are **reasoning models** and **do not support custom temperature values**. They only support the default temperature of 1.0.

### Error Example

```python
# ❌ THIS WILL FAIL
response = openai.chat.completions.create(
    model="gpt-5",
    temperature=0.7,  # ERROR: Unsupported value
    messages=[...]
)

# Error: "Unsupported value: 'temperature' does not support 0.7 with this model. Only the default (1) value is supported."
```

### Correct Usage

```python
# ✅ CORRECT - Do not include temperature parameter
response = openai.chat.completions.create(
    model="gpt-5",
    messages=[...]  # No temperature parameter
)
```

### Backend Implementation

The backend now includes a `temperature_locked: true` flag for GPT-5 models:

```python
# backend/app/api/analysis.py
"gpt-5": {
    "name": "gpt-5",
    "display_name": "GPT-5",
    "provider": "openai",
    "temperature_locked": True,  # Signals not to use temperature param
    # ... other fields
}
```

### What Needs to Be Updated

If you're implementing actual OpenAI API integration (currently only Ollama is integrated):

1. **Check for `temperature_locked` flag** before making API calls
2. **Omit temperature parameter** entirely for GPT-5 models
3. **Do NOT** pass `temperature=1` - omit it completely

Example implementation:

```python
def call_openai_model(model_name: str, messages: list, model_config: dict):
    params = {
        "model": model_name,
        "messages": messages,
        "max_tokens": 4096,
    }

    # Check if temperature is locked (GPT-5 series)
    if not model_config.get("temperature_locked", False):
        params["temperature"] = 0.7  # Only add for non-GPT-5 models

    return openai.chat.completions.create(**params)
```

## UI Changes

### ModelSelection Component

Updated the "Model Selection Tips" section to reflect new GPT-5 models:

```tsx
// Before
<li>• <strong>GPT-4.1 models</strong> offer 1M token context...</li>
<li>• <strong>O-series models</strong> are optimized for reasoning...</li>
<li>• <strong>GPT-4o Mini</strong> provides excellent cost-efficiency</li>

// After
<li>• <strong>GPT-5</strong> is the flagship model with advanced reasoning and vision</li>
<li>• <strong>GPT-5 Mini</strong> offers excellent balance of speed and capability</li>
<li>• <strong>GPT-5 Nano</strong> provides ultra-fast, cost-effective analysis</li>
```

## TypeScript Type Updates

Added new field to `ModelAvailabilityInfo` interface:

```typescript
export interface ModelAvailabilityInfo {
  // ... existing fields
  temperature_locked?: boolean; // Indicates GPT-5 series
}
```

## Files Modified

1. **backend/app/api/analysis.py** - Updated model definitions with GPT-5 series
2. **frontend/src/components/ai/ModelSelection.tsx** - Updated UI tips
3. **frontend/src/types/modelAvailability.ts** - Added `temperature_locked` field
4. **project-context.md** - Updated model list and added temperature warning
5. **docs/GPT5_MODEL_UPDATE.md** - This file

## Migration Guide

### For Users

- No action required - models will automatically update on next deployment
- GPT-5 offers better performance at lower cost than GPT-4o
- GPT-5 Nano is excellent for high-volume, low-cost analysis

### For Developers

#### If Implementing OpenAI Integration:

1. Check `temperature_locked` flag in model config
2. Omit temperature parameter for GPT-5 models
3. Test with actual OpenAI API to verify no 400 errors

#### Backend Services to Update:

Currently, the system only supports **Ollama** for actual analysis. OpenAI/Anthropic models are listed as "available" but not implemented in the analysis service.

If you're implementing OpenAI integration:

- Update `backend/app/services/ai_service.py`
- Update `backend/app/services/ai_analysis_service.py`
- Add OpenAI client initialization
- Implement model-specific parameter handling

## Cost Impact Analysis

### Example: 1M Token Analysis

| Model    | Old Cost             | New Cost           | Change         |
| -------- | -------------------- | ------------------ | -------------- |
| Flagship | $5.00 (GPT-4o)       | $1.25 (GPT-5)      | **Save $3.75** |
| Balanced | $0.15 (GPT-4o Mini)  | $0.25 (GPT-5 Mini) | Cost +$0.10    |
| Budget   | $10.00 (GPT-4 Turbo) | $0.05 (GPT-5 Nano) | **Save $9.95** |

### Recommendations

- **Use GPT-5** for: Complex analysis, architectural reviews, security audits
- **Use GPT-5 Mini** for: Standard code reviews, pattern detection, general analysis
- **Use GPT-5 Nano** for: Bulk processing, simple classification, quick summaries

## Production Deployment Checklist

- [ ] Deploy updated `backend/app/api/analysis.py` to Railway
- [ ] Deploy updated frontend to Vercel
- [ ] Verify models show in dropdown (should see 3 OpenAI + 2 Anthropic = 5 cloud models)
- [ ] Test with OpenAI API key (if integration exists)
- [ ] Verify no temperature parameter errors
- [ ] Update user documentation with new model names

## Known Limitations

1. **No OpenAI/Anthropic Integration Yet**: Models are listed as available but not implemented in analysis service
2. **Temperature Locked**: GPT-5 models cannot be fine-tuned with temperature
3. **No top_p Support**: GPT-5 models also don't support top_p parameter

## References

- [OpenAI GPT-5 Documentation](https://platform.openai.com/docs/models/gpt-5)
- [OpenAI Pricing Page](https://platform.openai.com/docs/pricing)
- [Simon Willison's GPT-5 Analysis](https://simonwillison.net/2025/Aug/7/gpt-5/)
- [Temperature Parameter Issue](https://community.openai.com/t/temperature-in-gpt-5-models/1337133)

## Status

✅ **Completed** - GPT-5 models added to model list with correct pricing and metadata
⚠️ **Pending** - Actual OpenAI API integration (currently only Ollama works)
📝 **Documented** - Temperature restrictions clearly marked for future implementation
