# app/api/multi_model_analysis.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.multi_model_ai_service import (
    MultiModelAIService,
    AIModel,
    AnalysisResult,
)
from app.models.repository import (
    Repository,
    AIModel as AIModelDB,
    AIAnalysisResult,
    ModelComparison,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/multi-model", tags=["Multi-Model Analysis"])

# Initialize multi-model service
multi_ai_service = MultiModelAIService()


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
        models = multi_ai_service.get_available_models()

        return {
            "available_models": models,
            "total_count": len(models),
            "categories": {
                "local": [m for m in models.values() if m.cost_per_1k_tokens == 0.0],
                "api": [m for m in models.values() if m.cost_per_1k_tokens > 0.0],
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
        model = AIModel(model_name)

        # Perform analysis
        result = await multi_ai_service.analyze_with_model(
            request.code, request.language, model
        )

        return {
            "model": model.value,
            "model_info": multi_ai_service.available_models[model].__dict__,
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
        models = [AIModel(name) for name in request.models]

        # Perform parallel analysis with all models
        results = await multi_ai_service.compare_models(
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
                    "model_info": multi_ai_service.available_models[
                        result.model
                    ].__dict__,
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


@router.post("/analyze/multi-model")
async def analyze_with_multiple_models(
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

        # Run parallel analysis with multiple models
        results = await multi_ai_service.analyze_repository_parallel(
            repository_id, selected_models
        )

        # Store comparison in database
        comparison = ModelComparison(
            id=str(uuid.uuid4()),
            repository_id=repository_id,
            models_compared=selected_models,
            consensus_patterns=results["consensus_patterns"],
            disputed_patterns=results["disputed_patterns"],
            agreement_score=results["agreement_score"],
        )
        db.add(comparison)
        db.commit()

        return ModelComparisonResponse(**results)

    except Exception as e:
        logger.error(f"Multi-model analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/repository")
async def analyze_repository_with_models(
    request: ComparisonAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Analyze entire repository with multiple models for comprehensive comparison"""
    try:
        # Get repository
        repo = (
            db.query(Repository).filter(Repository.id == request.repository_id).first()
        )
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

        # Start background analysis with multiple models
        background_tasks.add_task(
            _analyze_repository_with_multiple_models,
            request.repository_id,
            request.models,
            request.branch,
            request.commit_limit,
        )

        return {
            "message": "Multi-model repository analysis started",
            "repository_id": request.repository_id,
            "models": request.models,
            "estimated_completion": "5-15 minutes depending on repository size and model count",
        }

    except Exception as e:
        logger.error(f"Repository multi-model analysis error: {e}")
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

        # Get detailed results
        ai_results = (
            db.query(AIAnalysisResult)
            .filter(
                AIAnalysisResult.analysis_session_id == comparison.analysis_session_id
            )
            .all()
        )

        return {
            "comparison_id": comparison_id,
            "models_compared": comparison.models_compared,
            "consensus_patterns": comparison.consensus_patterns,
            "disputed_patterns": comparison.disputed_patterns,
            "agreement_score": comparison.model_agreement_score,
            "detailed_results": [
                {
                    "model": result.model.name,
                    "patterns": result.detected_patterns,
                    "complexity_score": result.complexity_score,
                    "confidence": result.confidence_score,
                    "processing_time": result.processing_time,
                    "cost": result.cost_estimate,
                }
                for result in ai_results
            ],
            "created_at": comparison.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting comparison results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_name}/stats")
async def get_model_statistics(model_name: str, db: Session = Depends(get_db)):
    """Get usage statistics and performance metrics for a specific model"""
    try:
        model = db.query(AIModelDB).filter(AIModelDB.name == model_name).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Get analysis results for this model
        results = (
            db.query(AIAnalysisResult)
            .filter(AIAnalysisResult.model_id == model.id)
            .all()
        )

        if not results:
            return {
                "model": model_name,
                "usage_stats": {
                    "total_analyses": 0,
                    "avg_processing_time": 0,
                    "avg_confidence": 0,
                    "total_cost": 0,
                },
            }

        # Calculate statistics
        total_analyses = len(results)
        avg_processing_time = sum(r.processing_time for r in results) / total_analyses
        avg_confidence = sum(r.confidence_score for r in results) / total_analyses
        total_cost = sum(r.cost_estimate for r in results)

        # Pattern statistics
        all_patterns = []
        for result in results:
            all_patterns.extend(result.detected_patterns)

        pattern_counts = {}
        for pattern in all_patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        return {
            "model": model_name,
            "model_info": {
                "display_name": model.display_name,
                "provider": model.provider,
                "strengths": model.strengths,
            },
            "usage_stats": {
                "total_analyses": total_analyses,
                "avg_processing_time": round(avg_processing_time, 3),
                "avg_confidence": round(avg_confidence, 3),
                "total_cost": round(total_cost, 4),
                "success_rate": len([r for r in results if not r.error_message])
                / total_analyses,
            },
            "pattern_stats": {
                "most_detected_patterns": sorted(
                    pattern_counts.items(), key=lambda x: x[1], reverse=True
                )[:10],
                "unique_patterns_detected": len(pattern_counts),
            },
        }

    except Exception as e:
        logger.error(f"Error getting model statistics: {e}")
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
    costs = {
        r.model.value: (
            r.token_usage.get("total_tokens", 0)
            * multi_ai_service.available_models[r.model].cost_per_1k_tokens
            / 1000
        )
        for r in results
        if r.token_usage
    }

    return {
        "consensus_patterns": list(consensus_patterns),
        "disputed_patterns": disputed_patterns,
        "agreement_score": round(agreement_score, 3),
        "performance": {
            "processing_times": processing_times,
            "fastest_model": min(processing_times.items(), key=lambda x: x[1])[0],
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


async def _analyze_repository_with_multiple_models(
    repository_id: str, model_names: List[str], branch: str, commit_limit: int
):
    """Background task for analyzing repository with multiple models"""
    # This would integrate with your existing repository analysis
    # but run it with multiple AI models in parallel
    pass
