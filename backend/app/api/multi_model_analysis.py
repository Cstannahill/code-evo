# app/api/multi_model_analysis.py - FIXED VERSION
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import uuid
import asyncio

from app.core.database import get_db
from app.services.multi_model_ai_service import (
    MultiModelAIService,
    AIModel,
    AnalysisResult,
)
from app.models.repository import (
    RepositorySQL as Repository,
    AIModelSQL as AIModelDB,
    AIAnalysisResultSQL as AIAnalysisResult,
    ModelComparisonSQL as ModelComparison,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/multi-model", tags=["Multi-Model Analysis"])

# Multi-model service will be initialized lazily
multi_ai_service = None

def get_multi_ai_service():
    """Get or create multi-model AI service instance"""
    global multi_ai_service
    if multi_ai_service is None:
        multi_ai_service = MultiModelAIService()
    return multi_ai_service


def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())


# Pydantic models for requests/responses
class ModelSelectionRequest(BaseModel):
    models: List[str]  # List of model names
    code: str
    language: str = "javascript"


class ComparisonAnalysisRequest(BaseModel):
    repository_id: str
    models: List[str]
    branch: str = "main"
    commit_limit: int = 50


class ModelComparisonResponse(BaseModel):
    comparison_id: str
    models_compared: List[str]
    results: List[Dict]
    consensus_patterns: List[str]
    disputed_patterns: List[Dict]
    agreement_score: float
    performance_metrics: Dict
    recommendations: Dict


@router.get("/models/available")
async def get_available_models():
    """Get all available AI models with their capabilities"""
    try:
        models = get_multi_ai_service().get_available_models()

        return {
            "available_models": models,
            "total_count": len(models),
            "categories": {
                "local": [m for m in models.values() if m["cost_per_1k_tokens"] == 0.0],
                "api": [m for m in models.values() if m["cost_per_1k_tokens"] > 0.0],
            },
            "recommendations": {
                "fastest": "codellama:7b",
                "most_capable": "gpt-4" if "gpt-4" in models else "codellama:13b",
                "best_value": (
                    "gpt-3.5-turbo" if "gpt-3.5-turbo" in models else "codellama:7b"
                ),
            },
        }
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/single")
async def analyze_with_single_model(
    request: ModelSelectionRequest, db: Session = Depends(get_db)
):
    """Analyze code with a single selected model"""
    try:
        if not request.models or len(request.models) != 1:
            raise HTTPException(
                status_code=400, detail="Exactly one model must be specified"
            )

        model_name = request.models[0]

        # Convert string to AIModel enum
        try:
            model = AIModel(model_name)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Unsupported model: {model_name}"
            )

        # Perform analysis
        result = await get_multi_ai_service().analyze_with_model(
            request.code, request.language, model
        )

        model_info = get_multi_ai_service().available_models.get(model)

        return {
            "model": model.value,
            "model_info": {
                "name": model_info.name if model_info else model_name,
                "provider": model_info.provider if model_info else "Unknown",
                "strengths": model_info.strengths if model_info else [],
            },
            "analysis": {
                "patterns": result.patterns,
                "complexity_score": result.complexity_score,
                "skill_level": result.skill_level,
                "suggestions": result.suggestions,
                "confidence": result.confidence,
                "processing_time": result.processing_time,
                "token_usage": result.token_usage,
                "error": result.error,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Single model analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/compare")
async def compare_multiple_models(
    request: ModelSelectionRequest, db: Session = Depends(get_db)
):
    """Compare code analysis across multiple AI models"""
    try:
        if len(request.models) < 2:
            raise HTTPException(
                status_code=400, detail="At least 2 models required for comparison"
            )

        # Convert model names to enum
        models = []
        for model_name in request.models:
            try:
                models.append(AIModel(model_name))
            except ValueError:
                logger.warning(f"Skipping unsupported model: {model_name}")

        if len(models) < 2:
            raise HTTPException(
                status_code=400, detail="At least 2 valid models required"
            )

        # Perform parallel analysis with all models
        results = await get_multi_ai_service().compare_models(
            request.code, request.language, models
        )

        # Calculate comparison metrics
        comparison_metrics = _calculate_comparison_metrics(results)

        return {
            "comparison_id": generate_uuid(),
            "models_compared": [r.model.value for r in results],
            "individual_results": [
                {
                    "model": result.model.value,
                    "model_info": {
                        "name": get_multi_ai_service().available_models[result.model].name,
                        "provider": get_multi_ai_service().available_models[
                            result.model
                        ].provider,
                        "strengths": get_multi_ai_service().available_models[
                            result.model
                        ].strengths,
                    },
                    "patterns": result.patterns,
                    "complexity_score": result.complexity_score,
                    "skill_level": result.skill_level,
                    "suggestions": result.suggestions,
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "token_usage": result.token_usage,
                    "error": result.error,
                }
                for result in results
            ],
            "comparison_analysis": comparison_metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Model comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/repository")
async def analyze_repository_with_multiple_models(
    repository_id: str,
    selected_models: List[str] = Query(..., min_items=1, max_items=4),
    analysis_type: str = "comparison",
    db: Session = Depends(get_db),
):
    """Compare multiple AI models on the same repository"""
    try:
        # Validate repository exists
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

        # Convert model names to enums
        models = []
        for model_name in selected_models:
            try:
                models.append(AIModel(model_name))
            except ValueError:
                logger.warning(f"Skipping unsupported model: {model_name}")

        if not models:
            raise HTTPException(status_code=400, detail="No valid models specified")

        # Run parallel analysis with multiple models
        results = await get_multi_ai_service().analyze_repository_parallel(
            repository_id, models
        )

        # Store comparison in database
        comparison = ModelComparison(
            id=generate_uuid(),
            repository_id=repository_id,
            models_compared=[m.value for m in models],
            consensus_patterns=results["consensus_patterns"],
            disputed_patterns=results["disputed_patterns"],
            agreement_score=results["agreement_score"],
        )
        db.add(comparison)
        db.commit()

        return {
            "comparison_id": comparison.id,
            "repository_id": repository_id,
            "models_compared": [m.value for m in models],
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Multi-model repository analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparison/{comparison_id}")
async def get_comparison_results(comparison_id: str, db: Session = Depends(get_db)):
    """Get results of a multi-model comparison"""
    try:
        comparison = (
            db.query(ModelComparison)
            .filter(ModelComparison.id == comparison_id)
            .first()
        )

        if not comparison:
            raise HTTPException(status_code=404, detail="Comparison not found")

        return {
            "comparison_id": comparison_id,
            "repository_id": comparison.repository_id,
            "models_compared": comparison.models_compared,
            "consensus_patterns": comparison.consensus_patterns,
            "disputed_patterns": comparison.disputed_patterns,
            "agreement_score": comparison.agreement_score,
            "created_at": comparison.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting comparison results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_name}/stats")
async def get_model_statistics(model_name: str, db: Session = Depends(get_db)):
    """Get usage statistics and performance metrics for a specific model"""
    try:
        # For now, return mock statistics since we need to build up usage data
        return {
            "model": model_name,
            "model_info": {
                "display_name": model_name.replace(":", " ").title(),
                "provider": "Ollama" if ":" in model_name else "API",
                "strengths": ["Code Analysis", "Pattern Detection"],
            },
            "usage_stats": {
                "total_analyses": 0,
                "avg_processing_time": 0,
                "avg_confidence": 0,
                "total_cost": 0,
                "success_rate": 1.0,
            },
            "pattern_stats": {
                "most_detected_patterns": [],
                "unique_patterns_detected": 0,
            },
        }

    except Exception as e:
        logger.error(f"Error getting model statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_name}/estimate-cost")
async def estimate_analysis_cost(model_name: str, request: Dict[str, str]):
    """Estimate the cost of analyzing code with a specific model"""
    try:
        # Convert string to AIModel enum
        try:
            model = AIModel(model_name)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Unsupported model: {model_name}"
            )

        code = request.get("code", "")
        if not code:
            raise HTTPException(status_code=400, detail="Code is required")

        # Get cost estimation
        cost_estimate = get_multi_ai_service().estimate_analysis_cost(code, model)
        
        return cost_estimate

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
def _calculate_comparison_metrics(results: List[AnalysisResult]) -> Dict:
    """Calculate comparison metrics between model results"""
    if len(results) < 2:
        return {}

    # Extract all patterns
    all_patterns = set()
    model_patterns = {}

    for result in results:
        model_patterns[result.model.value] = set(result.patterns)
        all_patterns.update(result.patterns)

    # Calculate consensus and disputes
    consensus_patterns = (
        set.intersection(*model_patterns.values()) if model_patterns else set()
    )
    disputed_patterns = []

    for pattern in all_patterns:
        models_detecting = [
            model for model, patterns in model_patterns.items() if pattern in patterns
        ]
        if len(models_detecting) < len(results):  # Not all models detected it
            disputed_patterns.append(
                {
                    "pattern": pattern,
                    "detected_by": models_detecting,
                    "agreement_ratio": len(models_detecting) / len(results),
                }
            )

    # Calculate agreement score
    total_possible_agreements = len(all_patterns) * len(results)
    actual_agreements = sum(
        sum(
            1
            for model_patterns_set in model_patterns.values()
            if pattern in model_patterns_set
        )
        for pattern in all_patterns
    )
    agreement_score = (
        actual_agreements / total_possible_agreements
        if total_possible_agreements > 0
        else 0
    )

    # Performance comparison
    processing_times = {r.model.value: r.processing_time for r in results}
    costs = {}

    for r in results:
        if r.token_usage and r.model in get_multi_ai_service().available_models:
            cost = (
                r.token_usage.get("total_tokens", 0)
                * get_multi_ai_service().available_models[r.model].cost_per_1k_tokens
                / 1000
            )
            costs[r.model.value] = cost

    return {
        "consensus_patterns": list(consensus_patterns),
        "disputed_patterns": disputed_patterns,
        "agreement_score": round(agreement_score, 3),
        "performance": {
            "processing_times": processing_times,
            "fastest_model": (
                min(processing_times.items(), key=lambda x: x[1])[0]
                if processing_times
                else None
            ),
            "cost_estimates": costs,
            "most_cost_effective": (
                min(costs.items(), key=lambda x: x[1])[0] if costs else None
            ),
        },
        "diversity_score": (
            len(all_patterns) / len(results) if results else 0
        ),  # How many unique patterns per model
        "consistency_score": (
            len(consensus_patterns) / len(all_patterns) if all_patterns else 0
        ),
    }
