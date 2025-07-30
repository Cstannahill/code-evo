import os
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.services.git_service import GitService
from app.services.ai_service import AIService
from app.services.repository_service import RepositoryService
from app.services.pattern_service import PatternService
from app.services.ai_analysis_service import AIAnalysisService

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Orchestrates repository cloning, data extraction, and AI-powered analysis.
    Combines GitService for repository operations with AIService for code insights.
    Now enhanced with MongoDB integration for comprehensive data persistence.

    Provides methods to analyze full repositories or local paths, and to generate AI insights.
    """

    def __init__(self):
        # set up git and AI backends using service manager
        from app.core.service_manager import (
            get_git_service,
            get_ai_service, 
            get_repository_service,
            get_pattern_service,
            get_ai_analysis_service
        )
        
        self.git = get_git_service()
        self.ai = get_ai_service()

        # Initialize MongoDB services using singletons
        self.repository_service = get_repository_service()
        self.pattern_service = get_pattern_service()
        self.ai_analysis_service = get_ai_analysis_service()

        # mirror AI availability and clients
        status = self.ai.get_status()
        self.ollama_available: bool = status.get("ollama_available", False)
        self.llm = getattr(self.ai, "llm", None)
        self.embeddings = getattr(self.ai, "embeddings", None)
        self.collection = getattr(self.ai, "collection", None)

        logger.info("AnalysisService initialized with MongoDB integration")

    def set_preferred_model(self, model_id: str):
        """Set the preferred model for AI analysis."""
        if hasattr(self.ai, "set_preferred_model"):
            self.ai.set_preferred_model(model_id)
            logger.info(f"🤖 Set preferred model to: {model_id}")
        else:
            logger.warning(
                f"⚠️ AIService does not support model selection. Ignoring model_id: {model_id}"
            )

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

            # Persist results to MongoDB
            await self._persist_analysis_results(repo_url, branch, report)

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

    async def _persist_analysis_results(
        self, repo_url: str, branch: str, report: Dict[str, Any]
    ) -> Optional[str]:
        """
        Persist analysis results to MongoDB

        Args:
            repo_url: Repository URL
            branch: Repository branch
            report: Analysis report data

        Returns:
            Repository ID if successful, None otherwise
        """
        try:
            logger.info(f"💾 Persisting analysis results to MongoDB...")

            # Extract repository info
            repo_info = report.get("repo_info", {})
            repo_name = repo_info.get(
                "name", repo_url.split("/")[-1].replace(".git", "")
            )

            # Get or create repository (handles existing repositories gracefully)
            repository = await self.repository_service.get_or_create_repository(
                url=repo_url,
                name=repo_name,
                description=repo_info.get("description"),
                branch=branch,
            )

            logger.info(f"✅ Repository created/updated: {repository.id}")

            # Add commits
            commits_data = report.get("commits", [])
            if commits_data:
                await self.repository_service.add_commits(
                    str(repository.id), commits_data
                )
                logger.info(f"✅ Added {len(commits_data)} commits")

            # Add technologies
            technologies_data = []
            tech_info = report.get("technologies", {})
            for category, items in tech_info.items():
                if isinstance(items, dict):
                    for name, details in items.items():
                        technologies_data.append(
                            {
                                "name": name,
                                "category": category,
                                "usage_count": (
                                    details.get("count", 0)
                                    if isinstance(details, dict)
                                    else 1
                                ),
                                "version": (
                                    details.get("version")
                                    if isinstance(details, dict)
                                    else None
                                ),
                                "tech_metadata": (
                                    details if isinstance(details, dict) else {}
                                ),
                            }
                        )
                elif isinstance(items, list):
                    for item in items:
                        technologies_data.append(
                            {
                                "name": item,
                                "category": category,
                                "usage_count": 1,
                                "tech_metadata": {},
                            }
                        )

            if technologies_data:
                await self.repository_service.add_technologies(
                    str(repository.id), technologies_data
                )
                logger.info(f"✅ Added {len(technologies_data)} technologies")

            # Add patterns with AI analysis results
            pattern_results = report.get("pattern_analyses", [])
            quality_results = report.get("quality_analyses", [])
            candidates = report.get("pattern_candidates", [])

            if pattern_results and candidates:
                await self._persist_patterns(
                    str(repository.id), candidates, pattern_results, quality_results
                )

            # Update repository status to completed
            await self.repository_service.update_repository_status(
                str(repository.id), "completed"
            )

            logger.info(f"🎉 Successfully persisted analysis results for {repo_name}")
            return str(repository.id)

        except Exception as e:
            logger.error(f"❌ Failed to persist analysis results: {e}")
            return None

    async def _persist_patterns(
        self,
        repository_id: str,
        candidates: List[Dict[str, Any]],
        pattern_results: List[Dict[str, Any]],
        quality_results: List[Dict[str, Any]],
    ) -> None:
        """Persist pattern analysis results to MongoDB"""
        try:
            # Process patterns and their occurrences
            for i, (candidate, pattern_result, quality_result) in enumerate(
                zip(candidates, pattern_results, quality_results)
            ):
                # Extract patterns from AI analysis
                patterns = pattern_result.get("combined_patterns", [])

                for pattern_name in patterns:
                    # Create pattern occurrence
                    await self.pattern_service.add_pattern_occurrence(
                        repository_id=repository_id,
                        pattern_name=pattern_name,
                        file_path=candidate.get("file_path", "unknown"),
                        code_snippet=candidate.get("code", ""),
                        line_number=candidate.get("line_number", 0),
                        confidence_score=pattern_result.get("confidence", 0.8),
                        ai_model_used="codellama:7b",  # TODO: Get from AI service
                        ai_analysis_metadata={
                            "pattern_analysis": pattern_result,
                            "quality_analysis": quality_result,
                            "analysis_index": i,
                        },
                    )

            logger.info(f"✅ Added pattern occurrences for repository {repository_id}")

        except Exception as e:
            logger.error(f"❌ Failed to persist patterns: {e}")
            raise

    async def analyze_local_path(
        self,
        local_path: str,
        commit_limit: int = 50,
        candidate_limit: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """
        Analyze an already-cloned local repository at `local_path`.
        Now properly async to avoid event loop conflicts.
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

        candidates = self.git.get_pattern_candidates(commits)
        report["pattern_candidates"] = candidates  # Full list for database
        analysis_candidates = (
            candidates[:candidate_limit] if candidate_limit else candidates
        )
        report["total_candidates"] = len(candidates)

        # Run AI analyses in parallel (same as analyze_repository)
        logger.info(f"🤖 Running AI analysis on {len(analysis_candidates)} patterns...")

        pattern_tasks = [
            self.ai.analyze_code_pattern(c["code"], c["language"])
            for c in analysis_candidates
        ]
        quality_tasks = [
            self.ai.analyze_code_quality(c["code"], c["language"])
            for c in analysis_candidates
        ]

        pattern_results, quality_results = await asyncio.gather(
            asyncio.gather(*pattern_tasks), asyncio.gather(*quality_tasks)
        )
        report["pattern_analyses"] = pattern_results
        report["quality_analyses"] = quality_results

        # Evolution analysis
        evolution: List[Dict[str, Any]] = []
        if len(analysis_candidates) >= 2:
            old = analysis_candidates[0]
            new = analysis_candidates[-1]
            evo = await self.ai.analyze_evolution(
                old["code"], new["code"], context=local_path
            )
            evolution.append(evo)
        report["evolution_analyses"] = evolution

        # Generate insights
        all_patterns = set()
        for res in pattern_results:
            all_patterns.update(res.get("combined_patterns", []))

        pattern_dict = {}
        for pattern in all_patterns:
            count = sum(
                1
                for res in pattern_results
                if pattern in res.get("combined_patterns", [])
            )
            pattern_dict[pattern] = count

        insights_input = {
            "patterns": pattern_dict,
            "technologies": list(report["technologies"].get("languages", {}).keys()),
            "commits": len(commits),
        }
        report["insights"] = await self.generate_insights(insights_input)

        return report
