from fastapi import APIRouter, HTTPException, Depends, Query
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
)
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryResponse,
    TimelineResponse,
)
from app.services.git_service import GitService
from app.services.ai_service import AIService
from app.tasks.analysis_tasks import analyze_repository_background

logger = logging.getLogger(__name__)

# Use AIService directly for insights
ai_service = AIService()
router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


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
    repo_data: RepositoryCreate,
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
        existing.status = "pending"
        existing.last_analyzed = datetime.utcnow()
        db.commit()
        analyze_repository_background(
            str(existing.id), repo_data.branch, repo_data.max_commits or 100
        )
        return existing

    repo = Repository(
        url=repo_data.url,
        name=repo_data.url.rstrip("/\n").split("/")[-1],
        branch=repo_data.branch,
        status="pending",
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    analyze_repository_background(
        str(repo.id), repo_data.branch, repo_data.max_commits or 100
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
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # gather pattern stats
    patterns = (
        db.query(Pattern)
        .join(PatternOccurrence)
        .filter(PatternOccurrence.repository_id == repo_id)
        .distinct()
        .all()
    )
    pattern_stats: Dict[str, Any] = {}
    for p in patterns:
        count = (
            db.query(PatternOccurrence)
            .filter(
                PatternOccurrence.pattern_id == p.id,
                PatternOccurrence.repository_id == repo_id,
            )
            .count()
        )
        pattern_stats[p.name] = {
            "category": p.category,
            "occurrences": count,
            "complexity_level": p.complexity_level,
            "is_antipattern": p.is_antipattern,
        }

    basic_insight = {
        "type": "info",
        "title": "Repository Overview",
        "description": f"Analyzed {repo.total_commits} commits with {len(pattern_stats)} patterns detected.",
        "data": {
            "repository_id": repo_id,
            "patterns": pattern_stats,
            "total_commits": repo.total_commits,
            "technologies": [t.name for t in repo.technologies],
        },
    }

    # AI Insights
    status = ai_service.get_status()
    ai_ok = status.get("ollama_available", False)
    ai_insights: List[Dict[str, Any]] = []
    if ai_ok:
        data = {
            "patterns": pattern_stats,
            "technologies": [t.name for t in repo.technologies],
            "commits": repo.total_commits,
        }
        ai_insights = await ai_service.generate_insights(data)

    return {
        "repository_id": repo_id,
        "pattern_timeline": {"timeline": [], "summary": {}},
        "pattern_statistics": pattern_stats,
        "insights": [basic_insight] + ai_insights,
        "ai_powered": ai_ok,
        "summary": {
            "total_patterns": len(pattern_stats),
            "antipatterns_detected": sum(1 for p in patterns if p.is_antipattern),
            "complexity_distribution": _get_complexity_distribution(patterns),
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
    months: Dict[str, Dict[str, Any]] = {}
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
        for fc in c.file_changes:
            if fc.language:
                months[m]["languages"].add(fc.language)
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
        for po in c.pattern_occurrences:
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
