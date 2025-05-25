# backend/app/tasks/analysis_tasks.py
import asyncio
from app.services.analysis_service import AnalysisService

_svc = AnalysisService()


def analyze_repository_background(
    repo_url: str,
    branch: str = "main",
    commit_limit: int = 100,
    candidate_limit: int = 20,
) -> None:
    """
    Fire-and-forget wrapper for AnalysisService.analyze_repository
    (e.g. for FastAPI BackgroundTasks.add_task)
    """
    try:
        # You could also offload to a thread pool if you like
        asyncio.run(
            _svc.analyze_repository(repo_url, branch, commit_limit, candidate_limit)
        )
    except Exception as e:
        # log and swallow so the background thread doesn’t kill your app
        import logging

        logging.getLogger(__name__).error(f"Background analysis failed: {e}")
