from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from typing import List, Optional, Dict, Any, cast
from datetime import datetime
import logging
from bson import ObjectId

from app.core.service_manager import (
    get_repository_service,
    get_pattern_service,
    get_ai_analysis_service,
    get_analysis_service,
)
from app.tasks.analysis_tasks import (
    analyze_repository_background,
    analyze_repository_incremental_background,
)
from pydantic import BaseModel, Field
from app.api.auth import get_current_user, get_user_api_key
from app.models.repository import User, Repository, UserRepository
from app.core.database import get_engine

logger = logging.getLogger(__name__)

# Router for repositories API
router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


def get_services():
    """Centralized accessor for services used in this module"""
    return (
        get_repository_service(),
        get_pattern_service(),
        get_ai_analysis_service(),
        get_analysis_service(),
    )


class RepositoryCreateWithModel(BaseModel):
    url: str
    branch: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    model_id: Optional[str] = Field(default=None, description="Preferred AI model")
    tags: Optional[List[str]] = Field(default=None)
    is_private: Optional[bool] = Field(default=False)


class RepositorySubmitRequest(BaseModel):
    url: str
    branch: str = Field(default="main")
    commit_limit: int = Field(default=100, ge=1, le=1000)
    candidate_limit: int = Field(default=20, ge=1, le=100)
    analysis_type: str = Field(default="comprehensive")  # or "incremental"
    include_security_scan: bool = Field(default=True)
    include_performance_scan: bool = Field(default=True)
    include_architectural_scan: bool = Field(default=True)
    model_id: Optional[str] = Field(default=None)
    force_reanalyze: bool = Field(default=False)


def convert_objectids_to_strings(obj):
    """Recursively convert ObjectId fields to strings in dictionaries and lists"""
    if isinstance(obj, dict):
        return {key: convert_objectids_to_strings(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [convert_objectids_to_strings(item) for item in obj]
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj


@router.get("", response_model=Dict[str, Any])
async def list_repositories(
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of repositories to return"
    ),
    offset: int = Query(0, ge=0, description="Number of repositories to skip"),
):
    """List all repositories with pagination"""
    try:
        repository_service, _, _, _ = get_services()

        # Get repositories using the service
        repositories_data = await repository_service.list_repositories()

        # Apply pagination to the repositories list
        repositories = repositories_data.get("repositories", [])
        total_count = len(repositories)

        # Apply offset and limit
        paginated_repos = repositories[offset : offset + limit]

        result = {
            "repositories": convert_objectids_to_strings(paginated_repos),
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_count,
        }

        logger.info(
            f"Listed {len(paginated_repos)} repositories (total: {total_count})"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list repositories: {str(e)}"
        )


@router.post("", response_model=Dict[str, Any])
async def create_repository(
    repo_data: RepositoryCreateWithModel,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user),
    force_reanalyze: bool = Query(
        False, description="Force re-analysis of existing repository"
    ),
):
    """Create a repository and start background analysis with Git cloning"""
    try:
        logger.info(f"🚀 Repository submission request: {repo_data.url}")

        # Validate Git URL
        if not repo_data.url or not repo_data.url.startswith(
            ("http", "git@", "git://")
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid Git repository URL. Must be HTTP(S), SSH, or Git protocol URL.",
            )

        repository_service, _, ai_analysis_service, _ = get_services()

        # Check if repository already exists
        existing_repos = await repository_service.list_repositories()
        existing = None
        for repo in existing_repos.get("repositories", []):
            if repo.get("url") == repo_data.url:
                existing = repo
                break

        if existing:
            logger.info(f"📋 Found existing repository: {existing['name']}")
            # Track user access to existing repository
            if current_user:
                await repository_service.track_user_repository_access(
                    str(current_user.id), existing["id"]
                )
                logger.info(
                    f"👤 User {current_user.username} accessed existing repository {existing['name']}"
                )

            # Determine if we should re-analyze based on model change
            should_reanalyze = False
            if repo_data.model_id:
                try:
                    latest_model_used = None
                    latest_dt = None
                    enhanced = (
                        await ai_analysis_service.get_repository_enhanced_analysis(
                            existing["id"]
                        )
                    )
                    if enhanced:
                        for key in ("pattern_analysis", "quality_analysis"):
                            item = enhanced.get(key)
                            if isinstance(item, dict):
                                created_at = item.get("created_at")
                                dt = None
                                if isinstance(created_at, str):
                                    try:
                                        dt = datetime.fromisoformat(created_at)
                                    except Exception:
                                        dt = None
                                elif created_at:
                                    dt = created_at
                                if (
                                    latest_dt is None
                                    or (dt and latest_dt and dt > latest_dt)
                                    or (dt and latest_dt is None)
                                ):
                                    latest_dt = dt
                                    latest_model_used = item.get("model_used")
                    if latest_model_used is None:
                        models_info = await ai_analysis_service.list_repository_models(
                            existing["id"]
                        )
                        models = (
                            models_info.get("models", [])
                            if isinstance(models_info, dict)
                            else []
                        )
                        if models:
                            latest_model_used = models[0].get("model")
                    if (
                        latest_model_used is None
                        or repo_data.model_id != latest_model_used
                    ):
                        should_reanalyze = True
                except Exception as e:
                    logger.warning(f"Could not determine latest model used: {e}")
                    # When in doubt and a specific model was requested, reanalyze
                    should_reanalyze = True

            if (
                not force_reanalyze
                and existing.get("status") == "completed"
                and not should_reanalyze
            ):
                logger.info("✅ Repository already analyzed, returning existing data")
                return convert_objectids_to_strings(existing)

            # Update status and restart analysis
            await repository_service.update_repository_status(
                existing["id"], "analyzing"
            )
            logger.info("🔄 Restarting analysis for existing repository")
            background_tasks.add_task(
                analyze_repository_background,
                repo_data.url,
                repo_data.branch or "main",
                100,  # commit_limit
                20,  # candidate_limit
                repo_data.model_id,
            )
            return convert_objectids_to_strings(existing)

        # Create new repository
        repo_name = repo_data.url.rstrip("/\n").split("/")[-1].replace(".git", "")
        logger.info(f"📝 Creating new repository: {repo_name}")

        repository = await repository_service.create_repository(
            url=repo_data.url,
            name=repo_name,
            branch=repo_data.branch or "main",
            description=repo_data.description,
        )

        # Track user-repository association if user is authenticated
        if current_user:
            await repository_service.track_user_repository_access(
                str(current_user.id), str(repository.id)
            )
            logger.info(
                f"👤 User {current_user.username} created and owns repository {repo_name}"
            )

        # Start background analysis with Git cloning
        logger.info(f"🚀 Starting background analysis for {repo_name}")
        background_tasks.add_task(
            analyze_repository_background,
            repo_data.url,
            repo_data.branch or "main",
            100,  # commit_limit
            20,  # candidate_limit
            repo_data.model_id,
        )

        # Convert ObjectIds to strings before returning
        try:
            result = convert_objectids_to_strings(repository.model_dump())
        except AttributeError:
            # Fallback for older versions
            result = convert_objectids_to_strings(repository.dict())
        logger.info(f"✅ Repository created successfully: {repo_name}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create repository: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create repository: {str(e)}"
        )


@router.post("/submit", response_model=Dict[str, Any])
async def submit_repository_for_analysis(
    submit_request: RepositorySubmitRequest,
    background_tasks: BackgroundTasks,
):
    """Submit a Git repository for comprehensive analysis with deep commit analysis"""
    try:
        logger.info(f"🚀 Repository submission for analysis: {submit_request.url}")

        # Validate Git URL format
        if not submit_request.url or not submit_request.url.startswith(
            ("http", "git@", "git://")
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid Git repository URL. Must be HTTP(S), SSH, or Git protocol URL.",
            )

        # Validate analysis parameters
        if submit_request.commit_limit < 1 or submit_request.commit_limit > 1000:
            raise HTTPException(
                status_code=400, detail="Commit limit must be between 1 and 1000"
            )
        if submit_request.candidate_limit < 1 or submit_request.candidate_limit > 100:
            raise HTTPException(
                status_code=400, detail="Candidate limit must be between 1 and 100"
            )

        repository_service, _, ai_analysis_service, _ = get_services()

        # Check if repository already exists
        existing_repos = await repository_service.list_repositories()
        existing = None
        for repo in existing_repos.get("repositories", []):
            if repo.get("url") == submit_request.url:
                existing = repo
                break

        if existing:
            logger.info(f"📋 Found existing repository: {existing['name']}")
            # Determine if we should re-analyze based on model change
            should_reanalyze = False
            if submit_request.model_id:
                try:
                    latest_model_used = None
                    latest_dt = None
                    enhanced = (
                        await ai_analysis_service.get_repository_enhanced_analysis(
                            existing["id"]
                        )
                    )
                    if enhanced:
                        for key in ("pattern_analysis", "quality_analysis"):
                            item = enhanced.get(key)
                            if isinstance(item, dict):
                                created_at = item.get("created_at")
                                dt = None
                                if isinstance(created_at, str):
                                    try:
                                        dt = datetime.fromisoformat(created_at)
                                    except Exception:
                                        dt = None
                                elif created_at:
                                    dt = created_at
                                if (
                                    latest_dt is None
                                    or (dt and latest_dt and dt > latest_dt)
                                    or (dt and latest_dt is None)
                                ):
                                    latest_dt = dt
                                    latest_model_used = item.get("model_used")
                    if latest_model_used is None:
                        models_info = await ai_analysis_service.list_repository_models(
                            existing["id"]
                        )
                        models = (
                            models_info.get("models", [])
                            if isinstance(models_info, dict)
                            else []
                        )
                        if models:
                            latest_model_used = models[0].get("model")
                    if (
                        latest_model_used is None
                        or submit_request.model_id != latest_model_used
                    ):
                        should_reanalyze = True
                except Exception as e:
                    logger.warning(f"Could not determine latest model used: {e}")
                    should_reanalyze = True

            if (
                (not submit_request.force_reanalyze)
                and existing.get("status") == "completed"
                and not should_reanalyze
            ):
                logger.info("✅ Repository already analyzed, returning existing data")
                return {
                    "message": "Repository already analyzed",
                    "repository": existing,
                    "analysis_status": "completed",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Update status and restart analysis
            await repository_service.update_repository_status(
                existing["id"], "analyzing"
            )
            logger.info("🔄 Restarting analysis for existing repository")
        else:
            # Create new repository
            repo_name = (
                submit_request.url.rstrip("/\n").split("/")[-1].replace(".git", "")
            )
            logger.info(f"📝 Creating new repository: {repo_name}")
            existing = await repository_service.create_repository(
                url=submit_request.url,
                name=repo_name,
                branch=submit_request.branch,
                description=f"Submitted for {submit_request.analysis_type} analysis",
            )

        # Start enhanced background analysis
        logger.info(
            f"🚀 Starting {submit_request.analysis_type} analysis for {existing['name']}"
        )

        # Choose analysis method based on type
        if submit_request.analysis_type == "incremental":
            background_tasks.add_task(
                analyze_repository_incremental_background,
                submit_request.url,
                submit_request.branch,
                submit_request.commit_limit,
                submit_request.candidate_limit,
                submit_request.model_id,
                submit_request.include_security_scan,
                submit_request.include_performance_scan,
                submit_request.include_architectural_scan,
            )
        else:
            background_tasks.add_task(
                analyze_repository_background,
                submit_request.url,
                submit_request.branch,
                submit_request.commit_limit,
                submit_request.candidate_limit,
                submit_request.model_id,
            )

        # Convert ObjectIds to strings before returning
        result = convert_objectids_to_strings(existing)
        return {
            "message": f"Repository submitted for {submit_request.analysis_type} analysis",
            "repository": result,
            "analysis_config": {
                "commit_limit": submit_request.commit_limit,
                "candidate_limit": submit_request.candidate_limit,
                "analysis_type": submit_request.analysis_type,
                "security_scan": submit_request.include_security_scan,
                "performance_scan": submit_request.include_performance_scan,
                "architectural_scan": submit_request.include_architectural_scan,
                "model_id": submit_request.model_id,
            },
            "status": "submitted",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to submit repository for analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit repository for analysis: {str(e)}",
        )


@router.get("/{repo_id}", response_model=Dict[str, Any])
async def get_repository(repo_id: str):
    """Get repository by ID"""
    try:
        repository_service, _, _, _ = get_services()
        repository = await repository_service.get_repository(repo_id)
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")
        # Convert ObjectIds to strings before returning
        return convert_objectids_to_strings(repository.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repository {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get repository")


@router.get("/{repo_id}/analysis", response_model=Dict[str, Any])
async def get_repository_analysis(repo_id: str):
    """Get complete repository analysis data"""
    try:
        repository_service, pattern_service, ai_analysis_service, analysis_service = (
            get_services()
        )
        analysis = await repository_service.get_repository_analysis(repo_id)
        patterns_data = await pattern_service.get_repository_patterns(
            repo_id, include_occurrences=True
        )
        pattern_timeline_result = await pattern_service.get_pattern_timeline(repo_id)

        # Extract timeline data from the service response
        timeline_data = pattern_timeline_result.get("timeline", [])

        status = analysis_service.get_status()
        ai_ok = status.get("ollama_available", False)
        ai_insights = []
        if ai_ok:
            try:
                insight_data = {
                    "patterns": patterns_data,
                    "technologies": [
                        t.get("name") for t in analysis.get("technologies", [])
                    ],
                    "commits": analysis.get("commits_summary", {}).get(
                        "total_commits", 0
                    ),
                }
                ai_insights = await analysis_service.generate_insights(insight_data)
            except Exception as e:
                logger.warning(f"Failed to generate AI insights: {e}")

        pattern_stats: Dict[str, Dict[str, Any]] = {}
        occurrences: List[Dict[str, Any]] = []
        for item in patterns_data.get("patterns", []):
            p = item.get("pattern", {})
            name = p.get("name")
            if not name:
                continue
            pattern_stats[name] = {
                "name": name,
                "category": p.get("category"),
                "occurrences": item.get("total_occurrences", 0),
                "complexity_level": p.get("complexity_level", "intermediate"),
                "is_antipattern": p.get("is_antipattern", False),
                "description": p.get("description"),
            }
            occurrences.extend(item.get("occurrences", []))

        analysis_sessions = analysis.get("analysis_sessions", [])
        latest_session = analysis_sessions[0] if analysis_sessions else None

        response_data = {
            "repository_id": repo_id,
            "repository": analysis.get("repository", {}),
            "status": analysis.get("repository", {}).get("status", "unknown"),
            "analysis_session": latest_session,
            "technologies": _organize_technologies_by_category(
                analysis.get("technologies", [])
            ),
            "patterns": occurrences,
            "pattern_timeline": {
                "timeline": timeline_data,
                "summary": {
                    "total_months": len(timeline_data),
                    "patterns_tracked": list(pattern_stats.keys()),
                },
            },
            "pattern_statistics": pattern_stats,
            "insights": ai_insights,
            "ai_powered": ai_ok,
            "summary": {
                "total_patterns": len(pattern_stats),
                "total_commits": analysis.get("commits_summary", {}).get(
                    "total_commits", 0
                ),
                "total_technologies": len(analysis.get("technologies", [])),
                "complexity_distribution": _get_complexity_distribution(
                    patterns_data.get("patterns", [])
                ),
                "antipatterns_detected": patterns_data.get("summary", {}).get(
                    "antipatterns_count", 0
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Convert any ObjectIds to strings before returning
        return convert_objectids_to_strings(response_data)
    except Exception as e:
        logger.error(f"Failed to get repository analysis for {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get repository analysis")


@router.get("/{repo_id}/patterns", response_model=Dict[str, Any])
async def get_repository_patterns(repo_id: str, include_occurrences: bool = True):
    """Get pattern statistics and occurrences for a repository"""
    try:
        _, pattern_service, _, _ = get_services()
        data = await pattern_service.get_repository_patterns(
            repo_id, include_occurrences=include_occurrences
        )
        return convert_objectids_to_strings(data)
    except Exception as e:
        logger.error(f"Failed to get patterns for repository {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get repository patterns")


@router.get("/{repo_id}/analysis/enhanced", response_model=Dict[str, Any])
async def get_enhanced_repository_analysis(repo_id: str):
    """Get enhanced repository analysis with security, performance, and architectural insights"""
    try:
        repository_service, pattern_service, ai_analysis_service, analysis_service = (
            get_services()
        )

        # Get base analysis first
        base_analysis = await get_repository_analysis(repo_id)

        # Try to get enhanced analysis results if available
        enhanced_data = {}
        try:
            # Check if we have enhanced analysis data in MongoDB
            # This would be populated by the enhanced analysis background tasks
            enhanced_results = (
                await ai_analysis_service.get_repository_enhanced_analysis(repo_id)
            )
            if enhanced_results:
                enhanced_data.update(
                    {
                        "security_analysis": enhanced_results.get("security_analysis"),
                        "performance_analysis": enhanced_results.get(
                            "performance_analysis"
                        ),
                        "architectural_analysis": enhanced_results.get(
                            "architectural_analysis"
                        ),
                        "ensemble_metadata": enhanced_results.get("ensemble_metadata"),
                        "incremental_analysis": enhanced_results.get(
                            "incremental_analysis"
                        ),
                    }
                )
        except Exception as e:
            logger.warning(f"Enhanced analysis data not available for {repo_id}: {e}")
            # Generate enhanced analysis using available services
            base_for_enhanced: Dict[str, Any] = (
                base_analysis if isinstance(base_analysis, dict) else {}
            )
            enhanced_data = await _generate_enhanced_analysis(base_for_enhanced)

        # Merge base analysis with enhanced data
        base = base_analysis if isinstance(base_analysis, dict) else {}
        result = {
            **base,
            **enhanced_data,
            "enhanced": True,
            "analysis_type": "comprehensive",
        }

        return convert_objectids_to_strings(result)

    except Exception as e:
        logger.error(f"Failed to get enhanced analysis for {repo_id}: {e}")
        # Fallback to regular analysis if enhanced fails
        return await get_repository_analysis(repo_id)


@router.get("/{repo_id}/timeline", response_model=Dict[str, Any])
async def get_repository_timeline(repo_id: str):
    """Get repository timeline"""
    try:
        repository_service, pattern_service, _, _ = get_services()
        repository = await repository_service.get_repository(repo_id)
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")
        timeline_result = await pattern_service.get_pattern_timeline(repo_id)
        timeline_data = timeline_result.get("timeline", [])
        analysis = await repository_service.get_repository_analysis(repo_id)
        commits_summary = analysis.get("commits_summary", {})
        response_data = {
            "repository_id": repo_id,
            "timeline": timeline_data,
            "summary": {
                "total_months": len(timeline_data),
                "total_commits": commits_summary.get("total_commits", 0),
                "total_patterns": len(
                    set(
                        pattern
                        for entry in timeline_data
                        for pattern in entry.get("patterns", {}).keys()
                    )
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        return convert_objectids_to_strings(response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repository timeline for {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get repository timeline")


def _organize_technologies_by_category(
    technologies: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    organized = {
        "language": [],
        "framework": [],
        "library": [],
        "tool": [],
        "database": [],
        "platform": [],
        "other": [],
    }
    for tech in technologies:
        category = tech.get("category", "other").lower()
        category_map = {
            "languages": "language",
            "frameworks": "framework",
            "libraries": "library",
            "tools": "tool",
            "databases": "database",
            "platforms": "platform",
        }
        mapped_category = category_map.get(category, category)
        if mapped_category not in organized:
            mapped_category = "other"
        organized[mapped_category].append(
            {
                "id": tech.get("id"),
                "name": tech.get("name"),
                "category": tech.get("category"),
                "first_seen": tech.get("first_seen"),
                "last_seen": tech.get("last_seen"),
                "usage_count": tech.get("usage_count", 0),
                "version": tech.get("version"),
                "metadata": tech.get("tech_metadata", {}),
            }
        )
    return organized


def _get_complexity_distribution(patterns: List[Dict[str, Any]]) -> Dict[str, int]:
    distribution = {"simple": 0, "intermediate": 0, "advanced": 0}
    for p in patterns:
        level = (
            p.get("pattern", {}).get("complexity_level")
            or p.get("complexity_level")
            or "intermediate"
        )
        if level in distribution:
            distribution[level] += 1
    return distribution


@router.get("/{repo_id}/analyses/models", response_model=Dict[str, Any])
async def list_repository_models(repo_id: str):
    """List available analyses grouped by model for a repository"""
    try:
        _, _, ai_analysis_service, _ = get_services()
        data = await ai_analysis_service.list_repository_models(repo_id)
        return convert_objectids_to_strings(data)
    except Exception as e:
        logger.error(f"Failed to list models for repository {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list repository models")


@router.get("/{repo_id}/analysis/by-model", response_model=Dict[str, Any])
async def get_repository_analysis_by_model(
    repo_id: str, model: str = Query(..., description="AI model identifier")
):
    """Get latest enhanced analyses for a repository filtered by model"""
    try:
        _, _, ai_analysis_service, _ = get_services()
        data = await ai_analysis_service.get_repository_analysis_by_model(
            repo_id, model
        )
        return convert_objectids_to_strings(data)
    except Exception as e:
        logger.error(f"Failed to get analysis by model for {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis by model")


async def _generate_enhanced_analysis(base_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate enhanced analysis data using pattern and technology information."""
    try:
        patterns = base_analysis.get("pattern_statistics", {})
        technologies = base_analysis.get("technologies", {})
        summary = base_analysis.get("summary", {})

        # Security Analysis
        security_score = _calculate_security_score(patterns, technologies)
        security_analysis = {
            "overall_score": security_score,
            "risk_level": (
                "low"
                if security_score > 80
                else "medium" if security_score > 60 else "high"
            ),
            "total_vulnerabilities": max(0, (100 - security_score) // 10),
            "vulnerabilities_by_severity": _categorize_security_issues(patterns),
            "recommendations": _generate_security_recommendations(
                patterns, technologies
            ),
            "security_patterns": _identify_security_patterns(patterns),
        }

        # Performance Analysis
        performance_score = _calculate_performance_score(patterns, technologies)
        performance_analysis = {
            "overall_score": performance_score,
            "performance_grade": _score_to_grade(performance_score),
            "total_issues": max(0, (100 - performance_score) // 8),
            "optimizations": _generate_performance_recommendations(
                patterns, technologies
            ),
            "performance_patterns": _identify_performance_patterns(patterns),
        }

        # Architectural Analysis
        arch_score = _calculate_architectural_score(patterns, technologies)
        architectural_analysis = {
            "quality_metrics": {
                "overall_score": arch_score,
                "modularity": min(1.0, len(patterns) / 10.0),
                "coupling": max(0.1, 1.0 - (len(patterns) / 20.0)),
                "cohesion": min(1.0, 0.5 + (len(patterns) / 40.0)),
                "grade": _score_to_grade(arch_score),
            },
            "design_patterns": _identify_design_patterns(patterns),
            "architectural_styles": _identify_architectural_styles(
                patterns, technologies
            ),
            "recommendations": _generate_architectural_recommendations(
                patterns, technologies
            ),
        }

        return {
            "security_analysis": security_analysis,
            "performance_analysis": performance_analysis,
            "architectural_analysis": architectural_analysis,
        }

    except Exception as e:
        logger.error(f"Failed to generate enhanced analysis: {e}")
        # Fallback to minimal mock data
        return {
            "security_analysis": {"overall_score": 75, "risk_level": "medium"},
            "performance_analysis": {"overall_score": 80, "performance_grade": "B"},
            "architectural_analysis": {
                "quality_metrics": {"overall_score": 78, "grade": "B+"}
            },
        }


def _calculate_security_score(
    patterns: Dict[str, Any], technologies: Dict[str, Any]
) -> int:
    """Calculate security score based on patterns and technologies."""
    base_score = 85

    # Deduct for potential security issues
    for pattern_name, pattern_data in patterns.items():
        if isinstance(pattern_data, dict):
            if pattern_data.get("is_antipattern", False):
                base_score -= 10

            # Look for security-related patterns
            pattern_lower = pattern_name.lower()
            if any(
                sec in pattern_lower
                for sec in ["sql", "injection", "xss", "csrf", "auth"]
            ):
                if pattern_data.get("is_antipattern", False):
                    base_score -= 15
                else:
                    base_score += 5

    return max(0, min(100, base_score))


def _calculate_performance_score(
    patterns: Dict[str, Any], technologies: Dict[str, Any]
) -> int:
    """Calculate performance score based on patterns and technologies."""
    base_score = 80

    # Add for performance-positive patterns
    for pattern_name, pattern_data in patterns.items():
        if isinstance(pattern_data, dict):
            pattern_lower = pattern_name.lower()
            if any(
                perf in pattern_lower for perf in ["cache", "pool", "lazy", "singleton"]
            ):
                base_score += 5
            elif any(
                anti in pattern_lower
                for anti in ["god_object", "spaghetti", "lava_flow"]
            ):
                base_score -= 10

    return max(0, min(100, base_score))


def _calculate_architectural_score(
    patterns: Dict[str, Any], technologies: Dict[str, Any]
) -> int:
    """Calculate architectural quality score."""
    base_score = 75

    # Add for good architectural patterns
    architectural_patterns = 0
    for pattern_name in patterns.keys():
        pattern_lower = pattern_name.lower()
        if any(
            arch in pattern_lower
            for arch in ["mvc", "mvp", "adapter", "facade", "strategy", "observer"]
        ):
            architectural_patterns += 1

    base_score += min(20, architectural_patterns * 4)

    # Deduct for anti-patterns
    antipattern_count = sum(
        1
        for p in patterns.values()
        if isinstance(p, dict) and p.get("is_antipattern", False)
    )
    base_score -= antipattern_count * 8

    return max(0, min(100, base_score))


def _categorize_security_issues(patterns: Dict[str, Any]) -> Dict[str, int]:
    """Categorize security issues by severity."""
    categories = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for pattern_name, pattern_data in patterns.items():
        if isinstance(pattern_data, dict) and pattern_data.get("is_antipattern", False):
            pattern_lower = pattern_name.lower()
            if any(
                critical in pattern_lower
                for critical in ["sql_injection", "command_injection"]
            ):
                categories["critical"] += 1
            elif any(high in pattern_lower for high in ["auth", "session", "crypto"]):
                categories["high"] += 1
            else:
                categories["medium"] += 1

    return categories


def _generate_security_recommendations(
    patterns: Dict[str, Any], technologies: Dict[str, Any]
) -> List[str]:
    """Generate security recommendations."""
    recommendations = []

    has_auth_patterns = any("auth" in name.lower() for name in patterns.keys())
    has_crypto_patterns = any("crypt" in name.lower() for name in patterns.keys())

    if not has_auth_patterns:
        recommendations.append("Implement proper authentication patterns")
    if not has_crypto_patterns:
        recommendations.append("Add cryptographic security measures")

    antipattern_count = sum(
        1
        for p in patterns.values()
        if isinstance(p, dict) and p.get("is_antipattern", False)
    )
    if antipattern_count > 0:
        recommendations.append(f"Refactor {antipattern_count} identified anti-patterns")

    recommendations.append("Implement input validation throughout the application")
    recommendations.append("Add comprehensive logging and monitoring")

    return recommendations[:5]


def _generate_performance_recommendations(
    patterns: Dict[str, Any], technologies: Dict[str, Any]
) -> List[str]:
    """Generate performance recommendations."""
    recommendations = []

    has_cache_patterns = any("cache" in name.lower() for name in patterns.keys())
    has_pool_patterns = any("pool" in name.lower() for name in patterns.keys())

    if not has_cache_patterns:
        recommendations.append(
            "Implement caching strategies for frequently accessed data"
        )
    if not has_pool_patterns:
        recommendations.append("Use connection pooling for database operations")

    recommendations.append("Optimize database queries and add indexing")
    recommendations.append("Implement lazy loading where appropriate")
    recommendations.append("Consider asynchronous processing for heavy operations")

    return recommendations[:5]


def _generate_architectural_recommendations(
    patterns: Dict[str, Any], technologies: Dict[str, Any]
) -> List[str]:
    """Generate architectural recommendations."""
    recommendations = []

    pattern_count = len(patterns)
    if pattern_count < 5:
        recommendations.append(
            "Consider implementing more design patterns for better structure"
        )
    elif pattern_count > 20:
        recommendations.append("Review pattern usage to avoid over-engineering")

    has_mvc = any("mvc" in name.lower() for name in patterns.keys())
    if not has_mvc:
        recommendations.append(
            "Consider implementing MVC or similar architectural pattern"
        )

    recommendations.append("Maintain clear separation of concerns")
    recommendations.append("Implement dependency injection for better testability")
    recommendations.append("Follow SOLID principles in design decisions")

    return recommendations[:5]


def _identify_security_patterns(patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify security-related patterns."""
    security_patterns = []

    for pattern_name, pattern_data in patterns.items():
        pattern_lower = pattern_name.lower()
        if any(
            sec in pattern_lower
            for sec in ["auth", "security", "validation", "crypto", "hash"]
        ):
            security_patterns.append(
                {
                    "name": pattern_name,
                    "type": "security",
                    "is_positive": not (
                        isinstance(pattern_data, dict)
                        and pattern_data.get("is_antipattern", False)
                    ),
                }
            )

    return security_patterns


def _identify_performance_patterns(patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify performance-related patterns."""
    performance_patterns = []

    for pattern_name, pattern_data in patterns.items():
        pattern_lower = pattern_name.lower()
        if any(
            perf in pattern_lower
            for perf in ["cache", "pool", "lazy", "singleton", "flyweight"]
        ):
            performance_patterns.append(
                {"name": pattern_name, "type": "performance", "impact": "positive"}
            )
        elif any(anti in pattern_lower for anti in ["god_object", "spaghetti"]):
            performance_patterns.append(
                {"name": pattern_name, "type": "performance", "impact": "negative"}
            )

    return performance_patterns


def _identify_design_patterns(patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify classic design patterns."""
    design_patterns = []

    pattern_map = {
        "singleton": 0.9,
        "factory": 0.85,
        "adapter": 0.8,
        "facade": 0.85,
        "strategy": 0.8,
        "observer": 0.75,
        "decorator": 0.8,
        "mvc": 0.9,
        "mvp": 0.85,
    }

    for pattern_name in patterns.keys():
        pattern_lower = pattern_name.lower()
        for design_pattern, confidence in pattern_map.items():
            if design_pattern in pattern_lower:
                design_patterns.append(
                    {
                        "name": design_pattern.title(),
                        "confidence": confidence,
                        "detected_in": pattern_name,
                    }
                )

    return design_patterns


def _identify_architectural_styles(
    patterns: Dict[str, Any], technologies: Dict[str, Any]
) -> List[str]:
    """Identify architectural styles from patterns and technologies."""
    styles = []

    # Check for MVC/MVP patterns
    if any("mvc" in name.lower() for name in patterns.keys()):
        styles.append("MVC")
    if any("mvp" in name.lower() for name in patterns.keys()):
        styles.append("MVP")

    # Check for microservices indicators
    tech_names = []
    if isinstance(technologies, dict):
        for tech_list in technologies.values():
            if isinstance(tech_list, list):
                tech_names.extend(
                    [
                        t.get("name", "") if isinstance(t, dict) else str(t)
                        for t in tech_list
                    ]
                )

    if any(
        "docker" in str(tech).lower() or "kubernetes" in str(tech).lower()
        for tech in tech_names
    ):
        styles.append("Microservices")

    # Default to layered if no specific style detected
    if not styles:
        styles.append("Layered")

    return styles


def _score_to_grade(score: int) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


# User-specific repository endpoints
@router.get("/user/my-repositories", response_model=List[Dict[str, Any]])
async def get_user_repositories(current_user: User = Depends(get_current_user)):
    """Get repositories associated with the current user"""
    try:
        engine = cast(Any, await get_engine())

        # Get user's repository associations
        user_repos = await engine.find(
            UserRepository, UserRepository.user_id == current_user.id
        )

        # Get repository details
        repositories = []
        for user_repo in user_repos:
            try:
                repo = await engine.get(Repository, user_repo.repository_id)
                if repo:
                    repo_dict = repo.dict()
                    repo_dict["access_type"] = user_repo.access_type
                    repo_dict["user_last_accessed"] = user_repo.last_accessed
                    repositories.append(repo_dict)
            except Exception as e:
                logger.warning(
                    f"Could not load repository {user_repo.repository_id}: {e}"
                )

        return convert_objectids_to_strings(repositories)
    except Exception as e:
        logger.error(f"Failed to get user repositories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user repositories")


@router.get("/user/relevant", response_model=List[Dict[str, Any]])
async def get_user_relevant_repositories(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, description="Maximum number of repositories to return"),
    include_global: bool = Query(
        True, description="Include repositories from global pool"
    ),
):
    """Get repositories relevant to the user based on their analysis history and preferences"""
    try:
        engine = cast(Any, await get_engine())

        # Get user's repository associations to understand their interests
        user_repos = await engine.find(
            UserRepository, UserRepository.user_id == current_user.id
        )

        # Extract patterns from user's repositories
        user_languages = set()
        user_tags = set()

        for user_repo in user_repos:
            try:
                repo = await engine.get(Repository, user_repo.repository_id)
                if repo:
                    if repo.primary_language:
                        user_languages.add(repo.primary_language)
                    if repo.tags:
                        user_tags.update(repo.tags)
            except Exception as e:
                logger.warning(
                    f"Could not analyze user repo {user_repo.repository_id}: {e}"
                )

        # Build relevance query
        relevance_criteria = {}

        # Include repositories with matching languages
        if user_languages:
            relevance_criteria["primary_language"] = {"$in": list(user_languages)}

        # Include repositories with matching tags
        if user_tags:
            relevance_criteria["tags"] = {"$in": list(user_tags)}

        # If no specific criteria, include popular repositories
        if not relevance_criteria:
            relevance_criteria["analysis_count"] = {"$gte": 1}

        # Get relevant repositories from global pool
        relevant_repos = []
        if include_global and relevance_criteria:
            try:
                global_repos = await engine.find(
                    Repository, relevance_criteria, limit=limit
                )

                for repo in global_repos:
                    # Skip repositories the user already has
                    user_repo_ids = [str(ur.repository_id) for ur in user_repos]
                    if str(repo.id) not in user_repo_ids:
                        repo_dict = repo.dict()
                        repo_dict["relevance_score"] = _calculate_relevance_score(
                            repo, user_languages, user_tags
                        )
                        relevant_repos.append(repo_dict)
            except Exception as e:
                logger.warning(f"Could not fetch global repositories: {e}")

        # Sort by relevance score
        relevant_repos.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return convert_objectids_to_strings(relevant_repos[:limit])

    except Exception as e:
        logger.error(f"Failed to get user relevant repositories: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get relevant repositories"
        )


def _calculate_relevance_score(
    repo: Repository, user_languages: set, user_tags: set
) -> float:
    """Calculate relevance score for a repository based on user preferences"""
    score = 0.0

    # Language match (high weight)
    if repo.primary_language and repo.primary_language in user_languages:
        score += 3.0

    # Tag matches (medium weight)
    if repo.tags:
        matching_tags = len(set(repo.tags) & user_tags)
        score += matching_tags * 1.5

    # Analysis count (popularity indicator)
    analysis_count = repo.get_analysis_count()
    if analysis_count > 0:
        score += min(analysis_count / 10.0, 2.0)  # Cap at 2.0

    # Unique users (community interest)
    unique_users = repo.get_unique_users()
    if unique_users > 0:
        score += min(unique_users / 5.0, 1.0)  # Cap at 1.0

    return score


@router.post("/user/add-repository", response_model=Dict[str, Any])
async def add_repository_to_user(
    repo_data: RepositoryCreateWithModel,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    force_reanalyze: bool = Query(
        False, description="Force re-analysis of existing repository"
    ),
):
    """Add a repository to the user's collection and optionally start analysis"""
    try:
        engine = cast(Any, await get_engine())
        repository_service, _, _, _ = get_services()

        # Check if repository already exists globally
        existing_repo = await engine.find_one(
            Repository, Repository.url == repo_data.url
        )

        if existing_repo:
            # Repository exists, just associate with user
            existing_user_repo = await engine.find_one(
                UserRepository,
                UserRepository.user_id == current_user.id,
                UserRepository.repository_id == existing_repo.id,
            )

            if existing_user_repo:
                # Already associated
                if not force_reanalyze:
                    repo_dict = existing_repo.dict()
                    repo_dict["access_type"] = existing_user_repo.access_type
                    return convert_objectids_to_strings(repo_dict)
                else:
                    # Force re-analysis
                    await repository_service.update_repository_status(
                        str(existing_repo.id), "analyzing"
                    )
                    background_tasks.add_task(
                        analyze_repository_background,
                        repo_data.url,
                        repo_data.branch or "main",
                        100,
                        20,
                        repo_data.model_id,
                    )
            else:
                # Create user association
                user_repo = UserRepository(  # type: ignore
                    user_id=current_user.id,
                    repository_id=existing_repo.id,
                    access_type="owner",
                )
                await engine.save(user_repo)

                # Update repository stats
                existing_repo.unique_users = int(existing_repo.unique_users or 0) + 1
                if force_reanalyze:
                    existing_repo.analysis_count = (
                        int(existing_repo.analysis_count or 0) + 1
                    )
                await engine.save(existing_repo)
        else:
            # Create new repository
            repo_name = repo_data.url.rstrip("/\n").split("/")[-1].replace(".git", "")

            repository = Repository(  # type: ignore
                url=repo_data.url,
                name=repo_name,
                default_branch=repo_data.branch or "main",
                is_public=not repo_data.is_private,
                created_by_user=current_user.id,
                tags=repo_data.tags,
                description=repo_data.description,
                unique_users=1,
                analysis_count=1,
            )

            await engine.save(repository)

            # Create user association
            user_repo = UserRepository(  # type: ignore
                user_id=current_user.id,
                repository_id=repository.id,
                access_type="owner",
            )
            await engine.save(user_repo)

            existing_repo = repository

            # Start analysis
            background_tasks.add_task(
                analyze_repository_background,
                repo_data.url,
                repo_data.branch or "main",
                100,
                20,
                repo_data.model_id,
            )

        # Get user's API keys for analysis
        user_api_keys = {}
        for provider in ["openai", "anthropic", "gemini"]:
            api_key = await get_user_api_key(str(current_user.id), provider)
            if api_key:
                user_api_keys[provider] = api_key

        # Store API keys in session or pass to background task somehow
        # This might need additional implementation based on your background task structure

        result = existing_repo.dict()
        result["user_api_keys_available"] = list(user_api_keys.keys())
        return convert_objectids_to_strings(result)

    except Exception as e:
        logger.error(f"Failed to add repository to user: {e}")
        raise HTTPException(status_code=500, detail="Failed to add repository to user")


@router.delete("/user/repositories/{repo_id}")
async def remove_repository_from_user(
    repo_id: str, current_user: User = Depends(get_current_user)
):
    """Remove repository association from current user"""
    try:
        engine = cast(Any, await get_engine())

        # Find user's association with the repository
        user_repo = await engine.find_one(
            UserRepository,
            UserRepository.user_id == current_user.id,
            UserRepository.repository_id == ObjectId(repo_id),
        )

        if not user_repo:
            raise HTTPException(
                status_code=404, detail="Repository not found in user's collection"
            )

        # Remove the association
        await engine.delete(user_repo)

        # Update repository stats
        try:
            repo = await engine.get(Repository, repo_id)
            if repo and repo.unique_users > 0:
                repo.unique_users = int(repo.unique_users or 0) - 1
                await engine.save(repo)
        except Exception as e:
            logger.warning(f"Could not update repository stats: {e}")

        return {"message": "Repository removed from user's collection"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove repository from user: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to remove repository from user"
        )


@router.get("/global", response_model=List[Dict[str, Any]])
async def get_global_repositories(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    language: Optional[str] = Query(None, description="Filter by primary language"),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get publicly available repositories (global repository table)"""
    try:
        engine = cast(Any, await get_engine())

        # Build query filters - handle missing fields gracefully
        filters = []
        # For is_public, check both None (missing field) and True values
        # This allows old repositories (None) and new public repositories (True)
        filters.append((Repository.is_public == True) | (Repository.is_public == None))
        if tag:
            # Only filter by tags if the field exists and contains the tag
            filters.append(cast(Any, Repository.tags).contains(tag))  # type: ignore[attr-defined]
        if language:
            filters.append(Repository.primary_language == language)

        # Get repositories with pagination
        repositories = await engine.find(
            Repository,
            *filters,
            limit=limit,
            skip=offset,
            sort=cast(Any, Repository.analysis_count).desc(),  # type: ignore[attr-defined]
        )

        # Convert to dict and add user association info if user is logged in
        result = []
        for repo in repositories:
            repo_dict = repo.dict()

            if current_user:
                # Check if user already has this repository
                user_repo = await engine.find_one(
                    UserRepository,
                    UserRepository.user_id == current_user.id,
                    UserRepository.repository_id == repo.id,
                )
                repo_dict["user_has_repository"] = user_repo is not None
                repo_dict["user_access_type"] = (
                    user_repo.access_type if user_repo else None
                )
            else:
                repo_dict["user_has_repository"] = False
                repo_dict["user_access_type"] = None

            result.append(repo_dict)

        return convert_objectids_to_strings(result)

    except Exception as e:
        logger.error(f"Failed to get global repositories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get global repositories")


@router.get("/global/popular", response_model=List[Dict[str, Any]])
async def get_popular_repositories(limit: int = Query(10, ge=1, le=50)):
    """Get most popular repositories (most analyzed)"""
    try:
        engine = cast(Any, await get_engine())

        repositories = await engine.find(
            Repository,
            # Handle both None (old repos) and True (new public repos)
            (Repository.is_public == True) | (Repository.is_public == None),
            limit=limit,
            # Sort by analysis_count, treating None as 0
            sort=cast(Any, Repository.analysis_count).desc(),  # type: ignore[attr-defined]
        )

        return convert_objectids_to_strings([repo.dict() for repo in repositories])

    except Exception as e:
        logger.error(f"Failed to get popular repositories: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get popular repositories"
        )


@router.get("/global/recent", response_model=List[Dict[str, Any]])
async def get_recent_repositories(limit: int = Query(10, ge=1, le=50)):
    """Get recently added repositories"""
    try:
        engine = cast(Any, await get_engine())

        repositories = await engine.find(
            Repository,
            # Handle both None (old repos) and True (new public repos)
            (Repository.is_public == True) | (Repository.is_public == None),
            limit=limit,
            sort=cast(Any, Repository.created_at).desc(),  # type: ignore[attr-defined]
        )

        return convert_objectids_to_strings([repo.dict() for repo in repositories])

    except Exception as e:
        logger.error(f"Failed to get recent repositories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent repositories")
