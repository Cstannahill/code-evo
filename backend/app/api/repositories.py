from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.repository import (
    Repository,
    Commit,
    Technology,
    Pattern,
    PatternOccurrence,
    AnalysisSession,
    FileChange,
)
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryResponse,
    TimelineResponse,
)
from app.services.analysis_service import AnalysisService
from app.tasks.analysis_tasks import analyze_repository_background
from app.schemas.repository import RepositoryCreate
from pydantic import BaseModel

logger = logging.getLogger(__name__)


analysis_service = AnalysisService()
router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


class RepositoryCreateWithModel(BaseModel):
    url: str
    branch: str = "main"
    model_id: Optional[str] = None


def _get_complexity_distribution(patterns: List[Pattern]) -> Dict[str, int]:
    distribution = {"simple": 0, "intermediate": 0, "advanced": 0}
    for p in patterns:
        lvl = p.complexity_level or "intermediate"
        if lvl in distribution:
            distribution[lvl] += 1
    return distribution


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(db: Session = Depends(get_db)):
    return db.query(Repository).all()


@router.post("/", response_model=RepositoryResponse)
async def create_repository(
    repo_data: RepositoryCreateWithModel,
    background_tasks: BackgroundTasks,
    force_reanalyze: bool = Query(
        False, description="Force re-analysis of existing repository"
    ),
    db: Session = Depends(get_db),
):
    existing = db.query(Repository).filter(Repository.url == repo_data.url).first()
    if existing:
        if not force_reanalyze and existing.status == "completed":
            return existing
        # reset and reanalyze
        existing.status = "analyzing"
        existing.last_analyzed = datetime.utcnow()
        db.commit()
        background_tasks.add_task(
            analyze_repository_background,
            repo_data.url,
            repo_data.branch or "main",
            100,  # commit_limit
            20,  # candidate_limit
            repo_data.model_id,  # Pass model_id to analysis
        )
        return existing

    repo = Repository(
        url=repo_data.url,
        name=repo_data.url.rstrip("/\n").split("/")[-1].replace(".git", ""),
        default_branch=repo_data.branch or "main",
        status="analyzing",
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    # Start background analysis - FIXED: Now passing model_id here too
    background_tasks.add_task(
        analyze_repository_background,
        repo_data.url,
        repo_data.branch or "main",
        100,  # commit_limit
        20,  # candidate_limit
        repo_data.model_id,  # Pass model_id to analysis
    )
    return repo


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/analysis", response_model=Dict[str, Any])
async def get_repository_analysis(repo_id: str, db: Session = Depends(get_db)):
    """
    Get complete repository analysis data including:
    - Repository info and status
    - Analysis session details
    - Technologies organized by category
    - Pattern occurrences and statistics
    - AI-generated insights
    - Timeline data
    """
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get the latest analysis session
    analysis_session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.repository_id == repo_id)
        .order_by(AnalysisSession.started_at.desc())
        .first()
    )

    # Get all technologies for this repository
    technologies_query = (
        db.query(Technology).filter(Technology.repository_id == repo_id).all()
    )
    all_patterns_count = db.query(Pattern).count()
    repo_patterns_count = (
        db.query(PatternOccurrence)
        .filter(PatternOccurrence.repository_id == repo_id)
        .count()
    )

    logger.info(f"📊 Debug - Total patterns in DB: {all_patterns_count}")
    logger.info(f"📊 Debug - Patterns for this repo: {repo_patterns_count}")

    # Get all patterns and their occurrences
    pattern_occurrences_query = (
        db.query(PatternOccurrence)
        .join(Pattern)
        .filter(PatternOccurrence.repository_id == repo_id)
        .all()
    )

    logger.info(
        f"📊 Debug - Pattern occurrences found: {len(pattern_occurrences_query)}"
    )
    # ---
    # Organize technologies by category
    technologies = {
        "language": [],
        "framework": [],
        "library": [],
        "tool": [],
        "database": [],
        "platform": [],
        "other": [],
    }

    for tech in technologies_query:
        # Map the category correctly
        category_map = {
            "languages": "language",
            "frameworks": "framework",
            "libraries": "library",
            "tools": "tool",
            "databases": "database",
            "platforms": "platform",
        }

        tech_category = tech.category.lower() if tech.category else "other"
        mapped_category = category_map.get(tech_category, tech_category)

        if mapped_category not in technologies:
            mapped_category = "other"

        technologies[mapped_category].append(
            {
                "id": tech.id,
                "name": tech.name,
                "category": tech.category,
                "first_seen": tech.first_seen.isoformat() if tech.first_seen else None,
                "last_seen": tech.last_seen.isoformat() if tech.last_seen else None,
                "usage_count": tech.usage_count,
                "version": tech.version,
                "metadata": tech.tech_metadata or {},
            }
        )
    # ----
    # Get all patterns and their occurrences
    pattern_occurrences_query = (
        db.query(PatternOccurrence)
        .join(Pattern)
        .filter(PatternOccurrence.repository_id == repo_id)
        .all()
    )

    patterns = []
    pattern_stats = {}

    for occurrence in pattern_occurrences_query:
        # Add to patterns array
        patterns.append(
            {
                "pattern_name": occurrence.pattern.name,
                "file_path": occurrence.file_path,
                "code_snippet": occurrence.code_snippet,
                "confidence_score": occurrence.confidence_score,
                "detected_at": occurrence.detected_at.isoformat(),
                "line_number": occurrence.line_number,
            }
        )

        # Build pattern statistics
        pattern_name = occurrence.pattern.name
        if pattern_name not in pattern_stats:
            pattern_stats[pattern_name] = {
                "name": pattern_name,
                "category": occurrence.pattern.category,
                "occurrences": 0,
                "complexity_level": occurrence.pattern.complexity_level,
                "is_antipattern": occurrence.pattern.is_antipattern,
                "description": occurrence.pattern.description,
            }
        pattern_stats[pattern_name]["occurrences"] += 1

    # Build pattern timeline
    timeline_data = {}
    for occurrence in pattern_occurrences_query:
        month = occurrence.detected_at.strftime("%Y-%m")
        if month not in timeline_data:
            timeline_data[month] = {}

        pattern_name = occurrence.pattern.name
        timeline_data[month][pattern_name] = (
            timeline_data[month].get(pattern_name, 0) + 1
        )

    timeline = [
        {"date": month, "patterns": patterns_dict}
        for month, patterns_dict in sorted(timeline_data.items())
    ]

    # Generate AI insights if available
    status = analysis_service.get_status()
    ai_ok = status.get("ollama_available", False)
    ai_insights = []

    if ai_ok:
        try:
            insight_data = {
                "patterns": pattern_stats,
                "technologies": [
                    t["name"] for tech_list in technologies.values() for t in tech_list
                ],
                "commits": repo.total_commits,
            }
            ai_insights = await analysis_service.generate_insights(insight_data)
        except Exception as e:
            logger.warning(f"Failed to generate AI insights: {e}")

    # Basic insight
    basic_insight = {
        "type": "info",
        "title": "Repository Overview",
        "description": f"Analyzed {repo.total_commits} commits with {len(pattern_stats)} patterns detected.",
        "data": {
            "repository_id": repo_id,
            "patterns": pattern_stats,
            "total_commits": repo.total_commits,
            "technologies": [
                t["name"] for tech_list in technologies.values() for t in tech_list
            ],
        },
    }

    # Calculate summary statistics
    unique_patterns = list(
        db.query(Pattern)
        .join(PatternOccurrence)
        .filter(PatternOccurrence.repository_id == repo_id)
        .distinct()
        .all()
    )
    antipatterns_count = sum(1 for p in unique_patterns if p.is_antipattern)

    return {
        "repository_id": repo_id,
        "status": repo.status,
        "analysis_session": (
            {
                "id": analysis_session.id if analysis_session else None,
                "status": analysis_session.status if analysis_session else "unknown",
                "commits_analyzed": (
                    analysis_session.commits_analyzed
                    if analysis_session
                    else repo.total_commits
                ),
                "patterns_found": (
                    analysis_session.patterns_found
                    if analysis_session
                    else len(pattern_stats)
                ),
                "started_at": (
                    analysis_session.started_at.isoformat()
                    if analysis_session and analysis_session.started_at
                    else None
                ),
                "completed_at": (
                    analysis_session.completed_at.isoformat()
                    if analysis_session and analysis_session.completed_at
                    else None
                ),
                "configuration": (
                    analysis_session.configuration if analysis_session else {}
                ),
                "error_message": (
                    analysis_session.error_message if analysis_session else None
                ),
            }
            if analysis_session
            else {
                "id": None,
                "status": "unknown",
                "commits_analyzed": repo.total_commits,
                "patterns_found": len(pattern_stats),
                "started_at": None,
                "completed_at": None,
                "configuration": {},
                "error_message": None,
            }
        ),
        "technologies": technologies,
        "patterns": patterns,
        "pattern_timeline": {
            "timeline": timeline,
            "summary": {
                "total_months": len(timeline),
                "patterns_tracked": list(pattern_stats.keys()),
            },
        },
        "pattern_statistics": pattern_stats,
        "insights": [basic_insight] + ai_insights,
        "ai_powered": ai_ok,
        "summary": {
            "total_patterns": len(pattern_stats),
            "antipatterns_detected": antipatterns_count,
            "complexity_distribution": _get_complexity_distribution(unique_patterns),
        },
    }


@router.get("/{repo_id}/timeline", response_model=TimelineResponse)
async def get_repository_timeline(repo_id: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    commits = (
        db.query(Commit)
        .filter(Commit.repository_id == repo_id)
        .order_by(Commit.committed_date)
        .all()
    )

    # build timeline
    months = {}
    for c in commits:
        m = c.committed_date.strftime("%Y-%m")
        if m not in months:
            months[m] = {
                "date": m,
                "commits": 0,
                "languages": set(),
                "technologies": set(),
                "patterns": {},
            }
        months[m]["commits"] += 1

        # Get file changes for this commit to extract languages
        file_changes = db.query(FileChange).filter(FileChange.commit_id == c.id).all()
        for fc in file_changes:
            if fc.language:
                months[m]["languages"].add(fc.language)

        # Get technologies active during this time
        techs = (
            db.query(Technology)
            .filter(
                Technology.repository_id == repo_id,
                Technology.first_seen <= c.committed_date,
                Technology.last_seen >= c.committed_date,
            )
            .all()
        )
        for t in techs:
            months[m]["technologies"].add(f"{t.name} ({t.category})")

        # Get pattern occurrences for this commit
        pattern_occurrences = (
            db.query(PatternOccurrence)
            .join(Pattern)
            .filter(PatternOccurrence.commit_id == c.id)
            .all()
        )
        for po in pattern_occurrences:
            name = po.pattern.name
            months[m]["patterns"][name] = months[m]["patterns"].get(name, 0) + 1

    timeline = [
        {
            "date": v["date"],
            "commits": v["commits"],
            "languages": sorted(v["languages"]),
            "technologies": sorted(v["technologies"]),
            "patterns": v["patterns"],
        }
        for v in months.values()
    ]

    return {
        "repository_id": repo_id,
        "timeline": timeline,
        "summary": {
            "total_months": len(timeline),
            "total_commits": sum(t["commits"] for t in timeline),
            "languages": list({lang for t in timeline for lang in t["languages"]}),
            "technologies": list(
                {tech for t in timeline for tech in t["technologies"]}
            ),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
