import os
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.services.git_service import GitService
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Orchestrates repository cloning, data extraction, and AI-powered analysis.
    Combines GitService for repository operations with AIService for code insights.

    Provides methods to analyze full repositories or local paths, and to generate AI insights.
    """

    def __init__(self):
        # set up git and AI backends
        self.git = GitService()
        self.ai = AIService()

        # mirror AI availability and clients
        status = self.ai.get_status()
        self.ollama_available: bool = status.get("ollama_available", False)
        self.llm = getattr(self.ai, "llm", None)
        self.embeddings = getattr(self.ai, "embeddings", None)
        self.collection = getattr(self.ai, "collection", None)

        logger.info("AnalysisService initialized")

    def get_status(self) -> Dict[str, Any]:
        """
        Delegate health/status check to the underlying AIService.
        """
        return self.ai.get_status()

    async def generate_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Delegate generation of AI insights to AIService.
        """
        try:
            return await self.ai.generate_insights(analysis_data)
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []

    async def analyze_repository(
        self,
        repo_url: str,
        branch: str = "main",
        commit_limit: int = 100,
        candidate_limit: Optional[int] = 20,
    ) -> Dict[str, Any]:
        """
        Clone the repository, extract history, and run AI analyses.

        Returns a report dictionary with:
          - repo_info
          - technologies
          - commits
          - pattern_analyses
          - quality_analyses
          - evolution_analyses
          - insights
          - pattern_candidates (for saving to database)
        """
        report: Dict[str, Any] = {}
        try:
            logger.info(f"🔄 Starting repository analysis for {repo_url}")

            # Clone and inspect
            logger.info(f"📥 Cloning repository {repo_url}...")
            repo = self.git.clone_repository(repo_url, branch)

            logger.info(f"🔍 Extracting repository information...")
            report["repo_info"] = self.git.get_repository_info(repo)
            report["technologies"] = self.git.extract_technologies(repo)

            logger.info(
                f"📚 Found {len(report['technologies'].get('languages', {}))} languages"
            )

            # Commit history
            logger.info(f"📖 Analyzing commit history (limit: {commit_limit})...")
            commits = self.git.get_commit_history(repo, limit=commit_limit)
            report["commits"] = commits
            logger.info(f"📈 Processed {len(commits)} commits")

            # Prepare pattern candidates
            logger.info(f"🔍 Extracting code patterns...")
            candidates = self.git.get_pattern_candidates(commits)
            report["total_candidates"] = len(candidates)
            logger.info(f"🎯 Found {len(candidates)} code patterns to analyze")

            # Limit candidates for analysis but keep all for database
            report["pattern_candidates"] = candidates  # Full list for database
            analysis_candidates = (
                candidates[:candidate_limit] if candidate_limit else candidates
            )

            logger.info(
                f"🤖 Running AI analysis on {len(analysis_candidates)} patterns..."
            )

            # Run AI analyses in parallel
            pattern_tasks = [
                self.ai.analyze_code_pattern(c["code"], c["language"])
                for c in analysis_candidates
            ]
            quality_tasks = [
                self.ai.analyze_code_quality(c["code"], c["language"])
                for c in analysis_candidates
            ]

            logger.info(
                f"⚡ Processing {len(pattern_tasks)} pattern analyses and {len(quality_tasks)} quality analyses..."
            )
            pattern_results, quality_results = await asyncio.gather(
                asyncio.gather(*pattern_tasks), asyncio.gather(*quality_tasks)
            )
            report["pattern_analyses"] = pattern_results
            report["quality_analyses"] = quality_results
            logger.info(f"✅ Completed AI analysis")

            # Evolution: compare first and last snippet if available
            logger.info(f"🔄 Analyzing code evolution...")
            evolution: List[Dict[str, Any]] = []
            if len(analysis_candidates) >= 2:
                old = analysis_candidates[0]
                new = analysis_candidates[-1]
                evo = await self.ai.analyze_evolution(
                    old["code"], new["code"], context=repo_url
                )
                evolution.append(evo)
                logger.info(f"📊 Evolution analysis completed")
            report["evolution_analyses"] = evolution

            # Aggregate insights - FIX THE SET ISSUE HERE
            logger.info(f"💡 Generating insights...")

            # Collect all unique patterns from analysis results
            all_patterns = set()
            for res in pattern_results:
                all_patterns.update(res.get("combined_patterns", []))

            # Convert set to dict with occurrence counts
            pattern_dict = {}
            for pattern in all_patterns:
                # Count occurrences across all results
                count = sum(
                    1
                    for res in pattern_results
                    if pattern in res.get("combined_patterns", [])
                )
                pattern_dict[pattern] = count

            insights_input = {
                "patterns": pattern_dict,  # Now it's a proper dict, not a set
                "technologies": list(
                    report["technologies"].get("languages", {}).keys()
                ),
                "commits": len(commits),
            }
            report["insights"] = await self.generate_insights(insights_input)
            logger.info(
                f"🎉 Analysis complete! Generated {len(report['insights'])} insights"
            )

        except Exception as e:
            logger.error(f"💥 Analysis failed: {e}")
            report["error"] = str(e)
        finally:
            # Cleanup temp dirs
            try:
                logger.info(f"🧹 Cleaning up temporary files...")
                self.git.cleanup()
            except Exception as cleanup_err:
                logger.warning(f"⚠️ Cleanup error: {cleanup_err}")

        return report

    def analyze_local_path(
        self,
        local_path: str,
        commit_limit: int = 50,
        candidate_limit: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """
        Analyze an already-cloned local repository at `local_path`.
        Synchronous wrapper for analyze_repository when repo is on disk.
        """
        report: Dict[str, Any] = {}

        if not os.path.isdir(local_path):
            raise ValueError(f"Invalid repository path: {local_path}")

        # Use Repo directly for local path
        from git import Repo

        repo = Repo(local_path)
        report["repo_info"] = self.git.get_repository_info(repo)
        report["technologies"] = self.git.extract_technologies(repo)

        commits = self.git.get_commit_history(repo, limit=commit_limit)
        report["commits"] = commits

        candidates = self.git.get_pattern_candidates(commits)[:candidate_limit]
        report["total_candidates"] = len(candidates)

        # Run full async analysis using repository URL placeholder
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async_report = loop.run_until_complete(
            self.analyze_repository(
                repo_url=local_path,
                branch="",
                commit_limit=commit_limit,
                candidate_limit=candidate_limit,
            )
        )
        loop.close()

        # Merge async results
        report.update(
            {
                k: v
                for k, v in async_report.items()
                if k
                in (
                    "pattern_analyses",
                    "quality_analyses",
                    "evolution_analyses",
                    "insights",
                )
            }
        )

        return report
