# app/api/multi_model_test.py - TEST & DEMO ENDPOINTS
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging
import asyncio

from app.core.database import get_db
from app.services.multi_model_ai_service import MultiModelAIService, AIModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/multi-model-test", tags=["Multi-Model Testing"])

# Initialize service
multi_ai_service = MultiModelAIService()


class QuickTestRequest(BaseModel):
    code: str = """
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const userData = await response.json();
        return userData;
    } catch (error) {
        console.error('Failed to fetch user:', error);
        throw error;
    }
}
"""
    language: str = "javascript"
    models: List[str] = ["codellama:7b"]


@router.get("/status")
async def get_multi_model_status():
    """Get status of all available AI models"""
    try:
        available_models = multi_ai_service.get_available_models()

        status = {
            "service_initialized": True,
            "total_models_configured": len(multi_ai_service.available_models),
            "available_models": len(available_models),
            "models": {},
            "recommendations": {
                "ready_for_testing": len(available_models) > 0,
                "suggested_test_models": [],
            },
        }

        # Test each model's actual availability
        for model_key, model_info in available_models.items():
            status["models"][model_key] = {
                "info": model_info,
                "status": "available" if model_info["available"] else "unavailable",
                "can_test": model_info["available"],
            }

            if model_info["available"]:
                status["recommendations"]["suggested_test_models"].append(model_key)

        return status

    except Exception as e:
        logger.error(f"Error getting multi-model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-test")
async def quick_multi_model_test(request: QuickTestRequest):
    """Quick test of multi-model analysis"""
    try:
        logger.info(f"🧪 Running quick test with {len(request.models)} models")

        # Convert model names to enums
        models_to_test = []
        for model_name in request.models:
            try:
                model_enum = AIModel(model_name)
                if model_enum in multi_ai_service.available_models:
                    models_to_test.append(model_enum)
                else:
                    logger.warning(f"Model {model_name} not available")
            except ValueError:
                logger.warning(f"Unknown model: {model_name}")

        if not models_to_test:
            return {
                "error": "No valid models available for testing",
                "available_models": list(
                    multi_ai_service.get_available_models().keys()
                ),
                "requested_models": request.models,
            }

        # Run analysis with selected models
        if len(models_to_test) == 1:
            # Single model analysis
            result = await multi_ai_service.analyze_with_model(
                request.code, request.language, models_to_test[0]
            )

            return {
                "test_type": "single_model",
                "model_tested": result.model.value,
                "result": {
                    "patterns": result.patterns,
                    "complexity_score": result.complexity_score,
                    "skill_level": result.skill_level,
                    "suggestions": result.suggestions[:3],  # Limit for readability
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "error": result.error,
                },
                "success": result.error is None,
            }
        else:
            # Multi-model comparison
            results = await multi_ai_service.compare_models(
                request.code, request.language, models_to_test
            )

            # Calculate basic comparison metrics
            all_patterns = set()
            model_patterns = {}

            for result in results:
                model_patterns[result.model.value] = set(result.patterns)
                all_patterns.update(result.patterns)

            consensus_patterns = (
                set.intersection(*model_patterns.values()) if model_patterns else set()
            )

            return {
                "test_type": "multi_model_comparison",
                "models_tested": [r.model.value for r in results],
                "individual_results": [
                    {
                        "model": r.model.value,
                        "patterns": r.patterns,
                        "complexity_score": r.complexity_score,
                        "confidence": r.confidence,
                        "processing_time": r.processing_time,
                        "error": r.error,
                        "success": r.error is None,
                    }
                    for r in results
                ],
                "comparison": {
                    "total_unique_patterns": len(all_patterns),
                    "consensus_patterns": list(consensus_patterns),
                    "agreement_score": (
                        len(consensus_patterns) / len(all_patterns)
                        if all_patterns
                        else 0
                    ),
                    "fastest_model": (
                        min(results, key=lambda x: x.processing_time).model.value
                        if results
                        else None
                    ),
                    "most_confident": (
                        max(results, key=lambda x: x.confidence).model.value
                        if results
                        else None
                    ),
                },
                "success": all(r.error is None for r in results),
            }

    except Exception as e:
        logger.error(f"Quick test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmark")
async def run_benchmark_test():
    """Run a comprehensive benchmark of all available models"""
    try:
        logger.info("🏁 Starting comprehensive model benchmark")

        # Get all available models
        available_models = [
            model
            for model in multi_ai_service.available_models.keys()
            if multi_ai_service.available_models[model].available
        ]

        if not available_models:
            return {
                "error": "No models available for benchmarking",
                "available_models": list(
                    multi_ai_service.get_available_models().keys()
                ),
            }

        # Test code samples for different complexity levels
        test_cases = [
            {
                "name": "Simple Function",
                "code": """
function greet(name) {
    return `Hello, ${name}!`;
}
""",
                "language": "javascript",
                "expected_complexity": "beginner",
            },
            {
                "name": "Async API Call",
                "code": """
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const userData = await response.json();
        return userData;
    } catch (error) {
        console.error('Failed to fetch user:', error);
        throw error;
    }
}
""",
                "language": "javascript",
                "expected_complexity": "intermediate",
            },
            {
                "name": "React Hook with Complex Logic",
                "code": """
import { useState, useEffect, useCallback } from 'react';

function useDataFetcher(url, options = {}) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [url, options]);
    
    useEffect(() => {
        fetchData();
    }, [fetchData]);
    
    return { data, loading, error, refetch: fetchData };
}
""",
                "language": "javascript",
                "expected_complexity": "advanced",
            },
        ]

        benchmark_results = {
            "benchmark_date": "2024-01-15T12:00:00Z",
            "models_tested": [m.value for m in available_models],
            "test_cases": len(test_cases),
            "results": {},
            "summary": {},
        }

        # Test each model on each test case
        for model in available_models:
            logger.info(f"🧪 Benchmarking {model.value}")
            model_results = []

            for test_case in test_cases:
                try:
                    result = await multi_ai_service.analyze_with_model(
                        test_case["code"], test_case["language"], model
                    )

                    model_results.append(
                        {
                            "test_case": test_case["name"],
                            "expected_complexity": test_case["expected_complexity"],
                            "actual_complexity": result.skill_level,
                            "complexity_score": result.complexity_score,
                            "patterns_detected": len(result.patterns),
                            "confidence": result.confidence,
                            "processing_time": result.processing_time,
                            "success": result.error is None,
                            "error": result.error,
                        }
                    )

                except Exception as e:
                    model_results.append(
                        {
                            "test_case": test_case["name"],
                            "success": False,
                            "error": str(e),
                        }
                    )

            benchmark_results["results"][model.value] = model_results

        # Calculate summary statistics
        for model_name, results in benchmark_results["results"].items():
            successful_tests = [r for r in results if r.get("success", False)]

            if successful_tests:
                benchmark_results["summary"][model_name] = {
                    "success_rate": len(successful_tests) / len(results),
                    "avg_processing_time": sum(
                        r["processing_time"] for r in successful_tests
                    )
                    / len(successful_tests),
                    "avg_confidence": sum(r["confidence"] for r in successful_tests)
                    / len(successful_tests),
                    "avg_patterns_detected": sum(
                        r["patterns_detected"] for r in successful_tests
                    )
                    / len(successful_tests),
                    "complexity_accuracy": sum(
                        1
                        for r in successful_tests
                        if r["expected_complexity"] == r["actual_complexity"]
                    )
                    / len(successful_tests),
                }
            else:
                benchmark_results["summary"][model_name] = {
                    "success_rate": 0.0,
                    "error": "All tests failed",
                }

        logger.info("✅ Benchmark completed")
        return benchmark_results

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo-data")
async def get_demo_comparison_data():
    """Get demo data for frontend testing"""
    return {
        "available_models": {
            "codellama:7b": {
                "name": "CodeLlama 7B",
                "provider": "Ollama (Local)",
                "cost_per_1k_tokens": 0.0,
                "strengths": [
                    "Fast inference",
                    "Good for basic patterns",
                    "Privacy-focused",
                ],
                "available": True,
            },
            "gpt-4": {
                "name": "GPT-4",
                "provider": "OpenAI",
                "cost_per_1k_tokens": 0.03,
                "strengths": [
                    "Exceptional reasoning",
                    "Detailed explanations",
                    "Latest patterns",
                ],
                "available": False,
            },
            "claude-3-sonnet": {
                "name": "Claude 3 Sonnet",
                "provider": "Anthropic",
                "cost_per_1k_tokens": 0.015,
                "strengths": [
                    "Code quality focus",
                    "Security analysis",
                    "Best practices",
                ],
                "available": False,
            },
        },
        "sample_comparison": {
            "comparison_id": "demo-123",
            "models_compared": ["codellama:7b", "gpt-4", "claude-3-sonnet"],
            "individual_results": [
                {
                    "model": "codellama:7b",
                    "patterns": ["async_await", "error_handling", "api_integration"],
                    "complexity_score": 7.2,
                    "skill_level": "intermediate",
                    "confidence": 0.85,
                    "processing_time": 1.2,
                    "suggestions": [
                        "Consider adding input validation",
                        "Error handling could be more robust",
                    ],
                },
                {
                    "model": "gpt-4",
                    "patterns": [
                        "async_await",
                        "error_handling",
                        "api_integration",
                        "security_concerns",
                    ],
                    "complexity_score": 8.1,
                    "skill_level": "advanced",
                    "confidence": 0.92,
                    "processing_time": 2.8,
                    "suggestions": [
                        "Implement comprehensive input sanitization",
                        "Consider adding rate limiting",
                    ],
                },
                {
                    "model": "claude-3-sonnet",
                    "patterns": [
                        "async_await",
                        "error_handling",
                        "api_integration",
                        "code_organization",
                    ],
                    "complexity_score": 7.8,
                    "skill_level": "intermediate",
                    "confidence": 0.89,
                    "processing_time": 2.1,
                    "suggestions": [
                        "Add comprehensive JSDoc comments",
                        "Consider extracting API logic",
                    ],
                },
            ],
            "comparison_analysis": {
                "consensus_patterns": [
                    "async_await",
                    "error_handling",
                    "api_integration",
                ],
                "disputed_patterns": [
                    {
                        "pattern": "security_concerns",
                        "detected_by": ["gpt-4"],
                        "agreement_ratio": 0.33,
                    }
                ],
                "agreement_score": 0.75,
                "performance": {
                    "fastest_model": "codellama:7b",
                    "most_confident": "gpt-4",
                },
            },
        },
    }
