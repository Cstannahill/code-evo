# app/api/analysis_mongodb.py - MongoDB-based Analysis API
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import asyncio

from app.services.ai_service import AIService
from app.services.pattern_service import PatternService
from app.services.ai_analysis_service import AIAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

# Initialize services
ai_service = AIService()
pattern_service = PatternService()
ai_analysis_service = AIAnalysisService()


@router.get("/status")
async def get_ai_status():
    """Get AI service status with MongoDB integration"""
    logger.info("AI status requested")
    status = ai_service.get_status()

    # Get additional MongoDB service health
    try:
        pattern_health = await pattern_service.get_service_health()
        ai_analysis_health = await ai_analysis_service.get_service_health()
    except Exception as e:
        logger.warning(f"Failed to get MongoDB service health: {e}")
        pattern_health = {"status": "unknown"}
        ai_analysis_health = {"status": "unknown"}

    return {
        "ai_service": status,
        "mongodb_services": {
            "pattern_service": pattern_health,
            "ai_analysis_service": ai_analysis_health,
        },
        "recommendations": {
            "ollama_missing": (
                "Run 'ollama serve' and 'ollama pull codellama:7b'"
                if not status["ollama_available"]
                else None
            ),
            "ready_for_analysis": status["ollama_available"],
        },
    }


@router.post("/code")
async def analyze_code_snippet(request: Dict[str, str]):
    """Analyze a code snippet for patterns with MongoDB backend"""
    try:
        code = request.get("code", "")
        language = request.get("language", "javascript")

        if not code:
            raise HTTPException(status_code=400, detail="Code is required")

        logger.info(f"🤖 Analyzing {len(code)} chars of {language} code")

        # Use AI service for pattern analysis
        pattern_result = await ai_service.analyze_code_pattern(code, language)
        quality_result = await ai_service.analyze_code_quality(code, language)

        # Store AI analysis results in MongoDB
        try:
            analysis_result = await ai_analysis_service.record_analysis_result(
                model_id="codellama:7b",  # TODO: Get from AI service
                code_snippet=code,
                language=language,
                analysis_type="pattern_detection",
                result_data={
                    "pattern_analysis": pattern_result,
                    "quality_analysis": quality_result,
                },
                confidence_score=pattern_result.get("confidence", 0.8),
                metadata={
                    "snippet_length": len(code),
                    "analysis_timestamp": None,  # Will be set automatically
                },
            )
            logger.info(f"✅ Stored analysis result with ID: {analysis_result.id}")
        except Exception as e:
            logger.warning(f"Failed to store analysis result: {e}")

        return {
            "patterns": pattern_result,
            "quality": quality_result,
            "analysis_id": (
                str(analysis_result.id) if "analysis_result" in locals() else None
            ),
            "timestamp": pattern_result.get("timestamp"),
        }

    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/patterns")
async def get_all_patterns():
    """Get all detected patterns across repositories with MongoDB backend"""
    try:
        # Get global pattern statistics
        global_stats = await pattern_service.get_global_pattern_statistics()

        # Convert to list format for API response
        patterns = []
        for pattern_name, stats in global_stats.items():
            patterns.append(
                {
                    "name": pattern_name,
                    "total_occurrences": stats.get("total_occurrences", 0),
                    "repositories_count": stats.get("repositories_count", 0),
                    "average_confidence": stats.get("average_confidence", 0.0),
                    "first_detected": stats.get("first_detected"),
                    "last_detected": stats.get("last_detected"),
                    "category": stats.get("category", "unknown"),
                }
            )

        # Sort by total occurrences
        patterns.sort(key=lambda x: x["total_occurrences"], reverse=True)

        return {
            "patterns": patterns,
            "total_patterns": len(patterns),
            "total_occurrences": sum(p["total_occurrences"] for p in patterns),
            "timestamp": global_stats.get("timestamp"),
        }

    except Exception as e:
        logger.error(f"Failed to get patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to get patterns")


@router.get("/patterns/{pattern_name}")
async def get_pattern_details(pattern_name: str):
    """Get detailed information about a specific pattern with MongoDB backend"""
    try:
        # Get pattern statistics
        global_stats = await pattern_service.get_global_pattern_statistics()
        pattern_stats = global_stats.get(pattern_name)

        if not pattern_stats:
            raise HTTPException(status_code=404, detail="Pattern not found")

        # Get repositories using this pattern
        repos_with_pattern = await pattern_service.get_repositories_using_pattern(
            pattern_name
        )

        return {
            "name": pattern_name,
            "statistics": pattern_stats,
            "repositories": repos_with_pattern,
            "usage_timeline": pattern_stats.get("timeline", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pattern details for {pattern_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pattern details")


@router.get("/insights/{repository_id}")
async def get_repository_insights(repository_id: str):
    """Get AI-generated insights for a repository with MongoDB backend"""
    try:
        # Get repository patterns
        repo_patterns = await pattern_service.get_repository_patterns_statistics(
            repository_id
        )

        if not repo_patterns:
            raise HTTPException(
                status_code=404, detail="Repository not found or no patterns detected"
            )

        # Get AI analysis results for this repository
        ai_results = await ai_analysis_service.get_repository_insights(repository_id)

        # Generate new insights if AI is available
        status = ai_service.get_status()
        new_insights = []

        if status.get("ollama_available", False):
            try:
                insight_data = {
                    "patterns": repo_patterns,
                    "repository_id": repository_id,
                }
                new_insights = await ai_service.generate_insights(insight_data)
            except Exception as e:
                logger.warning(f"Failed to generate new insights: {e}")

        return {
            "repository_id": repository_id,
            "patterns_summary": repo_patterns,
            "ai_insights": ai_results,
            "new_insights": new_insights,
            "ai_powered": status.get("ollama_available", False),
            "timestamp": None,  # Will be set automatically
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get insights for repository {repository_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get repository insights")


@router.get("/ai-models")
async def get_available_ai_models():
    """Get available AI models and their statistics"""
    try:
        models = await ai_analysis_service.get_available_models()

        model_stats = []
        for model in models:
            stats = await ai_analysis_service.get_model_usage_statistics(model.model_id)
            model_stats.append(
                {
                    "model_id": model.model_id,
                    "name": model.name,
                    "provider": model.provider,
                    "version": model.version,
                    "is_available": model.is_available,
                    "capabilities": model.capabilities,
                    "usage_statistics": stats,
                }
            )

        return {
            "models": model_stats,
            "total_models": len(model_stats),
            "available_models": len([m for m in model_stats if m["is_available"]]),
        }

    except Exception as e:
        logger.error(f"Failed to get AI models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI models")


@router.post("/models/{model_id}/benchmark")
async def benchmark_model(model_id: str, test_data: Dict[str, Any]):
    """Benchmark an AI model with test data"""
    try:
        code_snippets = test_data.get("code_snippets", [])
        if not code_snippets:
            raise HTTPException(
                status_code=400, detail="Code snippets are required for benchmarking"
            )

        # Run benchmark
        benchmark_result = await ai_analysis_service.run_model_benchmark(
            model_id=model_id, test_cases=code_snippets
        )

        return {
            "model_id": model_id,
            "benchmark_result": benchmark_result,
            "test_cases_count": len(code_snippets),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to benchmark model {model_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to benchmark model: {str(e)}"
        )
