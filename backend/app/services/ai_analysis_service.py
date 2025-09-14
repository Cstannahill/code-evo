# app/services/ai_analysis_service.py - MongoDB AI Analysis Service
"""
MongoDB AI Analysis Service for Code Evolution Tracker

This service provides comprehensive AI analysis management using MongoDB.
It handles AI model management, analysis sessions, and single model analysis,
and performance tracking with comprehensive error handling and optimization.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from collections import defaultdict
import json

from app.core.database import get_enhanced_database_manager
from app.models.repository import (
    AnalysisSession,
    AIModel,
    AIAnalysisResult,
    # ModelComparison removed - using single model analysis only
    ModelBenchmark,
    Repository,
    get_available_ai_models,
    get_analysis_sessions_by_repository,
    # get_model_comparisons_by_repository removed - using single model analysis only
)

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """
    Comprehensive AI analysis service providing AI model management,
    analysis session tracking, and single model analysis capabilities.
    """

    def __init__(self):
        """Initialize AI analysis service with enhanced database manager"""
        try:
            self.db_manager = get_enhanced_database_manager()
            self.engine = self.db_manager.engine
            self.cache = self.db_manager.cache
            logger.info("AIAnalysisService initialized with enhanced MongoDB backend")
        except Exception as e:
            logger.warning(f"⚠️  AIAnalysisService initialized without MongoDB: {e}")
            self.db_manager = None
            self.engine = None
            self.cache = None

        # Service metrics
        self._operation_count = 0
        self._error_count = 0
        self._total_analysis_time = 0.0
        self._total_token_usage = 0

    async def register_ai_model(
        self,
        name: str,
        display_name: str,
        provider: str,
        model_type: str = "code_analysis",
        context_window: Optional[int] = None,
        cost_per_1k_tokens: float = 0.0,
        strengths: List[str] = None,
        is_available: bool = True,
    ) -> AIModel:
        """
        Register a new AI model or update existing one

        Args:
            name: Model name (e.g., "codellama:7b")
            display_name: Human-readable display name
            provider: Model provider (e.g., "Ollama", "OpenAI")
            model_type: Type of model
            context_window: Context window size
            cost_per_1k_tokens: Cost per 1k tokens
            strengths: List of model strengths
            is_available: Whether model is available

        Returns:
            AIModel: Created or updated AI model
        """
        try:
            self._operation_count += 1

            # Check if model exists
            existing = await self.engine.find_one(AIModel, AIModel.name == name)

            if existing:
                # Update existing model
                existing.display_name = display_name
                existing.provider = provider
                existing.model_type = model_type
                existing.context_window = context_window
                existing.cost_per_1k_tokens = cost_per_1k_tokens
                existing.strengths = strengths or []
                existing.is_available = is_available

                saved_model = await self.engine.save(existing)
                logger.info(f"✅ Updated AI model: {name}")
            else:
                # Create new model
                model = AIModel(
                    name=name,
                    display_name=display_name,
                    provider=provider,
                    model_type=model_type,
                    context_window=context_window,
                    cost_per_1k_tokens=cost_per_1k_tokens,
                    strengths=strengths or [],
                    is_available=is_available,
                )

                saved_model = await self.engine.save(model)
                logger.info(f"✅ Registered new AI model: {name}")

            # Update cache
            cache_key = f"ai_model:{name}"
            await self.cache.set(cache_key, saved_model.dict(), ttl=3600)

            return saved_model

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to register AI model {name}: {e}")
            raise

    async def create_analysis_session(
        self, repository_id: str, configuration: Optional[Dict[str, Any]] = None
    ) -> AnalysisSession:
        """
        Create a new analysis session

        Args:
            repository_id: Repository ID
            configuration: Optional analysis configuration

        Returns:
            AnalysisSession: Created analysis session
        """
        try:
            self._operation_count += 1

            session = AnalysisSession(
                repository_id=ObjectId(repository_id),
                status="running",
                configuration=configuration or {},
            )

            saved_session = await self.engine.save(session)

            logger.info(
                f"✅ Created analysis session {saved_session.id} for repository {repository_id}"
            )
            return saved_session

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to create analysis session: {e}")
            raise

    async def update_analysis_session(
        self,
        session_id: str,
        status: Optional[str] = None,
        commits_analyzed: Optional[int] = None,
        patterns_found: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update analysis session status and metrics

        Args:
            session_id: Analysis session ID
            status: New status
            commits_analyzed: Number of commits analyzed
            patterns_found: Number of patterns found
            error_message: Error message if any

        Returns:
            bool: True if updated successfully
        """
        try:
            self._operation_count += 1

            obj_id = ObjectId(session_id)
            session = await self.engine.find_one(
                AnalysisSession, AnalysisSession.id == obj_id
            )

            if not session:
                logger.warning(f"⚠️ Analysis session {session_id} not found")
                return False

            # Update fields
            if status:
                session.status = status
                if status in ["completed", "failed"]:
                    session.completed_at = datetime.utcnow()

            if commits_analyzed is not None:
                session.commits_analyzed = commits_analyzed

            if patterns_found is not None:
                session.patterns_found = patterns_found

            if error_message:
                session.error_message = error_message

            await self.engine.save(session)

            logger.info(f"✅ Updated analysis session {session_id} status to {status}")
            return True

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to update analysis session: {e}")
            return False

    async def record_ai_analysis_result(
        self,
        analysis_session_id: str,
        model_name: str,
        code_snippet: str,
        language: Optional[str] = None,
        detected_patterns: List[str] = None,
        complexity_score: Optional[float] = None,
        skill_level: Optional[str] = None,
        suggestions: List[str] = None,
        confidence_score: Optional[float] = None,
        processing_time: Optional[float] = None,
        token_usage: Optional[Dict[str, Any]] = None,
        cost_estimate: float = 0.0,
        error_message: Optional[str] = None,
    ) -> AIAnalysisResult:
        """
        Record AI analysis result with comprehensive metadata

        Args:
            analysis_session_id: Analysis session ID
            model_name: Name of the AI model used
            code_snippet: Code that was analyzed
            language: Programming language
            detected_patterns: List of detected pattern names
            complexity_score: Complexity score
            skill_level: Skill level assessment
            suggestions: List of suggestions
            confidence_score: Overall confidence score
            processing_time: Processing time in seconds
            token_usage: Token usage information
            cost_estimate: Estimated cost
            error_message: Error message if any

        Returns:
            AIAnalysisResult: Created analysis result
        """
        try:
            self._operation_count += 1

            # Get model ID
            model = await self.engine.find_one(AIModel, AIModel.name == model_name)
            if not model:
                # Register unknown model
                model = await self.register_ai_model(
                    name=model_name,
                    display_name=model_name,
                    provider="Unknown",
                    is_available=False,
                )

            # Create analysis result
            result = AIAnalysisResult(
                analysis_session_id=ObjectId(analysis_session_id),
                model_id=model.id,
                code_snippet=code_snippet,
                language=language,
                detected_patterns=detected_patterns or [],
                complexity_score=complexity_score,
                skill_level=skill_level,
                suggestions=suggestions or [],
                confidence_score=confidence_score,
                processing_time=processing_time,
                token_usage=token_usage,
                cost_estimate=cost_estimate,
                error_message=error_message,
            )

            saved_result = await self.engine.save(result)

            # Update service metrics
            if processing_time:
                self._total_analysis_time += processing_time

            if token_usage and "total_tokens" in token_usage:
                self._total_token_usage += token_usage["total_tokens"]

            # Update model usage statistics
            model.usage_count += 1
            model.last_used = datetime.utcnow()
            await self.engine.save(model)

            logger.debug(f"✅ Recorded AI analysis result for model {model_name}")
            return saved_result

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to record AI analysis result: {e}")
            raise

    # compare_models method removed - using single model analysis only

    async def get_model_performance_stats(
        self, model_name: Optional[str] = None, days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance statistics for AI models

        Args:
            model_name: Optional specific model name
            days_back: Number of days to analyze

        Returns:
            Dict containing performance statistics
        """
        try:
            self._operation_count += 1

            # Check cache first
            cache_key = f"model_performance:{model_name or 'all'}:{days_back}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"📋 Cache hit for model performance stats")
                return cached

            start_date = datetime.utcnow() - timedelta(days=days_back)

            # Build query conditions
            conditions = [AIAnalysisResult.created_at >= start_date]

            if model_name:
                model = await self.engine.find_one(AIModel, AIModel.name == model_name)
                if model:
                    conditions.append(AIAnalysisResult.model_id == model.id)
                else:
                    return {"error": f"Model '{model_name}' not found"}

            # Get analysis results
            results = await self.engine.find(AIAnalysisResult, *conditions)

            # Get model details
            model_ids = list(set(result.model_id for result in results))
            models = await self.engine.find(AIModel, AIModel.id.in_(model_ids))
            model_lookup = {model.id: model for model in models}

            # Calculate statistics
            model_stats = defaultdict(
                lambda: {
                    "total_analyses": 0,
                    "total_processing_time": 0.0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "avg_confidence": [],
                    "avg_complexity": [],
                    "patterns_detected": [],
                    "success_rate": 0,
                    "errors": 0,
                }
            )

            for result in results:
                model = model_lookup.get(result.model_id)
                if not model:
                    continue

                stats = model_stats[model.name]
                stats["total_analyses"] += 1

                if result.processing_time:
                    stats["total_processing_time"] += result.processing_time

                if result.token_usage and "total_tokens" in result.token_usage:
                    stats["total_tokens"] += result.token_usage["total_tokens"]

                stats["total_cost"] += result.cost_estimate

                if result.confidence_score is not None:
                    stats["avg_confidence"].append(result.confidence_score)

                if result.complexity_score is not None:
                    stats["avg_complexity"].append(result.complexity_score)

                if result.detected_patterns:
                    stats["patterns_detected"].extend(result.detected_patterns)

                if result.error_message:
                    stats["errors"] += 1
                else:
                    stats["success_rate"] += 1

            # Calculate final metrics
            performance_data = {}
            for model_name, stats in model_stats.items():
                if stats["total_analyses"] > 0:
                    stats["success_rate"] = (
                        stats["success_rate"] / stats["total_analyses"]
                    ) * 100
                    stats["avg_processing_time"] = (
                        stats["total_processing_time"] / stats["total_analyses"]
                    )
                    stats["avg_tokens_per_analysis"] = (
                        stats["total_tokens"] / stats["total_analyses"]
                    )
                    stats["avg_cost_per_analysis"] = (
                        stats["total_cost"] / stats["total_analyses"]
                    )

                    if stats["avg_confidence"]:
                        stats["avg_confidence_score"] = sum(
                            stats["avg_confidence"]
                        ) / len(stats["avg_confidence"])
                    else:
                        stats["avg_confidence_score"] = 0

                    if stats["avg_complexity"]:
                        stats["avg_complexity_score"] = sum(
                            stats["avg_complexity"]
                        ) / len(stats["avg_complexity"])
                    else:
                        stats["avg_complexity_score"] = 0

                    stats["unique_patterns_detected"] = len(
                        set(stats["patterns_detected"])
                    )

                    # Clean up intermediate data
                    del stats["avg_confidence"]
                    del stats["avg_complexity"]
                    del stats["patterns_detected"]

                performance_data[model_name] = stats

            result = {
                "model_filter": model_name,
                "analysis_period_days": days_back,
                "models": performance_data,
                "summary": {
                    "total_models": len(performance_data),
                    "total_analyses": sum(
                        stats["total_analyses"] for stats in performance_data.values()
                    ),
                    "total_processing_time": sum(
                        stats["total_processing_time"]
                        for stats in performance_data.values()
                    ),
                    "total_cost": sum(
                        stats["total_cost"] for stats in performance_data.values()
                    ),
                    "avg_success_rate": (
                        sum(
                            stats["success_rate"] for stats in performance_data.values()
                        )
                        / len(performance_data)
                        if performance_data
                        else 0
                    ),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Cache for 30 minutes
            await self.cache.set(cache_key, result, ttl=1800)

            logger.info(
                f"✅ Generated performance stats for {len(performance_data)} models"
            )
            return result

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to get model performance stats: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def get_repository_ai_insights(
        self, repository_id: str, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get AI-powered insights for a repository

        Args:
            repository_id: Repository ID
            limit: Number of recent sessions to analyze

        Returns:
            Dict containing AI insights
        """
        try:
            self._operation_count += 1

            obj_id = ObjectId(repository_id)

            # Get recent analysis sessions
            sessions = await get_analysis_sessions_by_repository(
                self.engine, obj_id, limit=limit
            )

            if not sessions:
                return {
                    "repository_id": repository_id,
                    "insights": [],
                    "message": "No AI analysis sessions found for this repository",
                }

            # Get AI analysis results for these sessions
            session_ids = [session.id for session in sessions]
            results = await self.engine.find(
                AIAnalysisResult, AIAnalysisResult.analysis_session_id.in_(session_ids)
            )

            # Get model comparisons
            comparisons = await get_model_comparisons_by_repository(
                self.engine, obj_id, limit=5
            )

            # Analyze results for insights
            insights = []

            # Pattern detection insights
            all_patterns = []
            complexity_scores = []

            for result in results:
                all_patterns.extend(result.detected_patterns)
                if result.complexity_score:
                    complexity_scores.append(result.complexity_score)

            if all_patterns:
                pattern_frequency = Counter(all_patterns)
                top_patterns = pattern_frequency.most_common(5)

                insights.append(
                    {
                        "type": "pattern_analysis",
                        "title": "Most Common Patterns",
                        "description": f"Top patterns detected across {len(results)} AI analyses",
                        "data": {
                            "top_patterns": [
                                {"pattern": p, "count": c} for p, c in top_patterns
                            ],
                            "total_unique_patterns": len(pattern_frequency),
                            "total_pattern_occurrences": len(all_patterns),
                        },
                    }
                )

            # Complexity analysis
            if complexity_scores:
                avg_complexity = sum(complexity_scores) / len(complexity_scores)
                complexity_trend = (
                    "increasing"
                    if avg_complexity > 6
                    else "decreasing" if avg_complexity < 4 else "stable"
                )

                insights.append(
                    {
                        "type": "complexity_analysis",
                        "title": "Code Complexity Assessment",
                        "description": f"Average complexity score: {avg_complexity:.2f}/10",
                        "data": {
                            "average_complexity": round(avg_complexity, 2),
                            "complexity_trend": complexity_trend,
                            "total_analyses": len(complexity_scores),
                            "complexity_distribution": {
                                "low": len([s for s in complexity_scores if s < 4]),
                                "medium": len(
                                    [s for s in complexity_scores if 4 <= s < 7]
                                ),
                                "high": len([s for s in complexity_scores if s >= 7]),
                            },
                        },
                    }
                )

            # Model comparison insights
            if comparisons:
                latest_comparison = comparisons[0]
                if latest_comparison.agreement_score is not None:
                    agreement_level = (
                        "high"
                        if latest_comparison.agreement_score > 0.8
                        else (
                            "medium"
                            if latest_comparison.agreement_score > 0.5
                            else "low"
                        )
                    )

                    insights.append(
                        {
                            "type": "model_agreement",
                            "title": "AI Model Agreement",
                            "description": f"Latest comparison shows {agreement_level} agreement between models",
                            "data": {
                                "agreement_score": latest_comparison.agreement_score,
                                "agreement_level": agreement_level,
                                "models_compared": latest_comparison.models_compared,
                                "consensus_patterns": latest_comparison.consensus_patterns,
                                "disputed_patterns_count": (
                                    len(latest_comparison.disputed_patterns)
                                    if latest_comparison.disputed_patterns
                                    else 0
                                ),
                            },
                        }
                    )

            result = {
                "repository_id": repository_id,
                "insights": insights,
                "analysis_summary": {
                    "total_sessions": len(sessions),
                    "total_ai_results": len(results),
                    "total_comparisons": len(comparisons),
                    "latest_session_status": sessions[0].status if sessions else None,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"✅ Generated {len(insights)} AI insights for repository {repository_id}"
            )
            return result

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to get repository AI insights: {e}")
            return {
                "repository_id": repository_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def benchmark_model(
        self, model_name: str, benchmark_name: str, test_results: Dict[str, Any]
    ) -> ModelBenchmark:
        """
        Record model benchmark results

        Args:
            model_name: Name of the model
            benchmark_name: Name of the benchmark
            test_results: Benchmark test results

        Returns:
            ModelBenchmark: Created benchmark record
        """
        try:
            self._operation_count += 1

            # Get model
            model = await self.engine.find_one(AIModel, AIModel.name == model_name)
            if not model:
                raise ValueError(f"Model '{model_name}' not found")

            # Create benchmark record
            benchmark = ModelBenchmark(
                model_id=model.id,
                benchmark_name=benchmark_name,
                benchmark_version=test_results.get("version", "1.0"),
                test_dataset_size=test_results.get("dataset_size"),
                accuracy_score=test_results.get("accuracy"),
                precision_score=test_results.get("precision"),
                recall_score=test_results.get("recall"),
                f1_score=test_results.get("f1_score"),
                avg_processing_time=test_results.get("avg_processing_time"),
                avg_cost_per_analysis=test_results.get("avg_cost"),
                pattern_detection_rate=test_results.get("pattern_detection_rate"),
                false_positive_rate=test_results.get("false_positive_rate"),
                false_negative_rate=test_results.get("false_negative_rate"),
                notes=test_results.get("notes"),
            )

            saved_benchmark = await self.engine.save(benchmark)

            logger.info(
                f"✅ Recorded benchmark '{benchmark_name}' for model {model_name}"
            )
            return saved_benchmark

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to record model benchmark: {e}")
            raise

    async def get_service_health(self) -> Dict[str, Any]:
        """Get AI analysis service health metrics"""
        try:
            # Check if MongoDB is available
            if self.db_manager is None or self.engine is None:
                return {
                    "status": "unavailable",
                    "error": "MongoDB not initialized",
                    "metrics": {
                        "total_operations": self._operation_count,
                        "total_errors": self._error_count,
                        "error_rate_percent": round(
                            (self._error_count / max(self._operation_count, 1)) * 100, 2
                        ),
                        "total_analysis_time": round(self._total_analysis_time, 2),
                        "total_token_usage": self._total_token_usage,
                        "total_models": 0,
                        "total_sessions": 0,
                        "total_results": 0,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Check database connectivity
            db_health = await self.db_manager.health_check()

            # Get service metrics
            error_rate = (self._error_count / max(self._operation_count, 1)) * 100

            # Quick counts
            model_count = await self.engine.count(AIModel)
            session_count = await self.engine.count(AnalysisSession)
            result_count = await self.engine.count(AIAnalysisResult)

            return {
                "status": (
                    "healthy"
                    if db_health.get("is_connected", False)
                    and db_health.get("ping_success", False)
                    else "degraded"
                ),
                "database": db_health,
                "metrics": {
                    "total_operations": self._operation_count,
                    "total_errors": self._error_count,
                    "error_rate_percent": round(error_rate, 2),
                    "total_analysis_time": round(self._total_analysis_time, 2),
                    "total_token_usage": self._total_token_usage,
                    "total_models": model_count,
                    "total_sessions": session_count,
                    "total_results": result_count,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ AI analysis service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_repository_enhanced_analysis(
        self, repository_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get enhanced analysis results for a repository if available"""
        try:
            self._operation_count += 1
            from app.models.repository import (
                SecurityAnalysis,
                PerformanceAnalysis,
                ArchitecturalAnalysis,
                EnhancedPatternAnalysis,
                EnhancedQualityAnalysis,
                EnsembleAnalysisResult,
                IncrementalAnalysisSnapshot,
            )

            repo_oid = ObjectId(repository_id)

            # Fetch the most recent records per analysis type
            security = await self.engine.find_one(
                SecurityAnalysis,
                SecurityAnalysis.repository_id == repo_oid,
                sort=SecurityAnalysis.created_at.desc(),
            )
            performance = await self.engine.find_one(
                PerformanceAnalysis,
                PerformanceAnalysis.repository_id == repo_oid,
                sort=PerformanceAnalysis.created_at.desc(),
            )
            architecture = await self.engine.find_one(
                ArchitecturalAnalysis,
                ArchitecturalAnalysis.repository_id == repo_oid,
                sort=ArchitecturalAnalysis.created_at.desc(),
            )
            pattern = await self.engine.find_one(
                EnhancedPatternAnalysis,
                EnhancedPatternAnalysis.repository_id == repo_oid,
                sort=EnhancedPatternAnalysis.created_at.desc(),
            )
            quality = await self.engine.find_one(
                EnhancedQualityAnalysis,
                EnhancedQualityAnalysis.repository_id == repo_oid,
                sort=EnhancedQualityAnalysis.created_at.desc(),
            )
            ensemble = await self.engine.find(
                EnsembleAnalysisResult,
                EnsembleAnalysisResult.repository_id == repo_oid,
                limit=5,
                sort=EnsembleAnalysisResult.created_at.desc(),
            )
            # Optional: last incremental snapshot
            snapshot = await self.engine.find_one(
                IncrementalAnalysisSnapshot,
                IncrementalAnalysisSnapshot.repository_id == repo_oid,
                sort=IncrementalAnalysisSnapshot.created_at.desc(),
            )

            result: Dict[str, Any] = {
                "security_analysis": security.dict() if security else None,
                "performance_analysis": performance.dict() if performance else None,
                "architectural_analysis": architecture.dict() if architecture else None,
                "pattern_analysis": pattern.dict() if pattern else None,
                "quality_analysis": quality.dict() if quality else None,
                "ensemble_metadata": [e.dict() for e in ensemble] if ensemble else [],
                "incremental_analysis": snapshot.dict() if snapshot else None,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Enhanced analysis fetched for repository {repository_id} (keys: "
                f"{', '.join([k for k,v in result.items() if v])})"
            )
            return result

        except Exception as e:
            logger.error(
                f"Failed to get enhanced analysis for repository {repository_id}: {e}"
            )
            self._error_count += 1
            return None

    async def list_repository_models(self, repository_id: str) -> Dict[str, Any]:
        """List available analyses grouped by model for a repository"""
        try:
            self._operation_count += 1
            from app.models.repository import (
                EnhancedPatternAnalysis,
                EnhancedQualityAnalysis,
                PatternOccurrence,
            )

            repo_oid = ObjectId(repository_id)

            patterns = await self.engine.find(
                EnhancedPatternAnalysis,
                EnhancedPatternAnalysis.repository_id == repo_oid,
            )
            qualities = await self.engine.find(
                EnhancedQualityAnalysis,
                EnhancedQualityAnalysis.repository_id == repo_oid,
            )
            occurrences = await self.engine.find(
                PatternOccurrence,
                PatternOccurrence.repository_id == repo_oid,
            )

            models: Dict[str, Dict[str, Any]] = {}
            # Aggregate pattern analyses by model_used
            for p in patterns:
                model = p.model_used or "unknown"
                entry = models.setdefault(
                    model,
                    {
                        "model": model,
                        "types": set(),
                        "count": 0,
                        "latest": None,
                    },
                )
                entry["types"].add("pattern")
                entry["count"] += 1
                if not entry["latest"] or p.created_at > entry["latest"]:
                    entry["latest"] = p.created_at

            # Aggregate quality analyses by model_used
            for q in qualities:
                model = q.model_used or "unknown"
                entry = models.setdefault(
                    model,
                    {
                        "model": model,
                        "types": set(),
                        "count": 0,
                        "latest": None,
                    },
                )
                entry["types"].add("quality")
                entry["count"] += 1
                if not entry["latest"] or q.created_at > entry["latest"]:
                    entry["latest"] = q.created_at

            # Include models from raw pattern occurrences as a fallback
            for occ in occurrences:
                if getattr(occ, "ai_model_used", None):
                    model = occ.ai_model_used
                    entry = models.setdefault(
                        model,
                        {
                            "model": model,
                            "types": set(),
                            "count": 0,
                            "latest": None,
                        },
                    )
                    entry["types"].add("occurrence")
                    entry["count"] += 1
                    if not entry["latest"] or occ.detected_at > entry["latest"]:
                        entry["latest"] = occ.detected_at

            # Normalize sets and datetimes
            normalized = [
                {
                    "model": m,
                    "analysis_types": sorted(list(v["types"])),
                    "count": v["count"],
                    "latest": (v["latest"].isoformat() if v["latest"] else None),
                }
                for m, v in models.items()
            ]

            # Sort by latest desc
            normalized.sort(key=lambda x: x["latest"] or "", reverse=True)

            return {
                "repository_id": repository_id,
                "models": normalized,
                "total_models": len(normalized),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            self._error_count += 1
            logger.error(f"Failed to list repository models for {repository_id}: {e}")
            return {"repository_id": repository_id, "models": [], "error": str(e)}

    async def get_repository_analysis_by_model(
        self, repository_id: str, model: str
    ) -> Dict[str, Any]:
        """Get latest enhanced analyses for a repository filtered by model identifier"""
        try:
            self._operation_count += 1
            from app.models.repository import (
                EnhancedPatternAnalysis,
                EnhancedQualityAnalysis,
            )

            repo_oid = ObjectId(repository_id)

            pattern = await self.engine.find_one(
                EnhancedPatternAnalysis,
                (EnhancedPatternAnalysis.repository_id == repo_oid)
                & (EnhancedPatternAnalysis.model_used == model),
                sort=EnhancedPatternAnalysis.created_at.desc(),
            )
            quality = await self.engine.find_one(
                EnhancedQualityAnalysis,
                (EnhancedQualityAnalysis.repository_id == repo_oid)
                & (EnhancedQualityAnalysis.model_used == model),
                sort=EnhancedQualityAnalysis.created_at.desc(),
            )

            return {
                "repository_id": repository_id,
                "model": model,
                "pattern_analysis": pattern.dict() if pattern else None,
                "quality_analysis": quality.dict() if quality else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            self._error_count += 1
            logger.error(f"Failed to get analysis by model for {repository_id}: {e}")
            return {"repository_id": repository_id, "model": model, "error": str(e)}


# Convenience function for getting service instance
async def get_ai_analysis_service() -> AIAnalysisService:
    """Get AI analysis service instance"""
    from app.core.service_manager import get_ai_analysis_service as get_singleton

    return get_singleton()
