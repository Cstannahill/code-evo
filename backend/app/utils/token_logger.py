import json
import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _logs_dir() -> str:
    """Resolve a stable logs directory under backend/logs relative to this file."""
    # __file__ is backend/app/utils/token_logger.py -> go up to backend
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logs = os.path.join(base_dir, "logs")
    os.makedirs(logs, exist_ok=True)
    return logs


def _log_path(filename: str = "analysis_tokens.log") -> str:
    return os.path.join(_logs_dir(), filename)


def estimate_tokens_from_text(text: str) -> int:
    """Rough token estimate: ~4 chars per token (heuristic)."""
    try:
        return max(0, int(len(text) / 4))
    except Exception:
        return 0


def estimate_tokens_from_snippets(snippets: List[str]) -> int:
    total = 0
    for s in snippets:
        total += estimate_tokens_from_text(s or "")
    return total


def append_json_log(
    record: Dict[str, Any], filename: str = "analysis_tokens.log"
) -> None:
    """Append a single-line JSON record to the analysis token log file."""
    try:
        record_with_time = {"timestamp": datetime.utcnow().isoformat(), **record}
        path = _log_path(filename)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record_with_time, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write token log: {e}")


def log_analysis_run(
    *,
    repo_url: str,
    model_id: Optional[str],
    commit_count: int,
    total_candidates: int,
    analyzed_candidates: int,
    snippets: List[str],
    task_counts: Dict[str, int],
    repo_size_bytes: Optional[int] = None,
    duration_seconds: Optional[float] = None,
) -> None:
    """Aggregate and write a JSON log entry for a full analysis pipeline run.

    Args:
        repo_url: Repository URL analyzed
        model_id: Selected model identifier if any
        commit_count: Number of commits processed
        total_candidates: Total pattern candidates identified
        analyzed_candidates: Candidates actually sent for AI analysis
        snippets: Code snippets analyzed (for token estimation)
        task_counts: Counts for each task type, e.g., {"pattern": N, "quality": N, ...}
        repo_size_bytes: Optional total repository size (sum of blobs)
        duration_seconds: Optional wall-clock duration for the run
    """
    try:
        estimated_tokens = estimate_tokens_from_snippets(snippets)

        payload: Dict[str, Any] = {
            "repo_url": repo_url,
            "model_id": model_id,
            "commit_count": commit_count,
            "total_candidates": total_candidates,
            "analyzed_candidates": analyzed_candidates,
            "estimated_tokens": estimated_tokens,
            "task_counts": task_counts,
        }
        if repo_size_bytes is not None:
            payload["repo_size_bytes"] = repo_size_bytes
            # Include human-friendly GB representation
            payload["repo_size_gb"] = round(repo_size_bytes / (1024**3), 3)
        if duration_seconds is not None:
            payload["duration_seconds"] = round(float(duration_seconds), 3)

        append_json_log(payload)
    except Exception as e:
        logger.warning(f"Failed to aggregate token log: {e}")
