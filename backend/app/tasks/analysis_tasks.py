# backend/app/tasks/analysis_tasks.py

import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.services.analysis_service import AnalysisService
from app.models.repository import (
    Repository,
    AnalysisSession,
    Technology,
    Pattern,
    PatternOccurrence,
    Commit,
    FileChange,
)

logger = logging.getLogger(__name__)


async def analyze_repository_background(
    repo_url: str,
    branch: str,
    commit_limit: int,
    candidate_limit: int,
    model_id: Optional[str] = None,  # Add model parameter
):
    """Background task with model selection support"""

    db = None
    analysis_session = None
    repo = None
    try:
        # Use dependency-injected DB session
        db = next(get_db())

        # Initialize analysis service
        analysis_service = AnalysisService()

        # Use specific model if provided
        if model_id:
            logger.info(f"🤖 Using selected model: {model_id}")
            analysis_service.set_preferred_model(model_id)

        # Find the repository
        repo = db.query(Repository).filter(Repository.url == repo_url).first()
        if not repo:
            logger.error(f"❌ Repository not found: {repo_url}")
            return

        logger.info(f"🚀 Starting background analysis for {repo.name}")

        # Create analysis session
        analysis_session = AnalysisSession(
            repository_id=repo.id,
            status="running",
            commits_analyzed=0,
            patterns_found=0,
            started_at=datetime.utcnow(),
            configuration={
                "commit_limit": commit_limit,
                "candidate_limit": candidate_limit,
                "branch": branch,
            },
        )
        db.add(analysis_session)
        db.commit()
        db.refresh(analysis_session)
        logger.info(f"📊 Analysis session created: {analysis_session.id}")

        # Check for cancellation before running analysis
        try:
            logger.info(f"🔍 Cloning repository {repo_url}...")
            logger.info(f"🤖 Running AI analysis with {commit_limit} commits limit...")

            # FIXED: Directly await the async method instead of creating new event loop
            result = await analysis_service.analyze_repository(
                repo_url, branch, commit_limit, candidate_limit
            )

        except asyncio.CancelledError:
            logger.info(f"⏹️  Analysis cancelled for {repo.name}")
            analysis_session.status = "cancelled"
            analysis_session.completed_at = datetime.utcnow()
            repo.status = "pending"  # Reset to pending for retry
            db.commit()
            return
        except Exception as e:
            logger.error(f"💥 Analysis failed: {e}")
            if analysis_session:
                analysis_session.status = "failed"
                analysis_session.error_message = str(e)
                analysis_session.completed_at = datetime.utcnow()
            if repo:
                repo.status = "failed"
            db.commit()
            return

        if "error" in result:
            error_msg = result["error"]
            details = result.get("details", "")

            if (
                result.get("error")
                == "Repository contains potential secrets and cannot be analyzed"
            ):
                logger.error(f"🚨 SECURITY VIOLATION: {error_msg}")
                logger.error(f"   Details: {details}")
                logger.error(
                    f"   Findings: {result.get('secret_findings_count', 0)} potential secrets"
                )
                logger.error(f"   Recommendation: {result.get('recommendation', '')}")

                analysis_session.status = "failed"
                analysis_session.error_message = f"SECURITY: {error_msg}"
                repo.status = "failed"

                logger.error("🛑 Analysis terminated for security reasons")
            else:
                logger.error(f"❌ Analysis failed: {error_msg}")
                analysis_session.status = "failed"
                analysis_session.error_message = error_msg
                repo.status = "failed"

            analysis_session.completed_at = datetime.utcnow()
            db.commit()
            return

        # Save the analysis results to database
        _save_analysis_results(db, repo, analysis_session, result)

        # Update repository status
        repo.status = "completed"
        repo.last_analyzed = datetime.utcnow()
        repo.total_commits = len(result.get("commits", []))

        if result.get("repo_info"):
            repo_info = result["repo_info"]
            if repo_info.get("first_commit_date"):
                repo.first_commit_date = repo_info["first_commit_date"]
            if repo_info.get("last_commit_date"):
                repo.last_commit_date = repo_info["last_commit_date"]

        # Update analysis session
        analysis_session.status = "completed"
        analysis_session.completed_at = datetime.utcnow()
        analysis_session.commits_analyzed = len(result.get("commits", []))
        analysis_session.patterns_found = len(result.get("pattern_analyses", []))

        db.commit()
        logger.info(f"✅ Analysis completed for {repo.name}")
        logger.info(
            f"📈 Found {analysis_session.patterns_found} patterns in {analysis_session.commits_analyzed} commits"
        )

    except asyncio.CancelledError:
        logger.info(f"⏹️  Background task cancelled for {repo_url}")
        if analysis_session:
            analysis_session.status = "cancelled"
            analysis_session.completed_at = datetime.utcnow()
        if repo:
            repo.status = "pending"
        try:
            if db:
                db.commit()
        except Exception:
            pass  # Ignore db errors during cancellation
        return
    except Exception as e:
        logger.error(f"💥 Background analysis failed: {e}")

        if analysis_session:
            analysis_session.status = "failed"
            analysis_session.error_message = str(e)
            analysis_session.completed_at = datetime.utcnow()

        if repo:
            repo.status = "failed"

        try:
            if db:
                db.commit()
        except Exception:
            pass  # Ignore db errors during error handling
    finally:
        try:
            if db:
                db.close()
        except Exception:
            pass  # Ignore db close errors


def _save_analysis_results(
    db, repo: Repository, analysis_session: AnalysisSession, result: dict
):
    """Save the analysis results to the database"""

    try:
        # Save technologies
        technologies = result.get("technologies", {})
        for category, tech_list in technologies.items():
            if isinstance(tech_list, dict):  # Handle languages dict
                for tech_name, count in tech_list.items():
                    _save_technology(db, repo.id, tech_name, category, count)
            elif isinstance(tech_list, list):  # Handle framework/library lists
                for tech_name in tech_list:
                    _save_technology(db, repo.id, tech_name, category, 1)

        # Save commits and file changes
        commits = result.get("commits", [])
        for commit_data in commits:
            try:
                commit = _save_commit(db, repo.id, commit_data)

                # Only save file changes if commit was successfully saved
                if commit:
                    # Save file changes for this commit
                    for file_change in commit_data.get("files_changed", []):
                        try:
                            _save_file_change(db, commit.id, file_change)
                        except Exception as e:
                            logger.warning(f"⚠️  Error saving file change: {e}")
                            continue
                else:
                    logger.warning(f"⚠️  Skipping file changes for failed commit")

            except Exception as e:
                logger.error(
                    f"💥 Error saving commit {commit_data.get('hash', 'unknown')}: {e}"
                )
                continue

        # Save patterns and pattern occurrences
        pattern_analyses = result.get("pattern_analyses", [])
        candidates = result.get("pattern_candidates", [])  # From git service

        for i, pattern_analysis in enumerate(pattern_analyses):
            if i < len(candidates):
                candidate = candidates[i]
                _save_pattern_analysis(
                    db, repo.id, analysis_session.id, pattern_analysis, candidate
                )

        db.commit()
        logger.info(f"💾 Saved analysis results for {repo.name}")

    except Exception as e:
        logger.error(f"💥 Error saving analysis results: {e}")
        db.rollback()
        raise


def _save_technology(db, repo_id: str, name: str, category: str, usage_count: int):
    """Save or update a technology record"""
    existing = (
        db.query(Technology)
        .filter(Technology.repository_id == repo_id, Technology.name == name)
        .first()
    )

    if existing:
        existing.usage_count += usage_count
        existing.last_seen = datetime.utcnow()
    else:
        tech = Technology(
            repository_id=repo_id,
            name=name,
            category=category,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            usage_count=usage_count,
        )
        db.add(tech)


def _save_commit(db, repo_id: str, commit_data: dict) -> Commit:
    """Save a commit record"""
    commit_hash = commit_data.get("hash")
    if not commit_hash:
        logger.warning("⚠️  Commit data missing hash field")
        return None

    try:
        # Check if commit already exists
        existing = db.query(Commit).filter(Commit.hash == commit_hash).first()

        if existing:
            return existing

        # Create new commit
        commit = Commit(
            repository_id=repo_id,
            hash=commit_hash,
            author_name=commit_data.get("author"),
            author_email=commit_data.get("author_email"),
            committed_date=commit_data["date"],
            message=commit_data.get("message"),
            files_changed_count=commit_data.get("stats", {}).get("files", 0),
            additions=commit_data.get("stats", {}).get("additions", 0),
            deletions=commit_data.get("stats", {}).get("deletions", 0),
        )
        db.add(commit)
        db.flush()  # Get the ID
        return commit

    except Exception as e:
        logger.error(f"💥 Error saving commit {commit_hash}: {e}")
        return None


def _save_file_change(db, commit_id: str, file_change: dict):
    """Save a file change record"""
    change = FileChange(
        commit_id=commit_id,
        file_path=file_change["file_path"],
        change_type=file_change.get("change_type", "modified"),
        language=file_change.get("language"),
        additions=file_change.get("additions", 0),
        deletions=file_change.get("deletions", 0),
        patch=(
            file_change.get("content", "")[:5000]
            if file_change.get("content")
            else None
        ),  # Truncate large patches
    )
    db.add(change)


def _save_pattern_analysis(
    db, repo_id: str, session_id: str, pattern_analysis: dict, candidate: dict
):
    """Save pattern analysis results"""

    # Find the commit this candidate belongs to
    commit_hash = candidate.get("commit_hash")
    commit_id = None
    if commit_hash:
        try:
            # Query using the correct hash field
            commit = db.query(Commit).filter(Commit.hash == commit_hash).first()

            if commit:
                commit_id = commit.id
            else:
                logger.warning(
                    f"⚠️  Commit with hash {commit_hash} not found in database"
                )

        except Exception as e:
            logger.error(f"💥 Error finding commit {commit_hash}: {e}")

    # Get or create patterns
    patterns = pattern_analysis.get("combined_patterns", [])

    for pattern_name in patterns:
        try:
            # Get or create the pattern
            pattern = db.query(Pattern).filter(Pattern.name == pattern_name).first()
            if not pattern:
                pattern = Pattern(
                    name=pattern_name,
                    category=_infer_pattern_category(pattern_name),
                    description=f"Auto-detected pattern: {pattern_name}",
                    complexity_level=pattern_analysis.get(
                        "skill_level", "intermediate"
                    ),
                    is_antipattern=False,  # Could be enhanced with AI detection
                    detection_rules={},
                )
                db.add(pattern)
                db.flush()

            # Only create pattern occurrence if we have a valid commit_id
            if commit_id:
                occurrence = PatternOccurrence(
                    pattern_id=pattern.id,
                    repository_id=repo_id,
                    commit_id=commit_id,  # Now properly mapped to actual commit
                    file_path=candidate.get("file_path", "unknown"),
                    code_snippet=candidate.get("code", "")[
                        :1000
                    ],  # Truncate large snippets
                    confidence_score=pattern_analysis.get("complexity_score", 1.0)
                    / 10.0,  # Convert to 0-1 range
                    detected_at=datetime.utcnow(),
                )
                db.add(occurrence)
            else:
                logger.warning(
                    f"⚠️  Skipping pattern occurrence for {pattern_name} - no commit mapping found"
                )
        except Exception as e:
            logger.error(f"💥 Error saving pattern {pattern_name}: {e}")
            continue


def _infer_pattern_category(pattern_name: str) -> str:
    """Infer pattern category from pattern name"""
    name_lower = pattern_name.lower()

    if any(keyword in name_lower for keyword in ["react", "component", "jsx", "hook"]):
        return "react"
    elif any(
        keyword in name_lower for keyword in ["async", "promise", "await", "callback"]
    ):
        return "async"
    elif any(
        keyword in name_lower for keyword in ["function", "method", "class", "object"]
    ):
        return "javascript"
    elif any(
        keyword in name_lower for keyword in ["error", "exception", "try", "catch"]
    ):
        return "error_handling"
    else:
        return "general"


def _save_pattern_analysis(
    db, repo_id: str, session_id: str, pattern_analysis: dict, candidate: dict
):
    """Save pattern analysis results"""

    # Get or create patterns
    patterns = pattern_analysis.get("combined_patterns", [])

    if not patterns:
        # Fallback to detected_patterns if combined_patterns is empty
        patterns = pattern_analysis.get("detected_patterns", [])

    for pattern_name in patterns:
        try:
            # Get or create the pattern
            pattern = db.query(Pattern).filter(Pattern.name == pattern_name).first()
            if not pattern:
                pattern = Pattern(
                    name=pattern_name,
                    category=_infer_pattern_category(pattern_name),
                    description=f"Auto-detected pattern: {pattern_name}",
                    complexity_level=pattern_analysis.get(
                        "skill_level", "intermediate"
                    ),
                    is_antipattern=False,
                )
                db.add(pattern)
                db.flush()

            # Create pattern occurrence WITHOUT requiring commit_id
            occurrence = PatternOccurrence(
                pattern_id=pattern.id,
                repository_id=repo_id,
                file_path=candidate.get("file_path", "unknown"),
                code_snippet=candidate.get("code", "")[:1000],
                confidence_score=pattern_analysis.get("complexity_score", 1.0) / 10.0,
                detected_at=datetime.utcnow(),
                # Make commit_id optional
                commit_id=None,  # We'll update this later if we can map it
            )
            db.add(occurrence)

        except Exception as e:
            logger.error(f"💥 Error saving pattern {pattern_name}: {e}")
            continue
