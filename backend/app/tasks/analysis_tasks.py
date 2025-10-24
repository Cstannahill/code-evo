# backend/app/tasks/analysis_tasks.py

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId

from app.core.database import get_enhanced_database_manager
from app.services.analysis_service import AnalysisService
from app.core.service_manager import (
    get_repository_service,
    get_pattern_service, 
    get_ai_analysis_service
)
from app.models.repository import (
    Repository,
    AnalysisSession,
    Technology,
    Pattern,
    PatternOccurrence,
    Commit,
    FileChange,
)
from app.models.repository import (
    get_repository_by_url,
    get_analysis_sessions_by_repository,
)

logger = logging.getLogger(__name__)

# Services are managed by centralized service manager


async def analyze_repository_background(
    repo_url: str,
    branch: str,
    commit_limit: int,
    candidate_limit: int,
    model_id: Optional[str] = None,  # Add model parameter
    user_id: Optional[str] = None,
):
    """Background task with model selection support and MongoDB integration"""

    db_manager = None
    analysis_session = None
    repo = None
    try:
        # Get enhanced database manager
        db_manager = get_enhanced_database_manager()

        # Initialize analysis service
        from app.core.service_manager import get_analysis_service
        analysis_service = get_analysis_service()

        # Use specific model if provided
        if model_id:
            logger.info(f"🤖 Using selected model: {model_id}")
            analysis_service.set_preferred_model(model_id)

        # Find the repository using MongoDB service
        engine = get_repository_service().engine
        repo = await get_repository_by_url(engine, repo_url)
        if not repo:
            logger.error(f"❌ Repository not found: {repo_url}")
            return
        repo_id_str = str(repo.id)

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

        analysis_session = await get_ai_analysis_service().create_analysis_session(
            repo_id_str, session_data.get("configuration", {})
        )
        logger.info(f"📊 Analysis session created: {analysis_session.id}")

        # Check for cancellation before running analysis
        try:
            logger.info(f"🔍 Cloning repository {repo_url}...")
            logger.info(f"🤖 Running AI analysis with {commit_limit} commits limit...")

            # Run the analysis - this will automatically persist to MongoDB
            result = await analysis_service.analyze_repository(
                repo_url,
                branch,
                commit_limit,
                candidate_limit,
                user_id=user_id,
            )

        except asyncio.CancelledError:
            logger.info(f"⏹️  Analysis cancelled for {repo.name}")
            await get_ai_analysis_service().update_analysis_session(
                str(analysis_session.id), status="cancelled"
            )
            await get_repository_service().update_repository_status(repo_id_str, "pending")
            return
        except Exception as e:
            logger.error(f"💥 Analysis failed: {e}")
            if analysis_session:
                await get_ai_analysis_service().update_analysis_session(
                    str(analysis_session.id), status="failed", error_message=str(e)
                )
            if repo:
                await get_repository_service().update_repository_status(repo_id_str, "failed")
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

                await get_ai_analysis_service().update_analysis_session(
                    str(analysis_session.id),
                    status="failed",
                    error_message=f"SECURITY: {error_msg}",
                )
                await get_repository_service().update_repository_status(repo_id_str, "failed")

                logger.error("🛑 Analysis terminated for security reasons")
            else:
                logger.error(f"❌ Analysis failed: {error_msg}")
                await get_ai_analysis_service().update_analysis_session(
                    str(analysis_session.id), status="failed", error_message=error_msg
                )
                await get_repository_service().update_repository_status(repo_id_str, "failed")

            return

        # Analysis completed successfully - data is already persisted by AnalysisService
        # Update repository status
        await get_repository_service().update_repository_status(repo_id_str, "completed")

        # Update analysis session
        patterns_found = len(result.get("pattern_analyses", []))
        commits_analyzed = len(result.get("commits", []))
        await get_ai_analysis_service().update_analysis_session(
            str(analysis_session.id),
            status="completed",
            commits_analyzed=commits_analyzed,
            patterns_found=patterns_found,
        )
        logger.info(f"✅ Analysis completed for {repo.name}")
        logger.info(f"📈 Found {patterns_found} patterns in {commits_analyzed} commits")

    except asyncio.CancelledError:
        logger.info(f"⏹️  Background task cancelled for {repo_url}")
        if analysis_session:
            await get_ai_analysis_service().update_analysis_session(
                str(analysis_session.id), status="cancelled"
            )
        if repo:
            repo_id_str = str(repo.id)
            await get_repository_service().update_repository_status(repo_id_str, "pending")
        return
    except Exception as e:
        logger.error(f"💥 Background analysis failed: {e}")

        if analysis_session:
            await get_ai_analysis_service().update_analysis_session(
                str(analysis_session.id), status="failed", error_message=str(e)
            )
        if repo:
            repo_id_str = str(repo.id)
            await get_repository_service().update_repository_status(repo_id_str, "failed")


# Note: Analysis results are now automatically persisted by the AnalysisService
# via its _persist_analysis_results() and _persist_patterns() methods.
# The helper functions below are kept for reference but are no longer used.


async def get_analysis_status(repository_id: str) -> Dict[str, Any]:
    """Get the current analysis status for a repository"""
    try:
        sessions = await get_analysis_sessions_by_repository(
            get_ai_analysis_service().engine, ObjectId(repository_id)
        )
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
        sessions = await get_analysis_sessions_by_repository(
            get_ai_analysis_service().engine, ObjectId(repository_id)
        )
        for session in sessions:
            if session.status == "running":
                await get_ai_analysis_service().update_analysis_session(
                    str(session.id), status="cancelled"
                )
                await get_repository_service().update_repository_status(
                    str(repository_id), "pending"
                )
                return True
        return False
    except Exception as e:
        logger.error(f"Error cancelling analysis: {e}")
        return False


async def analyze_repository_incremental_background(
    repo_url: str,
    branch: str,
    commit_limit: int,
    candidate_limit: int,
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    include_security_scan: bool = True,
    include_performance_scan: bool = True,
    include_architectural_scan: bool = True,
):
    """Enhanced background task for incremental repository analysis with deep commit analysis"""
    
    db_manager = None
    analysis_session = None
    repo = None
    try:
        # Get enhanced database manager
        db_manager = get_enhanced_database_manager()

        # Initialize analysis service
        from app.core.service_manager import get_analysis_service
        analysis_service = get_analysis_service()

        # Use specific model if provided
        if model_id:
            logger.info(f"🤖 Using selected model: {model_id}")
            analysis_service.set_preferred_model(model_id)

        # Find the repository using MongoDB service
        engine = get_repository_service().engine
        repo = await get_repository_by_url(engine, repo_url)
        if not repo:
            logger.error(f"❌ Repository not found: {repo_url}")
            return
        repo_id_str = str(repo.id)

        logger.info(f"🚀 Starting incremental analysis for {repo.name}")

        # Create analysis session with enhanced configuration
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
                "analysis_type": "incremental",
                "include_security_scan": include_security_scan,
                "include_performance_scan": include_performance_scan,
                "include_architectural_scan": include_architectural_scan,
                "model_id": model_id,
            },
        }

        analysis_session = await get_ai_analysis_service().create_analysis_session(
            repo_id_str, session_data.get("configuration", {})
        )
        logger.info(f"📊 Analysis session created: {analysis_session.id}")

        # Run incremental analysis with enhanced commit analysis
        try:
            logger.info(f"🔍 Cloning repository {repo_url}...")
            logger.info(f"🤖 Running incremental AI analysis with {commit_limit} commits limit...")

            # Run the incremental analysis - this will automatically persist to MongoDB
            result = await analysis_service.analyze_repository_incremental(
                repo_url,
                branch,
                commit_limit,
                candidate_limit,
                user_id=user_id,
            )

        except asyncio.CancelledError:
            logger.info(f"⏹️  Incremental analysis cancelled for {repo.name}")
            await get_ai_analysis_service().update_analysis_session(
                str(analysis_session.id), status="cancelled"
            )
            await get_repository_service().update_repository_status(repo_id_str, "pending")
            return
        except Exception as e:
            logger.error(f"💥 Incremental analysis failed: {e}")
            if analysis_session:
                await get_ai_analysis_service().update_analysis_session(
                    str(analysis_session.id), status="failed", error_message=str(e)
                )
            if repo:
                await get_repository_service().update_repository_status(repo_id_str, "failed")
            return

        if "error" in result:
            error_msg = result["error"]
            logger.error(f"❌ Incremental analysis failed: {error_msg}")
            await get_ai_analysis_service().update_analysis_session(
                str(analysis_session.id), status="failed", error_message=error_msg
            )
            await get_repository_service().update_repository_status(repo_id_str, "failed")
            return

        # Analysis completed successfully - data is already persisted by AnalysisService
        # Update repository status
        await get_repository_service().update_repository_status(repo_id_str, "completed")

        # Update analysis session with enhanced metrics
        patterns_found = len(result.get("pattern_analyses", []))
        commits_analyzed = len(result.get("commits", []))
        
        # Calculate enhanced metrics
        incremental_data = result.get("incremental_analysis", {})
        changes_detected = incremental_data.get("changes_detected", 0)
        
        await get_ai_analysis_service().update_analysis_session(
            str(analysis_session.id),
            status="completed",
            commits_analyzed=commits_analyzed,
            patterns_found=patterns_found,
            configuration={
                **session_data["configuration"],
                "changes_detected": changes_detected,
                "incremental_efficiency": f"{changes_detected}/{commits_analyzed}" if commits_analyzed > 0 else "0/0"
            }
        )
        
        logger.info(f"✅ Incremental analysis completed for {repo.name}")
        logger.info(f"📈 Found {patterns_found} patterns in {commits_analyzed} commits")
        logger.info(f"🔄 Detected {changes_detected} changes for incremental processing")

    except asyncio.CancelledError:
        logger.info(f"⏹️  Background incremental task cancelled for {repo_url}")
        if analysis_session:
            await get_ai_analysis_service().update_analysis_session(
                str(analysis_session.id), status="cancelled"
            )
        if repo:
            repo_id_str = str(repo.id)
            await get_repository_service().update_repository_status(repo_id_str, "pending")
        return
    except Exception as e:
        logger.error(f"💥 Background incremental analysis failed: {e}")

        if analysis_session:
            await get_ai_analysis_service().update_analysis_session(
                str(analysis_session.id), status="failed", error_message=str(e)
            )
        if repo:
            repo_id_str = str(repo.id)
            await get_repository_service().update_repository_status(repo_id_str, "failed")