# app/services/pattern_service.py - MongoDB Pattern Service
"""
MongoDB Pattern Service for Code Evolution Tracker

This service provides comprehensive pattern management and analysis using MongoDB.
It handles pattern detection, storage, analysis, and querying with performance
optimization and comprehensive error handling.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from collections import Counter, defaultdict

from app.core.database import get_enhanced_database_manager
from app.models.repository import (
    Pattern,
    PatternOccurrence,
    Repository,
    AIAnalysisResult,
    AIModel,
    ModelComparison,
)

logger = logging.getLogger(__name__)


class PatternService:
    """
    Comprehensive pattern service providing pattern management,
    analysis, and querying with MongoDB backend and caching.
    """

    def __init__(self):
        """Initialize pattern service with enhanced database manager"""
        self.db_manager = get_enhanced_database_manager()
        self.engine = self.db_manager.engine
        self.cache = self.db_manager.cache

        # Service metrics
        self._operation_count = 0
        self._error_count = 0

        logger.info("PatternService initialized with enhanced MongoDB backend")

    async def create_or_get_pattern(
        self,
        name: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        complexity_level: Optional[str] = None,
        is_antipattern: bool = False,
    ) -> Pattern:
        """
        Create a new pattern or get existing one

        Args:
            name: Pattern name
            category: Pattern category
            description: Pattern description
            complexity_level: Complexity level (simple, intermediate, advanced)
            is_antipattern: Whether this is an antipattern

        Returns:
            Pattern: Created or existing pattern
        """
        try:
            self._operation_count += 1

            # Check cache first
            cache_key = f"pattern:name:{name}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"📋 Cache hit for pattern {name}")
                return Pattern(**cached)

            # Check if pattern exists
            existing = await self.engine.find_one(Pattern, Pattern.name == name)
            if existing:
                # Cache and return existing
                await self.cache.set(cache_key, existing.dict(), ttl=3600)
                return existing

            # Create new pattern
            pattern = Pattern(
                name=name,
                category=category,
                description=description,
                complexity_level=complexity_level,
                is_antipattern=is_antipattern,
            )

            saved_pattern = await self.engine.save(pattern)

            # Cache the new pattern
            await self.cache.set(cache_key, saved_pattern.dict(), ttl=3600)

            logger.info(f"✅ Created new pattern: {name}")
            return saved_pattern

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to create/get pattern {name}: {e}")
            raise

    async def add_pattern_occurrence(
        self,
        repository_id: str,
        pattern_name: str,
        file_path: Optional[str] = None,
        code_snippet: Optional[str] = None,
        line_number: Optional[int] = None,
        confidence_score: float = 1.0,
        commit_id: Optional[str] = None,
        ai_model_used: Optional[str] = None,
        model_confidence: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        token_usage: Optional[Dict[str, Any]] = None,
        ai_analysis_metadata: Optional[Dict[str, Any]] = None,
    ) -> PatternOccurrence:
        """
        Add a pattern occurrence with comprehensive metadata

        Args:
            repository_id: Repository ID
            pattern_name: Name of the pattern
            file_path: File path where pattern was found
            code_snippet: Code snippet containing the pattern
            line_number: Line number in the file
            confidence_score: Confidence score (0-1)
            commit_id: Optional commit ID
            ai_model_used: AI model that detected the pattern
            model_confidence: AI model confidence score
            processing_time_ms: Processing time in milliseconds
            token_usage: Token usage information
            ai_analysis_metadata: Additional AI analysis metadata

        Returns:
            PatternOccurrence: Created pattern occurrence
        """
        try:
            self._operation_count += 1

            # Get or create pattern
            pattern = await self.create_or_get_pattern(pattern_name)

            # Create pattern occurrence
            occurrence = PatternOccurrence(
                repository_id=ObjectId(repository_id),
                pattern_id=pattern.id,
                commit_id=ObjectId(commit_id) if commit_id else None,
                file_path=file_path,
                code_snippet=code_snippet,
                line_number=line_number,
                confidence_score=confidence_score,
                ai_model_used=ai_model_used,
                model_confidence=model_confidence,
                processing_time_ms=processing_time_ms,
                token_usage=token_usage,
                ai_analysis_metadata=ai_analysis_metadata,
            )

            saved_occurrence = await self.engine.save(occurrence)

            # Update pattern statistics cache
            await self._invalidate_pattern_cache(repository_id, str(pattern.id))

            logger.debug(f"✅ Added pattern occurrence: {pattern_name} in {file_path}")
            return saved_occurrence

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to add pattern occurrence: {e}")
            raise

    async def get_repository_patterns(
        self,
        repository_id: str,
        include_occurrences: bool = True,
        category_filter: Optional[str] = None,
        complexity_filter: Optional[str] = None,
        antipattern_only: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Get all patterns for a repository with detailed statistics

        Args:
            repository_id: Repository ID
            include_occurrences: Whether to include occurrence details
            category_filter: Filter by pattern category
            complexity_filter: Filter by complexity level
            antipattern_only: Filter for antipatterns only

        Returns:
            Dict containing patterns and statistics
        """
        try:
            self._operation_count += 1

            # Check cache first
            cache_key = f"repo_patterns:{repository_id}:{category_filter}:{complexity_filter}:{antipattern_only}"
            cached = await self.cache.get(cache_key)
            if cached and not include_occurrences:  # Only use cache for summary data
                logger.debug(f"📋 Cache hit for repository patterns {repository_id}")
                return cached

            obj_id = ObjectId(repository_id)

            # Get all pattern occurrences for the repository
            occurrences = await self.engine.find(
                PatternOccurrence, PatternOccurrence.repository_id == obj_id
            )

            # Get unique pattern IDs
            pattern_ids = list(set(occ.pattern_id for occ in occurrences))

            # Get pattern details
            pattern_conditions = [Pattern.id.in_(pattern_ids)]
            if category_filter:
                pattern_conditions.append(Pattern.category == category_filter)
            if complexity_filter:
                pattern_conditions.append(Pattern.complexity_level == complexity_filter)
            if antipattern_only is not None:
                pattern_conditions.append(Pattern.is_antipattern == antipattern_only)

            patterns = await self.engine.find(Pattern, *pattern_conditions)

            # Create pattern lookup
            pattern_lookup = {str(p.id): p for p in patterns}

            # Build pattern statistics
            pattern_stats = {}
            occurrence_details = defaultdict(list)

            for occurrence in occurrences:
                pattern_id = str(occurrence.pattern_id)

                # Skip if pattern not in filtered results
                if pattern_id not in pattern_lookup:
                    continue

                # Initialize pattern stats if needed
                if pattern_id not in pattern_stats:
                    pattern = pattern_lookup[pattern_id]
                    pattern_stats[pattern_id] = {
                        "pattern": pattern.dict(),
                        "total_occurrences": 0,
                        "unique_files": set(),
                        "confidence_scores": [],
                        "ai_models_used": set(),
                        "avg_confidence": 0.0,
                        "avg_model_confidence": 0.0,
                        "first_detected": occurrence.detected_at,
                        "last_detected": occurrence.detected_at,
                        "total_processing_time_ms": 0,
                    }

                stats = pattern_stats[pattern_id]

                # Update statistics
                stats["total_occurrences"] += 1
                if occurrence.file_path:
                    stats["unique_files"].add(occurrence.file_path)
                stats["confidence_scores"].append(occurrence.confidence_score)

                if occurrence.ai_model_used:
                    stats["ai_models_used"].add(occurrence.ai_model_used)

                if occurrence.processing_time_ms:
                    stats["total_processing_time_ms"] += occurrence.processing_time_ms

                # Update date range
                if occurrence.detected_at < stats["first_detected"]:
                    stats["first_detected"] = occurrence.detected_at
                if occurrence.detected_at > stats["last_detected"]:
                    stats["last_detected"] = occurrence.detected_at

                # Store occurrence details if requested
                if include_occurrences:
                    occurrence_details[pattern_id].append(occurrence.dict())

            # Calculate averages and finalize statistics
            for pattern_id, stats in pattern_stats.items():
                # Convert sets to lists and calculate averages
                stats["unique_files"] = list(stats["unique_files"])
                stats["ai_models_used"] = list(stats["ai_models_used"])
                stats["files_affected"] = len(stats["unique_files"])

                if stats["confidence_scores"]:
                    stats["avg_confidence"] = sum(stats["confidence_scores"]) / len(
                        stats["confidence_scores"]
                    )
                    stats["min_confidence"] = min(stats["confidence_scores"])
                    stats["max_confidence"] = max(stats["confidence_scores"])

                # Remove intermediate data
                del stats["confidence_scores"]

                # Add occurrence details if requested
                if include_occurrences:
                    stats["occurrences"] = occurrence_details[pattern_id]

            # Build result
            result = {
                "repository_id": repository_id,
                "total_patterns": len(pattern_stats),
                "patterns": list(pattern_stats.values()),
                "summary": {
                    "total_occurrences": sum(
                        stats["total_occurrences"] for stats in pattern_stats.values()
                    ),
                    "total_files_affected": len(
                        set().union(
                            *[stats["unique_files"] for stats in pattern_stats.values()]
                        )
                    ),
                    "antipatterns_count": sum(
                        1
                        for stats in pattern_stats.values()
                        if stats["pattern"]["is_antipattern"]
                    ),
                    "categories": list(
                        set(
                            stats["pattern"]["category"]
                            for stats in pattern_stats.values()
                            if stats["pattern"]["category"]
                        )
                    ),
                    "complexity_levels": list(
                        set(
                            stats["pattern"]["complexity_level"]
                            for stats in pattern_stats.values()
                            if stats["pattern"]["complexity_level"]
                        )
                    ),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Cache summary data
            if not include_occurrences:
                await self.cache.set(cache_key, result, ttl=1800)  # 30 minutes

            logger.info(
                f"✅ Retrieved {len(pattern_stats)} patterns for repository {repository_id}"
            )
            return result

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to get repository patterns: {e}")
            return {
                "repository_id": repository_id,
                "total_patterns": 0,
                "patterns": [],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_pattern_timeline(
        self,
        repository_id: str,
        pattern_name: Optional[str] = None,
        date_range_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Get pattern timeline for repository showing evolution over time

        Args:
            repository_id: Repository ID
            pattern_name: Optional specific pattern name
            date_range_days: Number of days to include in timeline

        Returns:
            Dict containing timeline data
        """
        try:
            self._operation_count += 1

            obj_id = ObjectId(repository_id)
            start_date = datetime.utcnow() - timedelta(days=date_range_days)

            # Build query conditions
            conditions = [
                PatternOccurrence.repository_id == obj_id,
                PatternOccurrence.detected_at >= start_date,
            ]

            if pattern_name:
                pattern = await self.engine.find_one(
                    Pattern, Pattern.name == pattern_name
                )
                if pattern:
                    conditions.append(PatternOccurrence.pattern_id == pattern.id)
                else:
                    return {"error": f"Pattern '{pattern_name}' not found"}

            # Get occurrences in date range
            occurrences = await self.engine.find(
                PatternOccurrence, *conditions, sort=PatternOccurrence.detected_at.asc()
            )

            # Group by date and pattern
            timeline_data = defaultdict(lambda: defaultdict(int))
            pattern_names = {}

            for occurrence in occurrences:
                date_key = occurrence.detected_at.strftime("%Y-%m-%d")
                pattern_id = str(occurrence.pattern_id)
                timeline_data[date_key][pattern_id] += 1

                # Cache pattern name
                if pattern_id not in pattern_names:
                    pattern = await self.engine.find_one(
                        Pattern, Pattern.id == occurrence.pattern_id
                    )
                    pattern_names[pattern_id] = pattern.name if pattern else "Unknown"

            # Convert to timeline format
            timeline = []
            for date_str in sorted(timeline_data.keys()):
                date_data = {
                    "date": date_str,
                    "total_patterns": sum(timeline_data[date_str].values()),
                    "patterns": {},
                }

                for pattern_id, count in timeline_data[date_str].items():
                    pattern_name = pattern_names.get(pattern_id, "Unknown")
                    date_data["patterns"][pattern_name] = count

                timeline.append(date_data)

            result = {
                "repository_id": repository_id,
                "timeline": timeline,
                "date_range_days": date_range_days,
                "total_data_points": len(timeline),
                "pattern_filter": pattern_name,
                "summary": {
                    "total_occurrences": sum(day["total_patterns"] for day in timeline),
                    "unique_patterns": len(pattern_names),
                    "patterns_tracked": list(pattern_names.values()),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"✅ Generated pattern timeline for repository {repository_id}")
            return result

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to get pattern timeline: {e}")
            return {
                "repository_id": repository_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def analyze_pattern_trends(
        self, repository_id: str, analysis_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze pattern trends and provide insights

        Args:
            repository_id: Repository ID
            analysis_days: Number of days to analyze

        Returns:
            Dict containing trend analysis
        """
        try:
            self._operation_count += 1

            obj_id = ObjectId(repository_id)
            start_date = datetime.utcnow() - timedelta(days=analysis_days)

            # Get recent occurrences
            recent_occurrences = await self.engine.find(
                PatternOccurrence,
                PatternOccurrence.repository_id == obj_id,
                PatternOccurrence.detected_at >= start_date,
                sort=[("detected_at", 1)],
            )

            # Get all-time occurrences for comparison
            all_occurrences = await self.engine.find(
                PatternOccurrence, PatternOccurrence.repository_id == obj_id
            )

            # Analyze trends
            recent_patterns = Counter()
            all_time_patterns = Counter()

            for occurrence in recent_occurrences:
                recent_patterns[str(occurrence.pattern_id)] += 1

            for occurrence in all_occurrences:
                all_time_patterns[str(occurrence.pattern_id)] += 1

            # Get pattern details
            pattern_ids = list(
                set(recent_patterns.keys()) | set(all_time_patterns.keys())
            )
            patterns = await self.engine.find(
                Pattern, Pattern.id.in_([ObjectId(pid) for pid in pattern_ids])
            )
            pattern_lookup = {str(p.id): p for p in patterns}

            # Calculate trends
            trends = []
            for pattern_id in pattern_ids:
                pattern = pattern_lookup.get(pattern_id)
                if not pattern:
                    continue

                recent_count = recent_patterns.get(pattern_id, 0)
                all_time_count = all_time_patterns.get(pattern_id, 0)

                # Calculate trend percentage
                historical_avg = (all_time_count - recent_count) / max(analysis_days, 1)
                recent_avg = recent_count / analysis_days

                if historical_avg > 0:
                    trend_percentage = (
                        (recent_avg - historical_avg) / historical_avg
                    ) * 100
                else:
                    trend_percentage = 100.0 if recent_count > 0 else 0.0

                trend_direction = (
                    "increasing"
                    if trend_percentage > 10
                    else "decreasing" if trend_percentage < -10 else "stable"
                )

                trends.append(
                    {
                        "pattern": pattern.dict(),
                        "recent_count": recent_count,
                        "all_time_count": all_time_count,
                        "trend_percentage": round(trend_percentage, 2),
                        "trend_direction": trend_direction,
                        "recent_avg_per_day": round(recent_avg, 2),
                        "significance": (
                            "high"
                            if abs(trend_percentage) > 50
                            else "medium" if abs(trend_percentage) > 20 else "low"
                        ),
                    }
                )

            # Sort by trend significance
            trends.sort(key=lambda x: abs(x["trend_percentage"]), reverse=True)

            # Generate insights
            insights = []

            # Top increasing patterns
            increasing = [t for t in trends if t["trend_direction"] == "increasing"][:3]
            if increasing:
                insights.append(
                    {
                        "type": "increasing_patterns",
                        "title": "Patterns on the Rise",
                        "description": f"Top {len(increasing)} patterns showing increased usage",
                        "patterns": [t["pattern"]["name"] for t in increasing],
                    }
                )

            # Concerning antipatterns
            concerning = [
                t
                for t in trends
                if t["pattern"]["is_antipattern"]
                and t["trend_direction"] == "increasing"
            ]
            if concerning:
                insights.append(
                    {
                        "type": "antipattern_alert",
                        "title": "Antipattern Alert",
                        "description": f"{len(concerning)} antipatterns showing increased usage",
                        "patterns": [t["pattern"]["name"] for t in concerning],
                    }
                )

            result = {
                "repository_id": repository_id,
                "analysis_period_days": analysis_days,
                "trends": trends,
                "insights": insights,
                "summary": {
                    "total_patterns_analyzed": len(trends),
                    "increasing_patterns": len(
                        [t for t in trends if t["trend_direction"] == "increasing"]
                    ),
                    "decreasing_patterns": len(
                        [t for t in trends if t["trend_direction"] == "decreasing"]
                    ),
                    "stable_patterns": len(
                        [t for t in trends if t["trend_direction"] == "stable"]
                    ),
                    "high_significance_trends": len(
                        [t for t in trends if t["significance"] == "high"]
                    ),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"✅ Analyzed pattern trends for repository {repository_id}")
            return result

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to analyze pattern trends: {e}")
            return {
                "repository_id": repository_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_global_pattern_stats(self) -> Dict[str, Any]:
        """
        Get global pattern statistics across all repositories

        Returns:
            Dict containing global pattern statistics
        """
        try:
            self._operation_count += 1

            # Check cache first
            cache_key = "global_pattern_stats"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug("📋 Cache hit for global pattern stats")
                return cached

            # Get all patterns
            patterns = await self.engine.find(Pattern)

            # Get all pattern occurrences
            occurrences = await self.engine.find(PatternOccurrence)

            # Calculate statistics
            pattern_stats = defaultdict(
                lambda: {
                    "total_occurrences": 0,
                    "repositories": set(),
                    "files": set(),
                    "avg_confidence": [],
                }
            )

            for occurrence in occurrences:
                pattern_id = str(occurrence.pattern_id)
                stats = pattern_stats[pattern_id]
                stats["total_occurrences"] += 1
                stats["repositories"].add(str(occurrence.repository_id))
                if occurrence.file_path:
                    stats["files"].add(occurrence.file_path)
                stats["avg_confidence"].append(occurrence.confidence_score)

            # Build result
            pattern_results = []
            for pattern in patterns:
                pattern_id = str(pattern.id)
                stats = pattern_stats[pattern_id]

                pattern_results.append(
                    {
                        "pattern": pattern.dict(),
                        "total_occurrences": stats["total_occurrences"],
                        "repositories_count": len(stats["repositories"]),
                        "unique_files_count": len(stats["files"]),
                        "avg_confidence": (
                            round(
                                sum(stats["avg_confidence"])
                                / len(stats["avg_confidence"]),
                                3,
                            )
                            if stats["avg_confidence"]
                            else 0
                        ),
                        "popularity_score": stats["total_occurrences"]
                        * len(stats["repositories"]),
                    }
                )

            # Sort by popularity
            pattern_results.sort(key=lambda x: x["popularity_score"], reverse=True)

            # Calculate global metrics
            total_repositories = len(
                set().union(
                    *[stats["repositories"] for stats in pattern_stats.values()]
                )
            )

            result = {
                "patterns": pattern_results,
                "total_patterns": len(patterns),
                "total_occurrences": sum(
                    occ["total_occurrences"] for occ in pattern_results
                ),
                "total_repositories": total_repositories,
                "antipatterns_count": sum(
                    1 for p in pattern_results if p["pattern"]["is_antipattern"]
                ),
                "categories": list(
                    set(
                        p["pattern"]["category"]
                        for p in pattern_results
                        if p["pattern"]["category"]
                    )
                ),
                "top_patterns": pattern_results[:10],
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Cache for 1 hour
            await self.cache.set(cache_key, result, ttl=3600)

            logger.info(f"✅ Generated global pattern statistics")
            return result

        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Failed to get global pattern stats: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def _invalidate_pattern_cache(
        self, repository_id: str, pattern_id: str
    ) -> None:
        """Invalidate pattern-related cache entries"""
        try:
            cache_keys = [
                f"repo_patterns:{repository_id}:*",
                f"pattern:id:{pattern_id}",
                "global_pattern_stats",
            ]

            for key in cache_keys:
                if "*" in key:
                    # For wildcard patterns, we'd need to implement cache key scanning
                    # For now, just log that we should invalidate these
                    logger.debug(f"Should invalidate cache pattern: {key}")
                else:
                    await self.cache.delete(key)

        except Exception as e:
            logger.warning(f"⚠️ Failed to invalidate cache: {e}")

    async def get_service_health(self) -> Dict[str, Any]:
        """Get pattern service health metrics"""
        try:
            # Check database connectivity
            db_health = await self.db_manager.health_check()

            # Get service metrics
            error_rate = (self._error_count / max(self._operation_count, 1)) * 100

            # Quick pattern count check
            pattern_count = await self.engine.count(Pattern)
            occurrence_count = await self.engine.count(PatternOccurrence)

            return {
                "status": "healthy" if db_health.get("is_connected", False) and db_health.get("ping_success", False) else "degraded",
                "database": db_health,
                "metrics": {
                    "total_operations": self._operation_count,
                    "total_errors": self._error_count,
                    "error_rate_percent": round(error_rate, 2),
                    "total_patterns": pattern_count,
                    "total_occurrences": occurrence_count,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Pattern service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Convenience function for getting service instance
async def get_pattern_service() -> PatternService:
    """Get pattern service instance"""
    return PatternService()
