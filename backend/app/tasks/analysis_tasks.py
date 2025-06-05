# backend/app/tasks/analysis_tasks.py

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.database import get_enhanced_database_manager
from app.services.analysis_service import AnalysisService
from app.services.repository_service import RepositoryService
from app.services.pattern_service import PatternService
from app.services.ai_analysis_service import AIAnalysisService
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

# Services will be lazily initialized
repository_service = None
pattern_service = None
ai_analysis_service = None


def get_services():
    """Lazy initialization of services"""
    global repository_service, pattern_service, ai_analysis_service

    if repository_service is None:
        repository_service = RepositoryService()
    if pattern_service is None:
        pattern_service = PatternService()
    if ai_analysis_service is None:
        ai_analysis_service = AIAnalysisService()

    return repository_service, pattern_service, ai_analysis_service


async def analyze_repository_background(
    repo_url: str,
    branch: str,
    commit_limit: int,
    candidate_limit: int,
    model_id: Optional[str] = None,  # Add model parameter
):
    """Background task with model selection support and MongoDB integration"""

    db_manager = None
    analysis_session = None
    repo = None
    try:
        # Get enhanced database manager
        db_manager = get_enhanced_database_manager()

        # Initialize analysis service
        analysis_service = AnalysisService()

        # Use specific model if provided
        if model_id:
            logger.info(f"🤖 Using selected model: {model_id}")
            analysis_service.set_preferred_model(model_id)

        # Find the repository using MongoDB service
        repo = await repository_service.get_repository_by_url(repo_url)
        if not repo:
            logger.error(f"❌ Repository not found: {repo_url}")
            return

        logger.info(f"🚀 Starting background analysis for {repo.name}")

        # Create analysis session using AI analysis service
        session_data = {
            "repository_id": str(repo.id),
            "status": "running",
            "commits_analyzed": 0,
            "patterns_found": 0,
            "started_at": datetime.utcnow(),
            "configuration": {
                "commit_limit": commit_limit,
                "candidate_limit": candidate_limit,
                "branch": branch,
            },
        }

        analysis_session = await ai_analysis_service.create_analysis_session(
            repo.id, session_data.get("configuration", {}), model_id
        )
        logger.info(f"📊 Analysis session created: {analysis_session.id}")

        # Check for cancellation before running analysis
        try:
            logger.info(f"🔍 Cloning repository {repo_url}...")
            logger.info(f"🤖 Running AI analysis with {commit_limit} commits limit...")

            # Run the analysis - this will automatically persist to MongoDB
            result = await analysis_service.analyze_repository(
                repo_url, branch, commit_limit, candidate_limit
            )

        except asyncio.CancelledError:
            logger.info(f"⏹️  Analysis cancelled for {repo.name}")
            await ai_analysis_service.update_analysis_session(
                analysis_session.id,
                {"status": "cancelled", "completed_at": datetime.utcnow()},
            )
            await repository_service.update_repository_status(repo.id, "pending")
            return
        except Exception as e:
            logger.error(f"💥 Analysis failed: {e}")
            if analysis_session:
                await ai_analysis_service.update_analysis_session(
                    analysis_session.id,
                    {
                        "status": "failed",
                        "error_message": str(e),
                        "completed_at": datetime.utcnow(),
                    },
                )
            if repo:
                await repository_service.update_repository_status(repo.id, "failed")
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

                await ai_analysis_service.update_analysis_session(
                    analysis_session.id,
                    {
                        "status": "failed",
                        "error_message": f"SECURITY: {error_msg}",
                        "completed_at": datetime.utcnow(),
                    },
                )
                await repository_service.update_repository_status(repo.id, "failed")

                logger.error("🛑 Analysis terminated for security reasons")
            else:
                logger.error(f"❌ Analysis failed: {error_msg}")
                await ai_analysis_service.update_analysis_session(
                    analysis_session.id,
                    {
                        "status": "failed",
                        "error_message": error_msg,
                        "completed_at": datetime.utcnow(),
                    },
                )
                await repository_service.update_repository_status(repo.id, "failed")

            return

        # Analysis completed successfully - data is already persisted by AnalysisService
        # Update repository status
        repo_update_data = {
            "status": "completed",
            "last_analyzed": datetime.utcnow(),
            "total_commits": len(result.get("commits", [])),
        }

        if result.get("repo_info"):
            repo_info = result["repo_info"]
            if repo_info.get("first_commit_date"):
                repo_update_data["first_commit_date"] = repo_info["first_commit_date"]
            if repo_info.get("last_commit_date"):
                repo_update_data["last_commit_date"] = repo_info["last_commit_date"]

        await repository_service.update_repository(repo.id, repo_update_data)

        # Update analysis session
        session_update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "commits_analyzed": len(result.get("commits", [])),
            "patterns_found": len(result.get("pattern_analyses", [])),
        }
        await ai_analysis_service.update_analysis_session(
            analysis_session.id, session_update_data
        )

        logger.info(f"✅ Analysis completed for {repo.name}")
        logger.info(
            f"📈 Found {session_update_data['patterns_found']} patterns in {session_update_data['commits_analyzed']} commits"
        )

    except asyncio.CancelledError:
        logger.info(f"⏹️  Background task cancelled for {repo_url}")
        if analysis_session:
            await ai_analysis_service.update_analysis_session(
                analysis_session.id,
                {"status": "cancelled", "completed_at": datetime.utcnow()},
            )
        if repo:
            await repository_service.update_repository_status(repo.id, "pending")
        return
    except Exception as e:
        logger.error(f"💥 Background analysis failed: {e}")

        if analysis_session:
            await ai_analysis_service.update_analysis_session(
                analysis_session.id,
                {
                    "status": "failed",
                    "error_message": str(e),
                    "completed_at": datetime.utcnow(),
                },
            )

        if repo:
            await repository_service.update_repository_status(repo.id, "failed")


# Note: Analysis results are now automatically persisted by the AnalysisService
# via its _persist_analysis_results() and _persist_patterns() methods.
# The helper functions below are kept for reference but are no longer used.


async def get_analysis_status(repository_id: str) -> Dict[str, Any]:
    """Get the current analysis status for a repository"""
    try:
        sessions = await ai_analysis_service.get_analysis_sessions(repository_id)
        if not sessions:
            return {"status": "not_started"}

        latest_session = sessions[0]  # Sessions are sorted by creation date
        return {
            "status": latest_session.status,
            "started_at": latest_session.started_at,
            "completed_at": latest_session.completed_at,
            "commits_analyzed": latest_session.commits_analyzed,
            "patterns_found": latest_session.patterns_found,
            "error_message": latest_session.error_message,
        }
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        return {"status": "error", "error": str(e)}


async def cancel_analysis(repository_id: str) -> bool:
    """Cancel any running analysis for a repository"""
    try:
        sessions = await ai_analysis_service.get_analysis_sessions(repository_id)
        for session in sessions:
            if session.status == "running":
                await ai_analysis_service.update_analysis_session(
                    session.id,
                    {"status": "cancelled", "completed_at": datetime.utcnow()},
                )
                await repository_service.update_repository_status(
                    repository_id, "pending"
                )
                return True
        return False
    except Exception as e:
        logger.error(f"Error cancelling analysis: {e}")
        return False
