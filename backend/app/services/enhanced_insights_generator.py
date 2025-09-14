# Enhanced AI Insights Generator
"""
Advanced AI insights generation system that provides:
- Comprehensive code quality analysis
- Detailed technology stack insights
- Performance and security recommendations
- Architecture assessment and suggestions
- Trend analysis and evolution insights
- Actionable recommendations with priorities
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """Represents a generated insight"""

    type: str  # recommendation, achievement, trend, warning, improvement
    title: str
    description: str
    category: str
    priority: str  # low, medium, high, critical
    confidence: float
    data: Dict[str, Any]
    actionable_items: List[str]
    impact_score: float
    effort_score: float  # 1-5 scale
    tags: List[str]


class EnhancedInsightsGenerator:
    """
    Advanced insights generator with comprehensive analysis,
    prioritization, and actionable recommendations.
    """

    def __init__(self):
        """Initialize with comprehensive analysis capabilities"""
        self.insight_templates = self._load_insight_templates()
        self.quality_metrics = self._load_quality_metrics()
        self.technology_assessments = self._load_technology_assessments()
        self.performance_benchmarks = self._load_performance_benchmarks()

        logger.info("EnhancedInsightsGenerator initialized")

    def _load_insight_templates(self) -> Dict[str, Dict]:
        """Load insight generation templates"""
        return {
            "code_quality": {
                "high_quality": {
                    "title": "Excellent Code Quality",
                    "description": "Your codebase demonstrates exceptional quality with {quality_score}% score, minimal technical debt, and strong adherence to best practices.",
                    "category": "achievement",
                    "priority": "low",
                    "confidence_threshold": 0.8,
                },
                "moderate_quality": {
                    "title": "Good Code Quality with Room for Improvement",
                    "description": "Your codebase shows solid quality at {quality_score}% but has opportunities for improvement in {improvement_areas}.",
                    "category": "recommendation",
                    "priority": "medium",
                    "confidence_threshold": 0.6,
                },
                "low_quality": {
                    "title": "Code Quality Needs Attention",
                    "description": "Your codebase quality score of {quality_score}% indicates significant issues that should be addressed, particularly in {critical_areas}.",
                    "category": "improvement",
                    "priority": "high",
                    "confidence_threshold": 0.4,
                },
            },
            "technology_stack": {
                "modern_stack": {
                    "title": "Modern Technology Stack",
                    "description": "Your project uses a contemporary technology stack with {tech_count} technologies, including {modern_techs}, demonstrating good technology choices.",
                    "category": "achievement",
                    "priority": "low",
                },
                "diverse_stack": {
                    "title": "Diverse Technology Portfolio",
                    "description": "Your project leverages {tech_count} technologies across {categories} categories, showing a polyglot approach to development.",
                    "category": "trend",
                    "priority": "medium",
                },
                "outdated_tech": {
                    "title": "Outdated Technology Usage",
                    "description": "Some technologies in your stack may be outdated: {outdated_techs}. Consider upgrading to more modern alternatives.",
                    "category": "recommendation",
                    "priority": "medium",
                },
            },
            "architecture": {
                "well_architected": {
                    "title": "Well-Architected System",
                    "description": "Your codebase demonstrates strong architectural patterns including {patterns}, indicating good system design.",
                    "category": "achievement",
                    "priority": "low",
                },
                "architectural_debt": {
                    "title": "Architectural Technical Debt",
                    "description": "Your system shows signs of architectural debt with {issues}. Consider refactoring to improve maintainability.",
                    "category": "improvement",
                    "priority": "high",
                },
            },
            "performance": {
                "optimized": {
                    "title": "Performance Optimized",
                    "description": "Your codebase shows good performance practices with {optimizations} implemented.",
                    "category": "achievement",
                    "priority": "low",
                },
                "performance_issues": {
                    "title": "Performance Optimization Opportunities",
                    "description": "Several performance issues detected: {issues}. Addressing these could significantly improve application performance.",
                    "category": "recommendation",
                    "priority": "high",
                },
            },
            "security": {
                "secure_practices": {
                    "title": "Strong Security Practices",
                    "description": "Your codebase demonstrates good security practices with {security_measures} implemented.",
                    "category": "achievement",
                    "priority": "low",
                },
                "security_vulnerabilities": {
                    "title": "Security Vulnerabilities Detected",
                    "description": "Critical security issues found: {vulnerabilities}. Immediate attention required to prevent potential breaches.",
                    "category": "warning",
                    "priority": "critical",
                },
            },
        }

    def _load_quality_metrics(self) -> Dict[str, Dict]:
        """Load code quality assessment metrics"""
        return {
            "complexity": {
                "low": {"score": 90, "description": "Simple, easy to understand code"},
                "medium": {
                    "score": 70,
                    "description": "Moderately complex code with some areas for improvement",
                },
                "high": {
                    "score": 50,
                    "description": "Complex code that may be difficult to maintain",
                },
                "very_high": {
                    "score": 30,
                    "description": "Very complex code requiring significant refactoring",
                },
            },
            "maintainability": {
                "excellent": {
                    "score": 95,
                    "description": "Highly maintainable code with clear structure",
                },
                "good": {
                    "score": 80,
                    "description": "Well-structured code with minor maintainability issues",
                },
                "fair": {
                    "score": 60,
                    "description": "Code with some maintainability concerns",
                },
                "poor": {
                    "score": 40,
                    "description": "Code with significant maintainability issues",
                },
            },
            "testability": {
                "high": {
                    "score": 90,
                    "description": "Code is highly testable with good separation of concerns",
                },
                "medium": {
                    "score": 70,
                    "description": "Code has moderate testability with some improvements needed",
                },
                "low": {
                    "score": 50,
                    "description": "Code has low testability requiring refactoring",
                },
            },
        }

    def _load_technology_assessments(self) -> Dict[str, Dict]:
        """Load technology assessment criteria"""
        return {
            "modern": {
                "frontend": [
                    "React",
                    "Vue.js",
                    "Angular",
                    "Svelte",
                    "Next.js",
                    "Nuxt.js",
                ],
                "backend": ["FastAPI", "Express.js", "Spring Boot", "Django", "NestJS"],
                "mobile": ["React Native", "Flutter", "Ionic"],
                "tools": ["Vite", "Webpack", "TypeScript", "ESLint", "Prettier"],
            },
            "outdated": {
                "frontend": ["jQuery", "AngularJS", "Backbone.js", "Knockout.js"],
                "backend": ["PHP 5", "ASP.NET Web Forms", "Struts", "EJB 2.x"],
                "tools": ["Grunt", "Gulp", "Bower", "RequireJS"],
            },
            "emerging": {
                "frontend": ["SolidJS", "Qwik", "SvelteKit", "Astro"],
                "backend": ["Deno", "Bun", "Cloudflare Workers"],
                "tools": ["Turborepo", "Nx", "Rome", "SWC"],
            },
        }

    def _load_performance_benchmarks(self) -> Dict[str, Dict]:
        """Load performance assessment benchmarks"""
        return {
            "bundle_size": {
                "excellent": {
                    "threshold": 100,
                    "description": "Bundle size under 100KB",
                },
                "good": {"threshold": 500, "description": "Bundle size under 500KB"},
                "fair": {"threshold": 1000, "description": "Bundle size under 1MB"},
                "poor": {
                    "threshold": float("inf"),
                    "description": "Bundle size over 1MB",
                },
            },
            "complexity": {
                "low": {"threshold": 10, "description": "Low cyclomatic complexity"},
                "medium": {
                    "threshold": 20,
                    "description": "Medium cyclomatic complexity",
                },
                "high": {"threshold": 50, "description": "High cyclomatic complexity"},
                "very_high": {
                    "threshold": float("inf"),
                    "description": "Very high cyclomatic complexity",
                },
            },
        }

    def generate_comprehensive_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Insight]:
        """
        Generate comprehensive insights from analysis data

        Args:
            analysis_data: Complete analysis results including patterns, technologies, quality metrics

        Returns:
            List of prioritized insights
        """
        insights = []

        try:
            # Normalize input to avoid shape-related errors (e.g., list has no attribute 'get')
            normalized = self._normalize_analysis_data(analysis_data)

            # Generate insights for each category using normalized data
            insights.extend(self._generate_quality_insights(normalized))
            insights.extend(self._generate_technology_insights(normalized))
            insights.extend(self._generate_architecture_insights(normalized))
            insights.extend(self._generate_performance_insights(normalized))
            insights.extend(self._generate_security_insights(normalized))
            insights.extend(self._generate_trend_insights(normalized))
            insights.extend(self._generate_evolution_insights(normalized))

            # Prioritize and rank insights
            insights = self._prioritize_insights(insights)

            logger.info(f"Generated {len(insights)} comprehensive insights")
            return insights

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []

    def _normalize_analysis_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize varied input shapes to a consistent schema expected by generators.

        Returns dict with keys:
          - patterns: Dict[str, Any]
          - technologies: Dict[str, List[str]] with languages/frameworks/tools
          - commits_list: Optional[List[Any]]
          - commit_count: int
          - quality: Dict with at least overall_score
          - summary: original summary if present
        """
        normalized: Dict[str, Any] = {}

        # Patterns can be a dict of name->data, or a repo summary with 'patterns' list, or a list of names
        patterns_in = analysis_data.get("patterns", {})
        patterns_out: Dict[str, Any] = {}
        try:
            if isinstance(patterns_in, dict):
                if "patterns" in patterns_in and isinstance(
                    patterns_in["patterns"], list
                ):
                    # repository patterns summary structure
                    for item in patterns_in.get("patterns", []):
                        name = None
                        if isinstance(item, dict):
                            # try nested pattern.name then fallback to id
                            pat = (
                                item.get("pattern")
                                if isinstance(item.get("pattern"), dict)
                                else None
                            )
                            name = (pat or {}).get("name") if pat else None
                            if not name:
                                name = str(item.get("pattern_id", "unknown"))
                        else:
                            name = str(item)
                        patterns_out[name] = item
                else:
                    patterns_out = patterns_in
            elif isinstance(patterns_in, list):
                for item in patterns_in:
                    if isinstance(item, str):
                        patterns_out[item] = {"occurrences": 1}
                    elif isinstance(item, dict):
                        name = (
                            item.get("name")
                            or (item.get("pattern") or {}).get("name")
                            or str(item.get("pattern_id", "unknown"))
                        )
                        patterns_out[name] = item
        except Exception as e:
            logger.debug(f"Pattern normalization warning: {e}")
            patterns_out = {}
        normalized["patterns"] = patterns_out

        # Technologies can be list (languages) or dict with languages/frameworks/tools
        technologies_in = analysis_data.get("technologies", {})
        technologies_out: Dict[str, List[str]] = {
            "languages": [],
            "frameworks": [],
            "tools": [],
        }
        try:
            if isinstance(technologies_in, list):
                technologies_out["languages"] = [str(t) for t in technologies_in]
            elif isinstance(technologies_in, dict):
                langs = technologies_in.get("languages", [])
                if isinstance(langs, dict):
                    technologies_out["languages"] = list(langs.keys())
                elif isinstance(langs, list):
                    technologies_out["languages"] = [str(t) for t in langs]
                frameworks = technologies_in.get("frameworks", [])
                tools = technologies_in.get("tools", [])
                libraries = technologies_in.get("libraries", [])
                technologies_out["frameworks"] = [
                    str(x)
                    for x in (
                        list(frameworks)
                        if not isinstance(frameworks, list)
                        else frameworks
                    )
                ]
                tools_list = list(tools) if not isinstance(tools, list) else tools
                libs_list = (
                    list(libraries) if not isinstance(libraries, list) else libraries
                )
                technologies_out["tools"] = [str(x) for x in (tools_list + libs_list)]
        except Exception as e:
            logger.debug(f"Technology normalization warning: {e}")
        normalized["technologies"] = technologies_out

        # Commits can be int count, list of commits, or dict with total_commits
        commits_in = analysis_data.get("commits", [])
        commit_count = 0
        commits_list: Optional[List[Any]] = None
        try:
            if isinstance(commits_in, list):
                commits_list = commits_in
                commit_count = len(commits_in)
            elif isinstance(commits_in, int):
                commit_count = commits_in
            elif isinstance(commits_in, dict):
                commit_count = int(commits_in.get("total_commits", 0))
                if isinstance(commits_in.get("items"), list):
                    commits_list = commits_in.get("items")
        except Exception:
            commit_count = 0
            commits_list = None
        normalized["commit_count"] = commit_count
        normalized["commits_list"] = commits_list

        # Quality metrics may come from 'quality_report' object or 'quality_metrics' dict
        quality: Dict[str, Any] = {}
        qr = analysis_data.get("quality_report")
        qm = analysis_data.get("quality_metrics")
        try:
            if qr is not None:
                overall = getattr(qr, "overall_score", None)
                if overall is not None:
                    quality["overall_score"] = float(overall)
                mi = getattr(qr, "maintainability_index", None)
                if mi is not None:
                    quality["maintainability_index"] = float(mi)
                td = getattr(qr, "technical_debt_score", None)
                if td is not None:
                    quality["technical_debt_score"] = float(td)
                ts = getattr(qr, "testability_score", None)
                if ts is not None:
                    quality["testability_score"] = float(ts)
                # Include summary-derived signals if present on QualityReport
                try:
                    qr_summary = getattr(qr, "summary", None)
                    if isinstance(qr_summary, dict):
                        if "documentation_coverage" in qr_summary:
                            quality["documentation_coverage"] = float(
                                qr_summary.get("documentation_coverage", 0)
                            )
                        if "style_consistency" in qr_summary:
                            quality["style_consistency"] = float(
                                qr_summary.get("style_consistency", 0)
                            )
                except Exception:
                    pass
        except Exception:
            pass
        if isinstance(qm, dict):
            try:
                quality["overall_score"] = float(
                    qm.get("overall_score", quality.get("overall_score", 0.0))
                )
            except Exception:
                pass
        normalized["quality"] = quality
        normalized["summary"] = analysis_data.get("summary", {})

        # Keep some raw shape info for debugging
        normalized["_raw_types"] = {
            "patterns": type(patterns_in).__name__,
            "technologies": type(technologies_in).__name__,
            "commits": type(commits_in).__name__,
        }

        return normalized

    def _generate_quality_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Insight]:
        """Generate code quality insights"""
        insights: List[Insight] = []

        # Extract quality metrics (prefer normalized quality.overall_score; fallback to summary.quality_score)
        quality_score = analysis_data.get("quality", {}).get(
            "overall_score", 0
        ) or analysis_data.get("summary", {}).get("quality_score", 0)
        complexity_dist = analysis_data.get("summary", {}).get(
            "complexity_distribution", {}
        )
        antipatterns = analysis_data.get("summary", {}).get("antipatterns_detected", 0)
        maintainability_index = analysis_data.get("quality", {}).get(
            "maintainability_index"
        )
        technical_debt_score = analysis_data.get("quality", {}).get(
            "technical_debt_score"
        )
        testability_score = analysis_data.get("quality", {}).get("testability_score")
        documentation_coverage = analysis_data.get("quality", {}).get(
            "documentation_coverage"
        ) or analysis_data.get("summary", {}).get("documentation_coverage")
        style_consistency = analysis_data.get("quality", {}).get(
            "style_consistency"
        ) or analysis_data.get("summary", {}).get("style_consistency")

        # Quality score insight
        if quality_score >= 90:
            insights.append(
                Insight(
                    type="achievement",
                    title="Excellent Code Quality",
                    description=f"Outstanding code quality score of {quality_score}% with minimal technical debt and strong adherence to best practices.",
                    category="code_quality",
                    priority="low",
                    confidence=0.9,
                    data={"quality_score": quality_score, "antipatterns": antipatterns},
                    actionable_items=[
                        "Maintain current quality standards",
                        "Continue code reviews",
                    ],
                    impact_score=0.3,
                    effort_score=1.0,
                    tags=["quality", "achievement", "maintenance"],
                )
            )
        elif quality_score >= 70:
            insights.append(
                Insight(
                    type="recommendation",
                    title="Good Code Quality with Improvement Opportunities",
                    description=f"Solid code quality at {quality_score}% with {antipatterns} antipatterns detected. Focus on reducing complexity and improving maintainability.",
                    category="code_quality",
                    priority="medium",
                    confidence=0.8,
                    data={"quality_score": quality_score, "antipatterns": antipatterns},
                    actionable_items=[
                        "Refactor complex functions",
                        "Add unit tests for uncovered areas",
                        "Implement code review process",
                    ],
                    impact_score=0.6,
                    effort_score=3.0,
                    tags=["quality", "improvement", "refactoring"],
                )
            )
        else:
            insights.append(
                Insight(
                    type="improvement",
                    title="Code Quality Needs Immediate Attention",
                    description=f"Code quality score of {quality_score}% indicates significant issues. {antipatterns} antipatterns detected require urgent attention.",
                    category="code_quality",
                    priority="high",
                    confidence=0.9,
                    data={"quality_score": quality_score, "antipatterns": antipatterns},
                    actionable_items=[
                        "Conduct comprehensive code review",
                        "Refactor critical antipatterns",
                        "Implement automated testing",
                        "Establish coding standards",
                    ],
                    impact_score=0.9,
                    effort_score=4.0,
                    tags=["quality", "critical", "refactoring", "standards"],
                )
            )

        # Complexity insights
        if complexity_dist.get("advanced", 0) > complexity_dist.get("simple", 0):
            insights.append(
                Insight(
                    type="recommendation",
                    title="High Code Complexity Detected",
                    description=f"Your codebase has more advanced complexity ({complexity_dist.get('advanced', 0)}) than simple patterns ({complexity_dist.get('simple', 0)}). Consider simplifying complex areas.",
                    category="complexity",
                    priority="medium",
                    confidence=0.7,
                    data=complexity_dist,
                    actionable_items=[
                        "Break down complex functions",
                        "Extract reusable components",
                        "Apply design patterns for simplification",
                    ],
                    impact_score=0.7,
                    effort_score=3.0,
                    tags=["complexity", "refactoring", "simplification"],
                )
            )

        # Maintainability insights
        if isinstance(maintainability_index, (int, float)):
            if maintainability_index >= 80:
                insights.append(
                    Insight(
                        type="achievement",
                        title="High Maintainability",
                        description=f"Maintainability index is strong at {maintainability_index:.1f}. Code structure supports long-term evolution.",
                        category="maintainability",
                        priority="low",
                        confidence=0.8,
                        data={"maintainability_index": maintainability_index},
                        actionable_items=[
                            "Keep modules small",
                            "Maintain clear interfaces",
                        ],
                        impact_score=0.3,
                        effort_score=1.0,
                        tags=["maintainability", "architecture"],
                    )
                )
            elif maintainability_index < 60:
                insights.append(
                    Insight(
                        type="improvement",
                        title="Maintainability Needs Work",
                        description=f"Maintainability index at {maintainability_index:.1f} suggests refactoring opportunities to improve structure and readability.",
                        category="maintainability",
                        priority="high",
                        confidence=0.85,
                        data={"maintainability_index": maintainability_index},
                        actionable_items=[
                            "Refactor large modules",
                            "Reduce coupling and improve cohesion",
                            "Introduce module boundaries",
                        ],
                        impact_score=0.8,
                        effort_score=4.0,
                        tags=["maintainability", "refactoring"],
                    )
                )

        # Technical debt insights
        if isinstance(technical_debt_score, (int, float)):
            if technical_debt_score > 60:
                insights.append(
                    Insight(
                        type="warning",
                        title="High Technical Debt",
                        description=f"Technical debt score {technical_debt_score:.1f} indicates significant quality risks. Prioritize remediation.",
                        category="debt",
                        priority="critical",
                        confidence=0.9,
                        data={"technical_debt_score": technical_debt_score},
                        actionable_items=[
                            "Create a refactoring backlog",
                            "Schedule debt sprints",
                            "Add guardrail tests before refactors",
                        ],
                        impact_score=1.0,
                        effort_score=5.0,
                        tags=["debt", "risk", "refactoring"],
                    )
                )
            elif technical_debt_score > 30:
                insights.append(
                    Insight(
                        type="recommendation",
                        title="Manageable Technical Debt",
                        description=f"Technical debt score {technical_debt_score:.1f}. Address hotspots proactively to avoid future slowdown.",
                        category="debt",
                        priority="medium",
                        confidence=0.8,
                        data={"technical_debt_score": technical_debt_score},
                        actionable_items=[
                            "Target biggest debt hotspots",
                            "Enforce code review standards",
                            "Track debt remediation KPI",
                        ],
                        impact_score=0.7,
                        effort_score=3.0,
                        tags=["debt", "process"],
                    )
                )

        # Testability insights
        if isinstance(testability_score, (int, float)):
            if testability_score >= 80:
                insights.append(
                    Insight(
                        type="achievement",
                        title="Highly Testable Code",
                        description=f"Testability score {testability_score:.1f}. Good separation of concerns and function sizes.",
                        category="testability",
                        priority="low",
                        confidence=0.75,
                        data={"testability_score": testability_score},
                        actionable_items=[
                            "Maintain unit test coverage",
                            "Keep functions focused",
                        ],
                        impact_score=0.3,
                        effort_score=1.0,
                        tags=["testability", "testing"],
                    )
                )
            elif testability_score < 60:
                insights.append(
                    Insight(
                        type="recommendation",
                        title="Improve Testability",
                        description=f"Testability score {testability_score:.1f} suggests harder-to-test modules. Favor smaller functions and dependency injection.",
                        category="testability",
                        priority="medium",
                        confidence=0.8,
                        data={"testability_score": testability_score},
                        actionable_items=[
                            "Extract pure functions",
                            "Reduce parameter counts",
                            "Use interfaces for external deps",
                        ],
                        impact_score=0.6,
                        effort_score=3.0,
                        tags=["testability", "refactoring"],
                    )
                )

        # Documentation and style insights
        if isinstance(documentation_coverage, (int, float)):
            if documentation_coverage >= 80:
                insights.append(
                    Insight(
                        type="achievement",
                        title="Strong Documentation Coverage",
                        description=f"Documentation coverage is {documentation_coverage:.1f}%. Team can onboard and evolve faster.",
                        category="documentation",
                        priority="low",
                        confidence=0.7,
                        data={"documentation_coverage": documentation_coverage},
                        actionable_items=[
                            "Keep docs current",
                            "Document complex modules",
                        ],
                        impact_score=0.3,
                        effort_score=1.0,
                        tags=["documentation", "knowledge"],
                    )
                )
            elif documentation_coverage < 50:
                insights.append(
                    Insight(
                        type="recommendation",
                        title="Increase Documentation",
                        description=f"Low documentation coverage at {documentation_coverage:.1f}%. Add docstrings, comments, and READMEs for complex areas.",
                        category="documentation",
                        priority="medium",
                        confidence=0.8,
                        data={"documentation_coverage": documentation_coverage},
                        actionable_items=[
                            "Add docstrings to public APIs",
                            "Document complex algorithms",
                            "Adopt documentation standards",
                        ],
                        impact_score=0.5,
                        effort_score=2.0,
                        tags=["documentation", "standards"],
                    )
                )

        if isinstance(style_consistency, (int, float)) and style_consistency < 70:
            insights.append(
                Insight(
                    type="recommendation",
                    title="Improve Style Consistency",
                    description=f"Style consistency score {style_consistency:.1f}. Enforce linters/formatters and naming conventions.",
                    category="style",
                    priority="low",
                    confidence=0.75,
                    data={"style_consistency": style_consistency},
                    actionable_items=[
                        "Enable linters/formatters",
                        "Adopt style guide",
                        "Automate pre-commit checks",
                    ],
                    impact_score=0.4,
                    effort_score=2.0,
                    tags=["style", "linting", "formatting"],
                )
            )

        return insights

    def _generate_technology_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Insight]:
        """Generate technology stack insights"""
        insights: List[Insight] = []

        technologies = analysis_data.get(
            "technologies", {"languages": [], "frameworks": [], "tools": []}
        )
        langs = technologies.get("languages", [])
        lang_count = (
            len(langs)
            if isinstance(langs, list)
            else len(list(langs.keys())) if isinstance(langs, dict) else 0
        )
        tech_count = lang_count + len(technologies.get("frameworks", []))

        # Technology diversity insight
        if tech_count > 10:
            insights.append(
                Insight(
                    type="trend",
                    title="Diverse Technology Portfolio",
                    description=f"Your project leverages {tech_count} technologies, demonstrating a modern, polyglot approach to development with good technology diversity.",
                    category="technology",
                    priority="low",
                    confidence=0.8,
                    data={"tech_count": tech_count, "technologies": technologies},
                    actionable_items=[
                        "Maintain technology documentation",
                        "Ensure team training",
                    ],
                    impact_score=0.4,
                    effort_score=2.0,
                    tags=["technology", "diversity", "modern"],
                )
            )
        elif tech_count < 3:
            insights.append(
                Insight(
                    type="recommendation",
                    title="Limited Technology Stack",
                    description=f"Your project uses only {tech_count} technologies. Consider expanding your stack to leverage modern tools and frameworks.",
                    category="technology",
                    priority="medium",
                    confidence=0.7,
                    data={"tech_count": tech_count, "technologies": technologies},
                    actionable_items=[
                        "Evaluate modern frameworks",
                        "Consider build tools and linters",
                        "Assess testing frameworks",
                    ],
                    impact_score=0.6,
                    effort_score=3.0,
                    tags=["technology", "expansion", "modernization"],
                )
            )

        # Modern technology assessment
        modern_techs = self._assess_modern_technologies(technologies)
        outdated_techs = self._assess_outdated_technologies(technologies)

        if modern_techs:
            insights.append(
                Insight(
                    type="achievement",
                    title="Modern Technology Stack",
                    description=f"Your project uses contemporary technologies including {', '.join(modern_techs[:3])}, demonstrating excellent technology choices.",
                    category="technology",
                    priority="low",
                    confidence=0.8,
                    data={"modern_techs": modern_techs},
                    actionable_items=[
                        "Stay updated with latest versions",
                        "Monitor for security updates",
                    ],
                    impact_score=0.3,
                    effort_score=1.0,
                    tags=["technology", "modern", "achievement"],
                )
            )

        if outdated_techs:
            insights.append(
                Insight(
                    type="recommendation",
                    title="Outdated Technology Usage",
                    description=f"Consider upgrading outdated technologies: {', '.join(outdated_techs[:3])}. Modern alternatives offer better security, performance, and maintainability.",
                    category="technology",
                    priority="medium",
                    confidence=0.8,
                    data={"outdated_techs": outdated_techs},
                    actionable_items=[
                        "Plan technology migration roadmap",
                        "Research modern alternatives",
                        "Allocate resources for upgrades",
                    ],
                    impact_score=0.7,
                    effort_score=4.0,
                    tags=["technology", "upgrade", "modernization"],
                )
            )

        return insights

    def _generate_architecture_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Insight]:
        """Generate architecture insights"""
        insights = []

        patterns = analysis_data.get("patterns", {})
        design_patterns = [
            p
            for p in patterns.keys()
            if any(
                cat in p.lower()
                for cat in ["singleton", "factory", "observer", "strategy"]
            )
        ]

        if len(design_patterns) >= 3:
            insights.append(
                Insight(
                    type="achievement",
                    title="Well-Architected System",
                    description=f"Your codebase demonstrates strong architectural patterns including {', '.join(design_patterns[:3])}, indicating excellent system design.",
                    category="architecture",
                    priority="low",
                    confidence=0.8,
                    data={"design_patterns": design_patterns},
                    actionable_items=[
                        "Document architectural decisions",
                        "Share patterns across team",
                    ],
                    impact_score=0.3,
                    effort_score=1.0,
                    tags=["architecture", "patterns", "achievement"],
                )
            )

        # Architectural debt detection
        antipatterns = [
            p
            for p in patterns.keys()
            if "antipattern" in p.lower() or "smell" in p.lower()
        ]
        if antipatterns:
            insights.append(
                Insight(
                    type="improvement",
                    title="Architectural Technical Debt",
                    description=f"Your system shows signs of architectural debt with {len(antipatterns)} antipatterns detected. Consider refactoring to improve maintainability.",
                    category="architecture",
                    priority="high",
                    confidence=0.8,
                    data={"antipatterns": antipatterns},
                    actionable_items=[
                        "Prioritize antipattern refactoring",
                        "Implement architectural reviews",
                        "Establish coding standards",
                    ],
                    impact_score=0.8,
                    effort_score=4.0,
                    tags=["architecture", "debt", "refactoring"],
                )
            )

        return insights

    def _generate_performance_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Insight]:
        """Generate performance insights"""
        insights = []

        patterns = analysis_data.get("patterns", {})
        performance_patterns = [
            p
            for p in patterns.keys()
            if any(
                perf in p.lower() for perf in ["lazy", "memo", "cache", "optimization"]
            )
        ]
        performance_issues = [
            p
            for p in patterns.keys()
            if any(
                issue in p.lower()
                for issue in ["n_plus_one", "inefficient", "bottleneck"]
            )
        ]

        if performance_patterns:
            insights.append(
                Insight(
                    type="achievement",
                    title="Performance Optimizations Implemented",
                    description=f"Your codebase shows good performance practices with {len(performance_patterns)} optimization patterns implemented.",
                    category="performance",
                    priority="low",
                    confidence=0.8,
                    data={"performance_patterns": performance_patterns},
                    actionable_items=[
                        "Monitor performance metrics",
                        "Continue optimization efforts",
                    ],
                    impact_score=0.3,
                    effort_score=1.0,
                    tags=["performance", "optimization", "achievement"],
                )
            )

        if performance_issues:
            insights.append(
                Insight(
                    type="recommendation",
                    title="Performance Optimization Opportunities",
                    description=f"Several performance issues detected: {', '.join(performance_issues[:3])}. Addressing these could significantly improve application performance.",
                    category="performance",
                    priority="high",
                    confidence=0.8,
                    data={"performance_issues": performance_issues},
                    actionable_items=[
                        "Profile application performance",
                        "Implement database query optimization",
                        "Add performance monitoring",
                        "Optimize critical code paths",
                    ],
                    impact_score=0.8,
                    effort_score=3.0,
                    tags=["performance", "optimization", "bottlenecks"],
                )
            )

        return insights

    def _generate_security_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Insight]:
        """Generate security insights"""
        insights = []

        patterns = analysis_data.get("patterns", {})
        security_patterns = [
            p
            for p in patterns.keys()
            if any(
                sec in p.lower()
                for sec in ["validation", "authentication", "encryption", "secure"]
            )
        ]
        security_issues = [
            p
            for p in patterns.keys()
            if any(
                issue in p.lower()
                for issue in ["injection", "xss", "hardcoded", "vulnerability"]
            )
        ]

        if security_patterns:
            insights.append(
                Insight(
                    type="achievement",
                    title="Strong Security Practices",
                    description=f"Your codebase demonstrates good security practices with {len(security_patterns)} security patterns implemented.",
                    category="security",
                    priority="low",
                    confidence=0.8,
                    data={"security_patterns": security_patterns},
                    actionable_items=[
                        "Maintain security standards",
                        "Regular security audits",
                    ],
                    impact_score=0.3,
                    effort_score=1.0,
                    tags=["security", "practices", "achievement"],
                )
            )

        if security_issues:
            insights.append(
                Insight(
                    type="warning",
                    title="Security Vulnerabilities Detected",
                    description=f"Critical security issues found: {', '.join(security_issues[:3])}. Immediate attention required to prevent potential breaches.",
                    category="security",
                    priority="critical",
                    confidence=0.9,
                    data={"security_issues": security_issues},
                    actionable_items=[
                        "Immediate security audit",
                        "Fix identified vulnerabilities",
                        "Implement security testing",
                        "Update security policies",
                    ],
                    impact_score=1.0,
                    effort_score=5.0,
                    tags=["security", "vulnerability", "critical", "urgent"],
                )
            )

        return insights

    def _generate_trend_insights(self, analysis_data: Dict[str, Any]) -> List[Insight]:
        """Generate trend analysis insights"""
        insights = []

        patterns = analysis_data.get("patterns", {})
        modern_patterns = [
            p
            for p in patterns.keys()
            if any(
                modern in p.lower()
                for modern in ["react", "vue", "async", "functional", "microservice"]
            )
        ]

        if modern_patterns:
            insights.append(
                Insight(
                    type="trend",
                    title="Modern Development Patterns",
                    description=f"Your codebase incorporates {len(modern_patterns)} modern development patterns, indicating adoption of current best practices.",
                    category="trends",
                    priority="low",
                    confidence=0.8,
                    data={"modern_patterns": modern_patterns},
                    actionable_items=[
                        "Stay updated with latest patterns",
                        "Share knowledge with team",
                    ],
                    impact_score=0.4,
                    effort_score=1.0,
                    tags=["trends", "modern", "patterns"],
                )
            )

        return insights

    def _generate_evolution_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Insight]:
        """Generate evolution and growth insights"""
        insights = []

        commit_count = analysis_data.get("commit_count", 0)
        if commit_count:
            commit_frequency = (
                commit_count / 30
            )  # commits per month (assuming 30-day period)

            if commit_frequency > 10:
                insights.append(
                    Insight(
                        type="achievement",
                        title="Active Development",
                        description=f"High development activity with {commit_count} commits analyzed, indicating active project maintenance and feature development.",
                        category="evolution",
                        priority="low",
                        confidence=0.8,
                        data={
                            "commit_count": commit_count,
                            "frequency": commit_frequency,
                        },
                        actionable_items=[
                            "Maintain development momentum",
                            "Plan feature roadmap",
                        ],
                        impact_score=0.3,
                        effort_score=1.0,
                        tags=["evolution", "activity", "achievement"],
                    )
                )
            elif commit_frequency < 2:
                insights.append(
                    Insight(
                        type="recommendation",
                        title="Low Development Activity",
                        description=f"Low development activity with {commit_count} commits. Consider increasing development frequency for better project health.",
                        category="evolution",
                        priority="medium",
                        confidence=0.7,
                        data={
                            "commit_count": commit_count,
                            "frequency": commit_frequency,
                        },
                        actionable_items=[
                            "Increase development frequency",
                            "Plan regular releases",
                            "Engage with community",
                        ],
                        impact_score=0.6,
                        effort_score=2.0,
                        tags=["evolution", "activity", "recommendation"],
                    )
                )

        return insights

    def _assess_modern_technologies(self, technologies: Dict[str, Any]) -> List[str]:
        """Assess which technologies are modern"""
        modern_techs = []

        frameworks = technologies.get("frameworks", [])
        tools = technologies.get("tools", [])

        modern_section = self.technology_assessments.get("modern", {})
        all_modern = (
            list(modern_section.get("frontend", []))
            + list(modern_section.get("backend", []))
            + list(modern_section.get("mobile", []))
            + list(modern_section.get("tools", []))
        )

        for tech in frameworks + tools:
            if tech in all_modern:
                modern_techs.append(tech)

        return modern_techs

    def _assess_outdated_technologies(self, technologies: Dict[str, Any]) -> List[str]:
        """Assess which technologies are outdated"""
        outdated_techs = []

        frameworks = technologies.get("frameworks", [])
        tools = technologies.get("tools", [])

        # Use .get with defaults to avoid KeyError when a category like 'mobile' is absent
        outdated_section = self.technology_assessments.get("outdated", {})
        all_outdated = (
            list(outdated_section.get("frontend", []))
            + list(outdated_section.get("backend", []))
            + list(outdated_section.get("mobile", []))
            + list(outdated_section.get("tools", []))
        )

        for tech in frameworks + tools:
            if tech in all_outdated:
                outdated_techs.append(tech)

        return outdated_techs

    def _prioritize_insights(self, insights: List[Insight]) -> List[Insight]:
        """Prioritize insights by importance and impact"""
        priority_order = {"critical": 5, "high": 4, "medium": 3, "low": 2}

        # Sort by priority, then by impact score, then by confidence
        return sorted(
            insights,
            key=lambda x: (
                priority_order.get(x.priority, 1),
                x.impact_score,
                x.confidence,
            ),
            reverse=True,
        )
