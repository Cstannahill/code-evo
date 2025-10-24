import os
import logging
import asyncio
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.services.git_service import GitService
from app.services.ai_service import AIService
from app.services.repository_service import RepositoryService
from app.services.pattern_service import PatternService
from app.services.ai_analysis_service import AIAnalysisService
from app.services.cache_service import cache_analysis_result
from app.utils.token_logger import log_analysis_run

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
            get_ai_analysis_service,
            get_incremental_analyzer,
        )

        self.git = get_git_service()
        self.ai = get_ai_service()

        # Initialize MongoDB services using singletons
        self.repository_service = get_repository_service()
        self.pattern_service = get_pattern_service()
        self.ai_analysis_service = get_ai_analysis_service()
        self.incremental_analyzer = get_incremental_analyzer()

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

    @cache_analysis_result(
        "repository", ttl_seconds=7200, tags=["analysis"]
    )  # 2 hour cache
    async def analyze_repository(
        self,
        repo_url: str,
        branch: str = "main",
        commit_limit: int = 100,
        candidate_limit: Optional[int] = 20,
        use_enhanced: bool = True,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clone the repository, extract history, and run AI analyses.
        Now supports enhanced analysis with superior pattern detection and insights.

        Returns a report dictionary with:
          - repo_info
          - technologies (enhanced if use_enhanced=True)
          - commits
          - patterns (enhanced if use_enhanced=True)
          - quality_metrics (enhanced if use_enhanced=True)
          - insights (enhanced if use_enhanced=True)
          - pattern_candidates (for saving to database)
        """
        # Track timing for token logging
        start_time = time.time()

        report: Dict[str, Any] = {}
        pattern_results = []
        quality_results = []
        security_results = []
        performance_results = []

        try:
            logger.info(
                f"🔄 Starting {'enhanced' if use_enhanced else 'standard'} repository analysis for {repo_url}"
            )

            # Clone and inspect
            logger.info(f"📥 Cloning repository {repo_url}...")
            repo = self.git.clone_repository(repo_url, branch)
            repo_path = repo.working_dir

            logger.info(f"🔍 Extracting repository information...")
            report["repo_info"] = self.git.get_repository_info(repo)

            # Get file list for enhanced analysis
            file_list = [
                str(item.path)
                for item in repo.head.commit.tree.traverse()
                if item.type == "blob"
            ]

            # Use enhanced analysis if requested
            if use_enhanced:
                logger.info("🚀 Running enhanced analysis with superior detection...")
                enhanced_results = await self.ai.enhanced_analyze_repository(
                    repo_path, file_list
                )

                # Merge enhanced results into report
                report.update(enhanced_results)

                # Still extract legacy technologies for compatibility
                report["technologies"] = report.get(
                    "technologies", self.git.extract_technologies(repo)
                )
            else:
                # Standard analysis
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
                self.ai.analyze_code_pattern(
                    c["code"], c["language"], user_id=user_id
                )
                for c in analysis_candidates
            ]
            quality_tasks = [
                self.ai.analyze_code_quality(
                    c["code"], c["language"], user_id=user_id
                )
                for c in analysis_candidates
            ]
            security_tasks = [
                self.ai.analyze_security(
                    c["code"], c.get("file_path", "unknown"), c["language"]
                )
                for c in analysis_candidates
            ]
            performance_tasks = [
                self.ai.analyze_performance(
                    c["code"], c.get("file_path", "unknown"), c["language"]
                )
                for c in analysis_candidates
            ]

            logger.info(
                f"⚡ Processing {len(pattern_tasks)} pattern, {len(quality_tasks)} quality, {len(security_tasks)} security, and {len(performance_tasks)} performance analyses..."
            )
            try:
                (
                    pattern_results,
                    quality_results,
                    security_results,
                    performance_results,
                ) = await asyncio.gather(
                    asyncio.gather(*pattern_tasks),
                    asyncio.gather(*quality_tasks),
                    asyncio.gather(*security_tasks),
                    asyncio.gather(*performance_tasks),
                )
                report["pattern_analyses"] = pattern_results
                report["quality_analyses"] = quality_results
                report["security_analyses"] = security_results
                report["performance_analyses"] = performance_results
                logger.info(f"✅ Completed AI analysis")
            except Exception as e:
                logger.warning(f"⚠️ AI analysis failed: {e}")
                report["pattern_analyses"] = []
                report["quality_analyses"] = []
                report["security_analyses"] = []
                report["performance_analyses"] = []

            # Evolution: compare first and last snippet if available
            logger.info(f"🔄 Analyzing code evolution...")
            evolution: List[Dict[str, Any]] = []
            try:
                if len(analysis_candidates) >= 2:
                    old = analysis_candidates[0]
                    new = analysis_candidates[-1]
                    evo = await self.ai.analyze_evolution(
                        old["code"],
                        new["code"],
                        context=repo_url,
                        user_id=user_id,
                    )
                    evolution.append(evo)
                    logger.info(f"📊 Evolution analysis completed")
            except Exception as e:
                logger.warning(f"⚠️ Evolution analysis failed: {e}")
            report["evolution_analyses"] = evolution

            # Architectural analysis
            logger.info(f"🏗️ Analyzing repository architecture...")
            try:
                architecture_analysis = await self.ai.analyze_architecture(
                    repo.working_dir,
                    [
                        c.get("file_path")
                        for c in analysis_candidates
                        if c.get("file_path")
                    ],
                )
                report["architecture_analysis"] = architecture_analysis
                logger.info(f"✅ Architecture analysis completed")
            except Exception as e:
                logger.warning(f"⚠️ Architecture analysis failed: {e}")
                report["architecture_analysis"] = {
                    "error": str(e),
                    "architectural_style": {"primary": "unknown", "confidence": 0.0},
                    "design_patterns": [],
                    "quality_metrics": {"overall_score": 50, "grade": "F"},
                }

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

            # Log token usage for full pipeline
            duration = time.time() - start_time
            snippets = [c.get("code", "") for c in analysis_candidates]
            task_counts = {
                "pattern": len(pattern_results),
                "quality": len(quality_results),
                "security": len(security_results),
                "performance": len(performance_results),
            }
            log_analysis_run(
                repo_url=repo_url,
                model_id=getattr(self.ai, "preferred_model", None),
                commit_count=len(commits),
                total_candidates=len(candidates),
                analyzed_candidates=len(analysis_candidates),
                snippets=snippets,
                task_counts=task_counts,
                duration_seconds=duration,
            )
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
                        detected_at=candidate.get("commit_date"),
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
        user_id: Optional[str] = None,
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
            self.ai.analyze_code_pattern(
                c["code"], c["language"], user_id=user_id
            )
            for c in analysis_candidates
        ]
        quality_tasks = [
            self.ai.analyze_code_quality(
                c["code"], c["language"], user_id=user_id
            )
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
                old["code"],
                new["code"],
                context=local_path,
                user_id=user_id,
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

    @cache_analysis_result(
        "incremental", ttl_seconds=1800, tags=["analysis"]
    )  # 30 minute cache
    async def analyze_repository_incremental(
        self,
        repo_url: str,
        branch: str = "main",
        commit_limit: int = 100,
        candidate_limit: Optional[int] = 20,
        force_full: bool = False,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform incremental analysis of repository, only analyzing changed files

        Args:
            repo_url: Repository URL
            branch: Git branch to analyze
            commit_limit: Maximum commits to analyze
            candidate_limit: Maximum candidates per analysis
            force_full: Force full analysis even if incremental is possible

        Returns:
            Analysis report dictionary
        """
        # Track timing for token logging
        start_time = time.time()

        report: Dict[str, Any] = {}

        try:
            logger.info(f"🔄 Starting incremental repository analysis for {repo_url}")

            # Clone and inspect
            logger.info(f"📥 Cloning repository {repo_url}...")
            repo = self.git.clone_repository(repo_url, branch)

            # Get current commit hash
            current_commit = repo.head.commit.hexsha
            logger.info(f"📝 Current commit: {current_commit[:8]}")

            # Check for incremental analysis possibility
            if not force_full:
                changes, should_full_reanalyze = (
                    self.incremental_analyzer.detect_changes(
                        repo.working_dir, current_commit
                    )
                )

                if not should_full_reanalyze and changes:
                    logger.info(
                        f"🚀 Performing incremental analysis of {len(changes)} changes"
                    )
                    return await self._perform_incremental_analysis(
                        repo,
                        repo_url,
                        branch,
                        changes,
                        current_commit,
                        start_time,
                        user_id=user_id,
                    )
                elif not changes:
                    logger.info("✅ No changes detected since last analysis")
                    # Return cached results if available
                    previous_snapshot = self.incremental_analyzer.snapshots_cache.get(
                        repo.working_dir
                    )
                    if previous_snapshot and previous_snapshot.analysis_results:
                        report = previous_snapshot.analysis_results.copy()
                        report["incremental_analysis"] = {
                            "no_changes": True,
                            "cached_results": True,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        return report

            # Fall back to full analysis
            logger.info("🔄 Falling back to full analysis")
            full_report = await self.analyze_repository(
                repo_url,
                branch,
                commit_limit,
                candidate_limit,
                user_id=user_id,
            )

            # Create snapshot for future incremental analysis
            self.incremental_analyzer.create_snapshot(
                repo.working_dir, current_commit, full_report
            )

            return full_report

        except Exception as e:
            logger.error(f"💥 Incremental analysis failed: {e}")
            report["error"] = str(e)
            return report
        finally:
            # Cleanup temp dirs
            try:
                logger.info(f"🧹 Cleaning up temporary files...")
                self.git.cleanup()
            except Exception as cleanup_err:
                logger.warning(f"⚠️ Cleanup error: {cleanup_err}")

    async def _perform_incremental_analysis(
        self,
        repo,
        repo_url: str,
        branch: str,
        changes: List,
        current_commit: str,
        start_time: float,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform the actual incremental analysis with token logging

        Args:
            repo: Git repository object
            repo_url: Repository URL
            branch: Git branch
            changes: List of detected changes
            current_commit: Current commit hash
            start_time: Analysis start time for duration calculation

        Returns:
            Analysis report
        """
        try:
            # Get previous analysis results
            previous_snapshot = self.incremental_analyzer.snapshots_cache.get(
                repo.working_dir
            )
            if not previous_snapshot:
                logger.warning(
                    "No previous snapshot found, falling back to full analysis"
                )
                return await self.analyze_repository(
                    repo_url,
                    branch,
                    user_id=user_id,
                )

            # Get basic repository info (may have changed)
            report = {}
            report["repo_info"] = self.git.get_repository_info(repo)
            report["technologies"] = self.git.extract_technologies(repo)

            # Get incremental candidates for changed files only
            incremental_candidates = (
                self.incremental_analyzer.get_incremental_candidates(
                    changes, repo.working_dir
                )
            )

            if not incremental_candidates:
                logger.info("No incremental candidates found")
                # Return previous results with update timestamp
                report = previous_snapshot.analysis_results.copy()
                report["incremental_analysis"] = {
                    "changes_detected": len(changes),
                    "no_analyzable_changes": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                return report

            logger.info(
                f"🤖 Running incremental AI analysis on {len(incremental_candidates)} changed files..."
            )

            # Run AI analyses on changed files only
            pattern_tasks = [
                self.ai.analyze_code_pattern(
                    c["code"], c["language"], user_id=user_id
                )
                for c in incremental_candidates
            ]
            quality_tasks = [
                self.ai.analyze_code_quality(
                    c["code"], c["language"], user_id=user_id
                )
                for c in incremental_candidates
            ]
            security_tasks = [
                self.ai.analyze_security(
                    c["code"], c.get("file_path", "unknown"), c["language"]
                )
                for c in incremental_candidates
            ]
            performance_tasks = [
                self.ai.analyze_performance(
                    c["code"], c.get("file_path", "unknown"), c["language"]
                )
                for c in incremental_candidates
            ]

            pattern_results, quality_results, security_results, performance_results = (
                await asyncio.gather(
                    asyncio.gather(*pattern_tasks),
                    asyncio.gather(*quality_tasks),
                    asyncio.gather(*security_tasks),
                    asyncio.gather(*performance_tasks),
                )
            )

            # Package incremental results
            incremental_results = {
                "pattern_analyses": pattern_results,
                "quality_analyses": quality_results,
                "security_analyses": security_results,
                "performance_analyses": performance_results,
                "pattern_candidates": incremental_candidates,
            }

            # Merge with previous results
            merged_report = self.incremental_analyzer.merge_analysis_results(
                previous_snapshot.analysis_results, incremental_results, changes
            )

            # Update with current repository info
            merged_report.update(report)

            # Log token usage for incremental pipeline
            duration = time.time() - start_time
            snippets = [c.get("code", "") for c in incremental_candidates]
            task_counts = {
                "pattern": len(pattern_results),
                "quality": len(quality_results),
                "security": len(security_results),
                "performance": len(performance_results),
            }
            log_analysis_run(
                repo_url=repo_url + " (incremental)",
                model_id=getattr(self.ai, "preferred_model", None),
                commit_count=len(changes),
                total_candidates=len(incremental_candidates),
                analyzed_candidates=len(incremental_candidates),
                snippets=snippets,
                task_counts=task_counts,
                duration_seconds=duration,
            )

            # Create new snapshot
            self.incremental_analyzer.create_snapshot(
                repo.working_dir, current_commit, merged_report
            )

            # Persist incremental results to MongoDB
            await self._persist_analysis_results(repo_url, branch, merged_report)

            logger.info(f"✅ Incremental analysis completed for {len(changes)} changes")
            return merged_report

        except Exception as e:
            logger.error(f"Error in incremental analysis: {e}")
            raise
