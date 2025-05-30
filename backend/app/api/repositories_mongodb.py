# app/api/repositories_mongodb.py - MongoDB-based Repository API
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

# MongoDB imports
from app.services.repository_service import RepositoryService
from app.services.pattern_service import PatternService
from app.services.ai_analysis_service import AIAnalysisService
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryResponse,
    TimelineResponse,
)
from app.services.analysis_service import AnalysisService
from app.tasks.analysis_tasks import analyze_repository_background
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Initialize MongoDB services
repository_service = RepositoryService()
pattern_service = PatternService()
ai_analysis_service = AIAnalysisService()
analysis_service = AnalysisService()
router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


class RepositoryCreateWithModel(BaseModel):
    url: str
    branch: str = "main"
    model_id: Optional[str] = None


@router.get("/", response_model=List[Dict[str, Any]])
async def list_repositories():
    """List all repositories with MongoDB backend"""
    try:
        result = await repository_service.list_repositories()
        return result.get("repositories", [])
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        raise HTTPException(status_code=500, detail="Failed to list repositories")


@router.post("/", response_model=Dict[str, Any])
async def create_repository(
    repo_data: RepositoryCreateWithModel,
    background_tasks: BackgroundTasks,
    force_reanalyze: bool = Query(
        False, description="Force re-analysis of existing repository"
    ),
):
    """Create repository with MongoDB backend"""
    try:
        # Check if repository already exists
        existing_repos = await repository_service.list_repositories()
        existing = None
        for repo in existing_repos.get("repositories", []):
            if repo.get("url") == repo_data.url:
                existing = repo
                break

        if existing:
            if not force_reanalyze and existing.get("status") == "completed":
                return existing
            # Reset and reanalyze
            await repository_service.update_repository_status(
                existing["id"], "analyzing"
            )
            background_tasks.add_task(
                analyze_repository_background,
                repo_data.url,
                repo_data.branch or "main",
                100,  # commit_limit
                20,  # candidate_limit
                repo_data.model_id,
            )
            return existing

        # Create new repository
        repo_name = repo_data.url.rstrip("/\n").split("/")[-1].replace(".git", "")
        repository = await repository_service.create_repository(
            url=repo_data.url, name=repo_name, branch=repo_data.branch or "main"
        )

        # Start background analysis
        background_tasks.add_task(
            analyze_repository_background,
            repo_data.url,
            repo_data.branch or "main",
            100,  # commit_limit
            20,  # candidate_limit
            repo_data.model_id,
        )

        return repository.dict()

    except Exception as e:
        logger.error(f"Failed to create repository: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create repository: {str(e)}"
        )


@router.get("/{repo_id}", response_model=Dict[str, Any])
async def get_repository(repo_id: str):
    """Get repository by ID with MongoDB backend"""
    try:
        repository = await repository_service.get_repository(repo_id)
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")
        return repository.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repository {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get repository")


@router.get("/{repo_id}/analysis", response_model=Dict[str, Any])
async def get_repository_analysis(repo_id: str):
    """
    Get complete repository analysis data with MongoDB backend including:
    - Repository info and status
    - Analysis session details
    - Technologies organized by category
    - Pattern occurrences and statistics
    - AI-generated insights
    - Timeline data
    """
    try:
        # Get comprehensive analysis from repository service
        analysis = await repository_service.get_repository_analysis(repo_id)

        # Get pattern statistics from pattern service
        pattern_stats = await pattern_service.get_repository_patterns_statistics(
            repo_id
        )

        # Get pattern timeline
        pattern_timeline = await pattern_service.get_pattern_timeline(repo_id)

        # Generate AI insights if available
        status = analysis_service.get_status()
        ai_ok = status.get("ollama_available", False)
        ai_insights = []

        if ai_ok:
            try:
                insight_data = {
                    "patterns": pattern_stats,
                    "technologies": [
                        tech["name"] for tech in analysis.get("technologies", [])
                    ],
                    "commits": analysis.get("commits_summary", {}).get(
                        "total_commits", 0
                    ),
                }
                ai_insights = await analysis_service.generate_insights(insight_data)
            except Exception as e:
                logger.warning(f"Failed to generate AI insights: {e}")

        # Build comprehensive response
        return {
            "repository_id": repo_id,
            "repository": analysis.get("repository", {}),
            "status": analysis.get("repository", {}).get("status", "unknown"),
            "analysis_sessions": analysis.get("analysis_sessions", []),
            "technologies": _organize_technologies_by_category(
                analysis.get("technologies", [])
            ),
            "patterns": analysis.get("patterns", []),
            "pattern_timeline": {
                "timeline": pattern_timeline,
                "summary": {
                    "total_months": len(pattern_timeline),
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
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get repository analysis for {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get repository analysis")


@router.get("/{repo_id}/timeline", response_model=Dict[str, Any])
async def get_repository_timeline(repo_id: str):
    """Get repository timeline with MongoDB backend"""
    try:
        # Get repository to verify it exists
        repository = await repository_service.get_repository(repo_id)
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")

        # Get pattern timeline
        timeline_data = await pattern_service.get_pattern_timeline(repo_id)

        # Get commits summary for additional timeline context
        analysis = await repository_service.get_repository_analysis(repo_id)
        commits_summary = analysis.get("commits_summary", {})

        return {
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repository timeline for {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get repository timeline")


def _organize_technologies_by_category(
    technologies: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Organize technologies by category"""
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

        # Map category names
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
