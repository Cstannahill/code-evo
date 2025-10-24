from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List, Optional, Tuple
import logging

from app.core.service_manager import (
    get_ai_service,
    get_pattern_service,
    get_ai_analysis_service,
    get_repository_service,
)
from app.api.auth import get_current_user_optional, user_has_provider_key
from app.models.repository import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


def get_services() -> Tuple[Any, Any, Any, Any]:
    """Get service instances using centralized service manager"""
    try:
        ai_service = get_ai_service()
    except Exception as e:
        logger.warning(f"AI service initialization failed: {e}")
        ai_service = None

    try:
        pattern_service = get_pattern_service()
    except Exception as e:
        logger.warning(f"Pattern service initialization failed: {e}")
        pattern_service = None

    try:
        ai_analysis_service = get_ai_analysis_service()
    except Exception as e:
        logger.warning(f"AI analysis service initialization failed: {e}")
        ai_analysis_service = None

    try:
        repository_service = get_repository_service()
    except Exception as e:
        logger.warning(f"Repository service initialization failed: {e}")
        repository_service = None

    return (
        ai_service,
        pattern_service,
        ai_analysis_service,
        repository_service,
    )


@router.get("/status")
async def get_ai_status():
    """Get AI service status with MongoDB integration"""
    logger.info("AI status requested")

    try:
        ai_service, pattern_service, ai_analysis_service, _ = get_services()

        # Get AI service status, with fallback if service is None
        if ai_service is not None:
            status = ai_service.get_status()
        else:
            status = {
                "ollama_available": False,
                "ollama_model": None,
                "embeddings_available": False,
                "embeddings_model": None,
                "vector_db_available": False,
                "preferred_model": None,
                "multi_model_service_available": False,
                "timestamp": "2025-09-12T23:37:23.516925",
                "available_models_count": 0,
                "openai_models_available": False,
            }
    except Exception as e:
        logger.error(f"Failed to get AI service: {e}")
        status = {
            "ollama_available": False,
            "ollama_model": None,
            "embeddings_available": False,
            "embeddings_model": None,
            "vector_db_available": False,
            "preferred_model": None,
            "multi_model_service_available": False,
            "timestamp": "2025-09-12T23:37:23.516925",
            "available_models_count": 0,
            "openai_models_available": False,
        }
        # Initialize services to None if they failed to initialize
        pattern_service = None
        ai_analysis_service = None

    # Return the status wrapped in the expected structure for frontend
    return {
        "ai_service": status,
        "pattern_service": {
            "available": pattern_service is not None,
            "patterns_count": (
                0
                if pattern_service is None
                else (
                    len(await pattern_service.get_all_patterns())
                    if hasattr(pattern_service, "get_all_patterns")
                    else 0
                )
            ),
        },
        "analysis_service": {"available": ai_analysis_service is not None},
    }


@router.get("/models/available")
async def get_available_models(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get ALL AI models for frontend dropdown.
    Returns all models with 'available' flag indicating if they can be used.
    Models without API keys are shown but marked as unavailable.
    """
    logger.info("Available models requested")

    try:
        ai_service, _, _, _ = get_services()
        if ai_service is None:
            logger.error("AI service is unavailable while fetching model list")
            raise HTTPException(status_code=503, detail="AI service unavailable")

        status = ai_service.get_status()

        # If Ollama isn't available locally, try to detect a per-user tunnel
        # and use it to fetch available models. This ensures that when a user
        # registers an external tunnel (Cloudflare/ngrok) the frontend will
        # see ollama models as available for that user.
        tunnel_models: list = []
        try:
            # Only attempt if the ai service reports Ollama as unavailable
            # and we have an authenticated user
            if not status.get("ollama_available", False) and current_user is not None:
                from app.services.secure_tunnel_service import get_tunnel_service

                tunnel_service = get_tunnel_service()
                tunnel_status = tunnel_service.get_tunnel_status(str(current_user.id))
                if tunnel_status and tunnel_status.get("connected"):
                    tunnel_url = tunnel_status.get("tunnel_url")
                    if tunnel_url:
                        import requests

                        try:
                            resp = requests.get(
                                f"{tunnel_url.rstrip('/')}/api/tags", timeout=5
                            )
                            if resp.status_code == 200:
                                payload = resp.json()
                                tunnel_models = payload.get("models") or []
                                # Convert tunnel 'size' (bytes) to size_gb for frontend display
                                for m in tunnel_models:
                                    try:
                                        byte_size = m.get("size")
                                        if (
                                            isinstance(byte_size, (int, float))
                                            and byte_size > 0
                                        ):
                                            m["size_gb"] = round(
                                                byte_size / (1024 * 1024 * 1024), 1
                                            )
                                    except Exception:
                                        # ignore malformed size values
                                        pass

                                # Treat per-user tunnel as Ollama available for this request
                                status["ollama_available"] = True
                                logger.info(
                                    f"Detected Ollama models via tunnel for user {current_user.id}: {len(tunnel_models or [])} models"
                                )
                        except Exception as e:
                            logger.debug(f"Could not fetch models via user tunnel: {e}")
        except Exception as e:
            logger.debug(f"Tunnel model detection skipped or failed: {e}")

        # Check if OpenAI key is available (global or user-specific)
        openai_models_available = status.get("openai_models_available", False)
        if not openai_models_available and current_user is not None:
            user_has_openai_key = await user_has_provider_key(current_user, "openai")
            openai_models_available = openai_models_available or user_has_openai_key

        # Check if Anthropic key is available (global or user-specific)
        anthropic_models_available = status.get("anthropic_available", False)
        if not anthropic_models_available and current_user is not None:
            user_has_anthropic_key = await user_has_provider_key(
                current_user, "anthropic"
            )
            anthropic_models_available = (
                anthropic_models_available or user_has_anthropic_key
            )

        # Get Ollama model sizes from backend service
        from app.services.ollama_size_service import get_ollama_size_service

        ollama_sizes = await get_ollama_size_service().get_model_sizes()

        # Build available models response
        available_models = {}

        # Add Ollama models (if running locally OR available via per-user tunnel)
        if status.get("ollama_available", False):
            try:
                import requests

                # Prefer tunnel-provided models when available for this user
                if tunnel_models is not None:
                    models = tunnel_models
                else:
                    # Fallback to local Ollama on localhost
                    response = requests.get(
                        "http://localhost:11434/api/tags", timeout=5
                    )
                    models = []
                    if response.status_code == 200:
                        models_data = response.json()
                        models = models_data.get("models", [])

                for model in models:
                    model_name = model.get("name", "")
                    # Prefer size supplied by the tunnel payload (size_gb) then fall back to backend ollama_sizes
                    size_gb = None
                    try:
                        size_gb = model.get("size_gb")
                    except Exception:
                        size_gb = None
                    if size_gb is None:
                        size_info = ollama_sizes.get(model_name, {})
                        size_gb = size_info.get("size_gb")

                    available_models[model_name] = {
                        "name": model_name,
                        "display_name": model_name,
                        "provider": "ollama",
                        "available": True,
                        "context_window": 4096,  # Default
                        "cost_per_1k_tokens": 0,
                        "strengths": ["code", "general"],
                        "size_gb": size_gb,  # Add backend-provided size
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch Ollama models: {e}")

        # ALWAYS add OpenAI models (show even without API key)
        # GPT-5 series models: DO NOT include temperature parameter (must use default of 1)
        openai_models = {
            "gpt-5": {
                "name": "gpt-5",
                "display_name": "GPT-5",
                "provider": "openai",
                "available": openai_models_available,
                "context_window": 400000,
                "cost_per_1k_tokens": 0.00125,  # $1.25 per 1M tokens input, $10 per 1M output (using input price)
                "strengths": ["reasoning", "code", "analysis", "vision", "agentic"],
                "requires_api_key": not openai_models_available,
                "temperature_locked": True,  # GPT-5 models require temperature=1 (default)
            },
            "gpt-5-mini": {
                "name": "gpt-5-mini",
                "display_name": "GPT-5 Mini",
                "provider": "openai",
                "available": openai_models_available,
                "context_window": 400000,
                "cost_per_1k_tokens": 0.00025,  # $0.25 per 1M tokens input, $2 per 1M output
                "strengths": ["code", "fast", "efficient", "cost-effective"],
                "requires_api_key": not openai_models_available,
                "temperature_locked": True,  # GPT-5 models require temperature=1 (default)
            },
            "gpt-5-nano": {
                "name": "gpt-5-nano",
                "display_name": "GPT-5 Nano",
                "provider": "openai",
                "available": openai_models_available,
                "context_window": 400000,
                "cost_per_1k_tokens": 0.00005,  # $0.05 per 1M tokens input, $0.40 per 1M output
                "strengths": ["fast", "lightweight", "classification", "summarization"],
                "requires_api_key": not openai_models_available,
                "temperature_locked": True,  # GPT-5 models require temperature=1 (default)
            },
        }
        available_models.update(openai_models)

        # ALWAYS add Anthropic models (show even without API key)
        # Updated to use Claude Sonnet 4.5 (latest, same cost as 3.5)
        anthropic_models = {
            "claude-sonnet-4.5": {
                "name": "claude-sonnet-4.5",
                "display_name": "Claude Sonnet 4.5",
                "provider": "anthropic",
                "available": anthropic_models_available,
                "context_window": 200000,
                "cost_per_1k_tokens": 0.003,
                "strengths": ["reasoning", "code", "analysis", "long-context"],
                "requires_api_key": not anthropic_models_available,
            },
            "claude-opus-4": {
                "name": "claude-opus-4",
                "display_name": "Claude Opus 4",
                "provider": "anthropic",
                "available": anthropic_models_available,
                "context_window": 200000,
                "cost_per_1k_tokens": 0.015,
                "strengths": [
                    "advanced-reasoning",
                    "complex-tasks",
                    "code",
                    "research",
                ],
                "requires_api_key": not anthropic_models_available,
            },
        }
        available_models.update(anthropic_models)

        return {
            "available_models": available_models,
            "total_count": len(available_models),
            "ollama_available": status.get("ollama_available", False),
            "openai_available": openai_models_available,
            "anthropic_available": anthropic_models_available,
            "timestamp": status.get("timestamp", ""),
        }

    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        return {
            "available_models": {},
            "total_count": 0,
            "ollama_available": False,
            "openai_available": False,
            "timestamp": "",
            "error": str(e),
        }

    try:
        if pattern_service and ai_analysis_service:
            pattern_health = await pattern_service.get_service_health()
            ai_analysis_health = await ai_analysis_service.get_service_health()
        else:
            pattern_health = {
                "status": "unavailable",
                "error": "Services not initialized",
            }
            ai_analysis_health = {
                "status": "unavailable",
                "error": "Services not initialized",
            }
    except Exception as e:
        logger.warning(f"Failed to get MongoDB service health: {e}")
        pattern_health = {"status": "unavailable", "error": str(e)}
        ai_analysis_health = {"status": "unavailable", "error": str(e)}

    return {
        "ai_service": status,
        "mongodb_services": {
            "pattern_service": pattern_health,
            "ai_analysis_service": ai_analysis_health,
        },
        "recommendations": {
            "ollama_missing": (
                "Run 'ollama serve' and 'ollama pull codellama:7b'"
                if not status.get("ollama_available", False)
                else None
            ),
            "ready_for_analysis": status.get("ollama_available", False),
        },
    }


@router.post("/code")
async def analyze_code_snippet(
    request: Dict[str, str],
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Analyze a code snippet for patterns and store the result"""
    try:
        code = request.get("code", "")
        language = request.get("language", "javascript")
        if not code:
            raise HTTPException(status_code=400, detail="Code is required")

        logger.info(f"🤖 Analyzing {len(code)} chars of {language} code")
        ai_service, _, ai_analysis_service, _ = get_services()
        user_id = str(current_user.id) if current_user else None
        pattern_result = await ai_service.analyze_code_pattern(
            code, language, user_id=user_id
        )
        quality_result = await ai_service.analyze_code_quality(
            code, language, user_id=user_id
        )

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
async def analyze_code_evolution(
    request: Dict[str, Any],
    current_user: Optional[User] = Depends(get_current_user_optional),
):
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
        user_id = str(current_user.id) if current_user else None
        evolution_result = await ai_service.analyze_evolution(
            old_code, new_code, context, user_id=user_id
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
