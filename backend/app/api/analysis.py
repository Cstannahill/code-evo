from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

from app.services.ai_service import AIService
from app.services.pattern_service import PatternService
from app.services.ai_analysis_service import AIAnalysisService
from app.services.repository_service import RepositoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

# Global service instances (lazy initialized)
_ai_service = None
_pattern_service = None
_ai_analysis_service = None
_repository_service = None


def get_services():
    """Get or create service instances (lazy initialization)"""
    global _ai_service, _pattern_service, _ai_analysis_service, _repository_service

    if _ai_service is None:
        _ai_service = AIService()
    if _pattern_service is None:
        _pattern_service = PatternService()
    if _ai_analysis_service is None:
        _ai_analysis_service = AIAnalysisService()
    if _repository_service is None:
        _repository_service = RepositoryService()

    return _ai_service, _pattern_service, _ai_analysis_service, _repository_service


@router.get("/status")
async def get_ai_status():
    """Get AI service status with MongoDB integration"""
    logger.info("AI status requested")
    ai_service, pattern_service, ai_analysis_service, _ = get_services()
    status = ai_service.get_status()

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
    """Analyze a code snippet for patterns and store the result"""
    try:
        code = request.get("code", "")
        language = request.get("language", "javascript")
        if not code:
            raise HTTPException(status_code=400, detail="Code is required")

        logger.info(f"🤖 Analyzing {len(code)} chars of {language} code")
        ai_service, _, ai_analysis_service, _ = get_services()
        pattern_result = await ai_service.analyze_code_pattern(code, language)
        quality_result = await ai_service.analyze_code_quality(code, language)

        analysis_id = None
        try:
            # Create analysis session first
            session = await ai_analysis_service.create_analysis_session(
                repository_id="unknown"
            )
            analysis_result = await ai_analysis_service.record_ai_analysis_result(
                analysis_session_id=str(session.id),
                model_name="codellama:7b",
                code_snippet=code,
                language=language,
                detected_patterns=pattern_result.get("patterns", []),
                complexity_score=quality_result.get("complexity_score"),
                skill_level=quality_result.get("skill_level"),
                suggestions=quality_result.get("suggestions", []),
                confidence_score=pattern_result.get("confidence", 0.8),
                processing_time=pattern_result.get("processing_time"),
                token_usage=pattern_result.get("token_usage"),
                cost_estimate=pattern_result.get("cost_estimate", 0.0),
                error_message=None,
            )
            analysis_id = str(analysis_result.id)
            logger.info(f"✅ Stored analysis result with ID: {analysis_id}")
        except Exception as e:
            logger.warning(f"Failed to store analysis result: {e}")
            analysis_id = None
        return {
            "patterns": pattern_result,
            "quality": quality_result,
            "analysis_id": analysis_id,
            "timestamp": pattern_result.get("timestamp"),
        }
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/patterns")
async def get_all_patterns():
    """Get all detected patterns across repositories"""
    try:
        _, pattern_service, _, _ = get_services()
        global_stats = await pattern_service.get_global_pattern_stats()
        patterns = []
        for pattern_name, stats in global_stats.items():
            if pattern_name == "timestamp":
                continue
            patterns.append(
                {
                    "name": pattern_name,
                    "total_occurrences": stats.get("total_occurrences", 0),
                    "repositories_count": stats.get("repositories_count", 0),
                    "average_confidence": stats.get("avg_confidence", 0.0),
                    "first_detected": stats.get("first_detected"),
                    "last_detected": stats.get("last_detected"),
                    "category": stats.get("category", "unknown"),
                }
            )
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
    """Get detailed information about a specific pattern"""
    try:
        _, pattern_service, _, _ = get_services()
        global_stats = await pattern_service.get_global_pattern_stats()
        pattern_stats = global_stats.get(pattern_name)
        if not pattern_stats:
            raise HTTPException(status_code=404, detail="Pattern not found")

        # The following method does not exist in PatternService, so we return an empty list or placeholder
        repos_with_pattern = (
            []
        )  # await pattern_service.get_repositories_using_pattern(pattern_name)

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
    """Get AI-generated insights for a repository"""
    try:
        ai_service, pattern_service, ai_analysis_service, _ = get_services()
        repo_patterns = await pattern_service.get_repository_patterns(
            repository_id, include_occurrences=False
        )
        if not repo_patterns or repo_patterns.get("error"):
            raise HTTPException(
                status_code=404,
                detail="Repository not found or no patterns detected",
            )

        ai_results = await ai_analysis_service.get_repository_ai_insights(repository_id)
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
            "timestamp": None,
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
        from app.models.repository import get_available_ai_models

        _, _, ai_analysis_service, _ = get_services()
        engine = ai_analysis_service.engine
        models = await get_available_ai_models(engine)
        model_stats = []
        for model in models:
            stats = await ai_analysis_service.get_model_performance_stats(model.name)
            model_stats.append(
                {
                    "model_id": str(model.id),
                    "name": model.name,
                    "provider": model.provider,
                    "version": getattr(model, "version", None),
                    "is_available": model.is_available,
                    "capabilities": getattr(model, "capabilities", []),
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
        _, _, ai_analysis_service, _ = get_services()
        code_snippets = test_data.get("code_snippets", [])
        benchmark_name = test_data.get("benchmark_name", "default")
        if not code_snippets:
            raise HTTPException(
                status_code=400,
                detail="Code snippets are required for benchmarking",
            )
        # Prepare test_results as a dict for benchmark_model
        test_results = {
            "dataset_size": len(code_snippets),
            "version": test_data.get("version", "1.0"),
            "accuracy": test_data.get("accuracy"),
            "precision": test_data.get("precision"),
            "recall": test_data.get("recall"),
            "f1_score": test_data.get("f1_score"),
            "avg_processing_time": test_data.get("avg_processing_time"),
            "avg_cost": test_data.get("avg_cost"),
            "pattern_detection_rate": test_data.get("pattern_detection_rate"),
            "false_positive_rate": test_data.get("false_positive_rate"),
            "false_negative_rate": test_data.get("false_negative_rate"),
            "notes": test_data.get("notes"),
            "code_snippets": code_snippets,
        }
        benchmark_result = await ai_analysis_service.benchmark_model(
            model_name=model_id,
            benchmark_name=benchmark_name,
            test_results=test_results,
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


@router.post("/evolution")
async def analyze_code_evolution(request: Dict[str, Any]):
    """Analyze evolution between two code versions"""
    try:
        ai_service, _, _, _ = get_services()
        old_code = request.get("old_code", "")
        new_code = request.get("new_code", "")
        context = request.get("context", "")
        if not old_code or not new_code:
            raise HTTPException(
                status_code=400, detail="Both old_code and new_code are required"
            )
        evolution_result = await ai_service.analyze_evolution(
            old_code, new_code, context
        )
        return {
            "evolution_analysis": evolution_result,
            "ai_powered": ai_service.ollama_available,
            "timestamp": "2024-01-01T00:00:00Z",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing code evolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{repo_id1}/{repo_id2}")
async def compare_repositories(repo_id1: str, repo_id2: str):
    """Compare two repositories"""
    try:
        ai_service, pattern_service, _, repository_service = get_services()
        repo1 = await repository_service.get_repository(repo_id1)
        repo2 = await repository_service.get_repository(repo_id2)
        if not repo1 or not repo2:
            raise HTTPException(
                status_code=404, detail="One or both repositories not found"
            )

        patterns1_data = await pattern_service.get_repository_patterns(
            repo_id1, include_occurrences=False
        )
        patterns2_data = await pattern_service.get_repository_patterns(
            repo_id2, include_occurrences=False
        )
        patterns1 = set(
            p["pattern"]["name"] for p in patterns1_data.get("patterns", [])
        )
        patterns2 = set(
            p["pattern"]["name"] for p in patterns2_data.get("patterns", [])
        )

        tech1 = (
            set(t.get("name") for t in repo1.tech_stack)
            if hasattr(repo1, "tech_stack")
            else set()
        )
        tech2 = (
            set(t.get("name") for t in repo2.tech_stack)
            if hasattr(repo2, "tech_stack")
            else set()
        )

        similarity_score = _calculate_similarity_score(
            patterns1, patterns2, tech1, tech2
        )

        comparison = {
            "repository_1": {
                "id": repo_id1,
                "name": repo1.name,
                "total_commits": repo1.total_commits,
                "patterns": list(patterns1),
                "technologies": list(tech1),
            },
            "repository_2": {
                "id": repo_id2,
                "name": repo2.name,
                "total_commits": repo2.total_commits,
                "patterns": list(patterns2),
                "technologies": list(tech2),
            },
            "comparison": {
                "common_patterns": list(patterns1.intersection(patterns2)),
                "unique_to_repo1": list(patterns1.difference(patterns2)),
                "unique_to_repo2": list(patterns2.difference(patterns1)),
                "common_technologies": list(tech1.intersection(tech2)),
                "unique_tech_repo1": list(tech1.difference(tech2)),
                "unique_tech_repo2": list(tech2.difference(tech1)),
                "similarity_score": similarity_score,
            },
            "ai_powered": ai_service.ollama_available,
        }
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_complexity_distribution(patterns: List[Dict[str, Any]]) -> Dict[str, int]:
    distribution = {"simple": 0, "intermediate": 0, "advanced": 0}
    for p in patterns:
        level = (
            p.get("complexity_level")
            or p.get("pattern", {}).get("complexity_level")
            or "intermediate"
        )
        if level in distribution:
            distribution[level] += 1
    return distribution


def _calculate_similarity_score(
    patterns1: set, patterns2: set, tech1: set, tech2: set
) -> float:
    if not patterns1 and not patterns2 and not tech1 and not tech2:
        return 1.0
    pattern_union = patterns1.union(patterns2)
    pattern_intersection = patterns1.intersection(patterns2)
    pattern_similarity = (
        len(pattern_intersection) / len(pattern_union) if pattern_union else 0
    )
    tech_union = tech1.union(tech2)
    tech_intersection = tech1.intersection(tech2)
    tech_similarity = len(tech_intersection) / len(tech_union) if tech_union else 0
    return (pattern_similarity * 0.7) + (tech_similarity * 0.3)
