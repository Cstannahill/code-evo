# app/api/repositories.py - Fixed version with working AI integration
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
import asyncio
from datetime import datetime

from app.core.database import get_db, SessionLocal
from app.models.repository import (
    Repository,
    AnalysisSession,
    User,
    Commit,
    FileChange,
    Technology,
    Pattern,
    PatternOccurrence,
    Insight,
)
from app.services.git_service import GitService
from app.services.ai_service import AIService
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryResponse,
    AnalysisResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/repositories", response_model=RepositoryResponse)
async def create_repository(
    repo_data: RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create and analyze a new repository"""
    try:
        # Check if repository already exists
        existing_repo = (
            db.query(Repository).filter(Repository.url == repo_data.url).first()
        )
        if existing_repo:
            return RepositoryResponse(
                id=str(existing_repo.id),
                url=existing_repo.url,
                name=existing_repo.name,
                status=existing_repo.status,
                total_commits=existing_repo.total_commits,
                created_at=existing_repo.created_at,
            )

        # Create repository record
        db_repo = Repository(
            url=repo_data.url,
            name=repo_data.url.split("/")[-1].replace(".git", ""),
            default_branch=repo_data.branch or "main",
            status="pending",
            repo_metadata={},
        )

        db.add(db_repo)
        db.commit()
        db.refresh(db_repo)

        # Start background analysis - FIXED
        background_tasks.add_task(
            analyze_repository_background,
            str(db_repo.id),
            repo_data.url,
            repo_data.branch or "main",
        )

        return RepositoryResponse(
            id=str(db_repo.id),
            url=db_repo.url,
            name=db_repo.name,
            status=db_repo.status,
            total_commits=0,
            created_at=db_repo.created_at,
        )

    except Exception as e:
        logger.error(f"Error creating repository: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/repositories/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str, db: Session = Depends(get_db)):
    """Get repository details"""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    return RepositoryResponse(
        id=str(repo.id),
        url=repo.url,
        name=repo.name,
        status=repo.status,
        total_commits=repo.total_commits,
        first_commit_date=repo.first_commit_date,
        last_commit_date=repo.last_commit_date,
        last_analyzed=repo.last_analyzed,
        created_at=repo.created_at,
    )


@router.get("/repositories")
async def list_repositories(db: Session = Depends(get_db)):
    """List all repositories"""
    repos = db.query(Repository).all()
    return [
        RepositoryResponse(
            id=str(repo.id),
            url=repo.url,
            name=repo.name,
            status=repo.status,
            total_commits=repo.total_commits,
            created_at=repo.created_at,
        )
        for repo in repos
    ]


@router.get("/repositories/{repo_id}/analysis")
async def get_repository_analysis(repo_id: str, db: Session = Depends(get_db)):
    """Get repository analysis results"""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get latest analysis session
    analysis_session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.repository_id == repo_id)
        .order_by(AnalysisSession.started_at.desc())
        .first()
    )

    if not analysis_session:
        return {
            "repository_id": repo_id,
            "status": repo.status,
            "analysis_session": None,
            "technologies": {},
            "patterns": [],
            "insights": [],
        }

    # Get technologies
    technologies = {}
    for tech in repo.technologies:
        if tech.category not in technologies:
            technologies[tech.category] = []
        technologies[tech.category].append(
            {
                "name": tech.name,
                "first_seen": tech.first_seen.isoformat() if tech.first_seen else None,
                "usage_count": tech.usage_count,
            }
        )

    # Get patterns - FIXED to actually return patterns
    patterns = []
    pattern_occurrences = (
        db.query(PatternOccurrence)
        .filter(PatternOccurrence.repository_id == repo_id)
        .limit(50)
        .all()
    )

    for occurrence in pattern_occurrences:
        patterns.append(
            {
                "pattern_name": occurrence.pattern.name,
                "file_path": occurrence.file_path,
                "confidence_score": occurrence.confidence_score,
                "detected_at": occurrence.detected_at.isoformat(),
            }
        )

    return {
        "repository_id": repo_id,
        "status": repo.status,
        "analysis_session": {
            "id": str(analysis_session.id),
            "status": analysis_session.status,
            "commits_analyzed": analysis_session.commits_analyzed,
            "patterns_found": analysis_session.patterns_found,
            "started_at": analysis_session.started_at.isoformat(),
            "completed_at": (
                analysis_session.completed_at.isoformat()
                if analysis_session.completed_at
                else None
            ),
        },
        "technologies": technologies,
        "patterns": patterns,  # Now returns actual patterns
        "insights": (
            [
                {
                    "type": insight.type,
                    "title": insight.title,
                    "description": insight.description,
                    "data": insight.data,
                }
                for insight in analysis_session.insights
            ]
            if analysis_session.insights
            else []
        ),
    }


@router.get("/repositories/{repo_id}/timeline")
async def get_technology_timeline(repo_id: str, db: Session = Depends(get_db)):
    """Get technology adoption timeline"""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get commits ordered by date
    commits = (
        db.query(Commit)
        .filter(Commit.repository_id == repo_id)
        .order_by(Commit.committed_date)
        .all()
    )

    # Build timeline
    timeline = {}
    for commit in commits:
        month_key = commit.committed_date.strftime("%Y-%m")
        if month_key not in timeline:
            timeline[month_key] = {
                "date": month_key,
                "commits": 0,
                "languages": set(),
                "technologies": set(),
            }

        timeline[month_key]["commits"] += 1

        # Add languages from file changes
        for file_change in commit.file_changes:
            if file_change.language and file_change.language != "Other":
                timeline[month_key]["languages"].add(file_change.language)

    # Convert sets to lists and sort timeline
    timeline_list = []
    for month_data in sorted(timeline.values(), key=lambda x: x["date"]):
        month_data["languages"] = list(month_data["languages"])
        month_data["technologies"] = list(month_data["technologies"])
        timeline_list.append(month_data)

    return {"repository_id": repo_id, "timeline": timeline_list}


def analyze_repository_background(repo_id: str, repo_url: str, branch: str):
    """Background task to analyze repository with AI pattern detection"""
    git_service = GitService()

    # Get database session
    db = SessionLocal()

    try:
        # Update repository status
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            logger.error(f"Repository {repo_id} not found")
            return

        repo.status = "analyzing"
        db.commit()

        # Create analysis session
        analysis_session = AnalysisSession(
            repository_id=repo_id,
            user_id=repo.user_id if repo.user_id else None,
            status="running",
            configuration={
                "branch": branch,
                "max_commits": 100,
            },
        )
        db.add(analysis_session)
        db.commit()
        db.refresh(analysis_session)

        logger.info(f"Starting analysis for repository {repo_url}")

        # Clone and analyze repository
        git_repo = git_service.clone_repository(repo_url, branch)

        # Get repository info
        repo_info = git_service.get_repository_info(git_repo)
        repo.total_commits = repo_info["total_commits"]
        repo.first_commit_date = repo_info["first_commit_date"]
        repo.last_commit_date = repo_info["last_commit_date"]

        # Get commit history (limited for faster processing)
        commits = git_service.get_commit_history(git_repo, limit=50)
        analysis_session.commits_analyzed = len(commits)

        logger.info(f"Analyzing {len(commits)} commits...")

        # Store commits in database
        stored_commits = []
        for commit_data in commits:
            # Check if commit already exists
            existing_commit = (
                db.query(Commit)
                .filter(Commit.commit_hash == commit_data["hash"])
                .first()
            )
            if existing_commit:
                stored_commits.append(existing_commit)
                continue

            db_commit = Commit(
                repository_id=repo_id,
                commit_hash=commit_data["hash"],
                author_name=commit_data["author_name"],
                author_email=commit_data["author_email"],
                committed_date=commit_data["committed_date"],
                message=commit_data["message"],
                files_changed_count=len(commit_data["files_changed"]),
                additions=commit_data["stats"]["total_insertions"],
                deletions=commit_data["stats"]["total_deletions"],
            )
            db.add(db_commit)
            db.commit()
            db.refresh(db_commit)
            stored_commits.append(db_commit)

            # Store file changes (limited to avoid too much data)
            for file_change in commit_data["files_changed"][:10]:
                db_file_change = FileChange(
                    commit_id=db_commit.id,
                    file_path=file_change["file_path"],
                    old_path=file_change.get("old_path"),
                    change_type=file_change["change_type"],
                    language=file_change["language"],
                    additions=file_change["additions"],
                    deletions=file_change["deletions"],
                    patch=file_change.get("patch", "")[:5000],  # Limit patch size
                )
                db.add(db_file_change)

        db.commit()

        # AI PATTERN DETECTION - FIXED
        patterns_detected = 0
        ai_service = AIService()

        if ai_service.ollama_available:
            logger.info("🤖 Running AI pattern analysis on code snippets...")

            # Async wrapper function to run AI analysis
            async def run_ai_analysis():
                nonlocal patterns_detected

                # Get code snippets from commits for AI analysis
                code_snippets = []
                for commit_data in commits[:10]:  # Analyze first 10 commits
                    for file_change in commit_data["files_changed"]:
                        if (
                            file_change.get("content")
                            and len(file_change["content"]) > 50
                            and file_change["language"]
                            in ["JavaScript", "TypeScript", "React", "Python"]
                        ):
                            code_snippets.append(
                                {
                                    "code": file_change["content"][:2000],
                                    "language": file_change["language"],
                                    "file_path": file_change["file_path"],
                                    "commit_hash": commit_data["hash"],
                                }
                            )

                # Run AI analysis on code snippets
                for snippet in code_snippets[:5]:  # Analyze 5 snippets max
                    try:
                        pattern_result = await ai_service.analyze_code_pattern(
                            snippet["code"], snippet["language"]
                        )

                        # Store detected patterns in database
                        detected_patterns = pattern_result.get("combined_patterns", [])
                        for pattern_name in detected_patterns:
                            # Create pattern if it doesn't exist
                            pattern = (
                                db.query(Pattern)
                                .filter(Pattern.name == pattern_name)
                                .first()
                            )
                            if not pattern:
                                pattern = Pattern(
                                    name=pattern_name,
                                    category="detected",
                                    description=f"Auto-detected pattern: {pattern_name}",
                                    complexity_level="intermediate",
                                )
                                db.add(pattern)
                                db.commit()
                                db.refresh(pattern)

                            # Find the commit in database
                            db_commit_for_pattern = (
                                db.query(Commit)
                                .filter(Commit.commit_hash == snippet["commit_hash"])
                                .first()
                            )

                            if db_commit_for_pattern:
                                # Check if pattern occurrence already exists
                                existing_occurrence = (
                                    db.query(PatternOccurrence)
                                    .filter(
                                        PatternOccurrence.pattern_id == pattern.id,
                                        PatternOccurrence.commit_id
                                        == db_commit_for_pattern.id,
                                        PatternOccurrence.file_path
                                        == snippet["file_path"],
                                    )
                                    .first()
                                )

                                if not existing_occurrence:
                                    # Create pattern occurrence
                                    occurrence = PatternOccurrence(
                                        pattern_id=pattern.id,
                                        repository_id=repo_id,
                                        commit_id=db_commit_for_pattern.id,
                                        file_path=snippet["file_path"],
                                        code_snippet=snippet["code"][:500],
                                        confidence_score=0.8,
                                    )
                                    db.add(occurrence)
                                    patterns_detected += 1

                        logger.info(
                            f"🔍 Found {len(detected_patterns)} patterns in {snippet['file_path']}"
                        )

                    except Exception as e:
                        logger.warning(f"Pattern analysis failed for snippet: {e}")

                db.commit()
                logger.info(f"🎯 Total patterns detected: {patterns_detected}")

            # Run the async analysis in the background thread
            try:
                asyncio.run(run_ai_analysis())
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")

        else:
            logger.info("⚠️  AI not available - skipping pattern detection")

        # Update analysis session with patterns found
        analysis_session.patterns_found = patterns_detected

        # Extract technologies
        technologies = git_service.extract_technologies(git_repo)

        # Store technologies
        for category, tech_list in technologies.items():
            if category == "languages":
                for lang_name, count in tech_list.items():
                    # Check if technology already exists
                    existing_tech = (
                        db.query(Technology)
                        .filter(
                            Technology.repository_id == repo_id,
                            Technology.name == lang_name,
                        )
                        .first()
                    )
                    if existing_tech:
                        continue

                    db_tech = Technology(
                        repository_id=repo_id,
                        name=lang_name,
                        category="language",
                        first_seen=repo.first_commit_date,
                        last_seen=repo.last_commit_date,
                        usage_count=count,
                        tech_metadata={},
                    )
                    db.add(db_tech)
            else:
                for tech_name in tech_list:
                    # Check if technology already exists
                    existing_tech = (
                        db.query(Technology)
                        .filter(
                            Technology.repository_id == repo_id,
                            Technology.name == tech_name,
                        )
                        .first()
                    )
                    if existing_tech:
                        continue

                    db_tech = Technology(
                        repository_id=repo_id,
                        name=tech_name,
                        category=category.rstrip("s"),  # Remove plural 's'
                        first_seen=repo.first_commit_date,
                        last_seen=repo.last_commit_date,
                        usage_count=1,
                        tech_metadata={},
                    )
                    db.add(db_tech)

        db.commit()

        # Create comprehensive insight
        insight = Insight(
            analysis_session_id=analysis_session.id,
            repository_id=repo_id,
            type="info",
            title="Repository Analysis Complete",
            description=f'Successfully analyzed {len(commits)} commits, detected {len(technologies.get("languages", {}))} programming languages, and found {patterns_detected} code patterns.',
            data={
                "technologies": technologies,
                "patterns_detected": patterns_detected,
                "commits_analyzed": len(commits),
            },
        )
        db.add(insight)

        # Complete analysis
        analysis_session.status = "completed"
        analysis_session.completed_at = datetime.utcnow()
        repo.status = "completed"
        repo.last_analyzed = datetime.utcnow()

        db.commit()

        logger.info(
            f"✅ Analysis completed for repository {repo_url} - {patterns_detected} patterns detected"
        )

    except Exception as e:
        logger.error(f"❌ Error analyzing repository {repo_url}: {e}")

        # Update status to failed
        if "analysis_session" in locals():
            analysis_session.status = "failed"
            analysis_session.error_message = str(e)
            analysis_session.completed_at = datetime.utcnow()

        if "repo" in locals():
            repo.status = "failed"

        db.commit()

    finally:
        db.close()
        git_service.cleanup()
