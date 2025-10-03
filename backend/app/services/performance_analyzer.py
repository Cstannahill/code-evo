# app/services/performance_analyzer.py - Performance Analysis Service
"""
Performance Analyzer for Code Evolution Tracker

This service detects performance issues, antipatterns, and provides optimization
recommendations using static analysis and pattern detection.

⚡ FRONTEND UPDATE NEEDED: New performance analysis requires:
- Performance score dashboard
- Bottleneck identification charts
- Performance trends over time
- Optimization recommendations display
- Performance metrics comparison
"""

import re
import ast
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceSeverity(Enum):
    """Performance issue severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PerformanceCategory(Enum):
    """Performance issue categories"""

    ALGORITHMIC = "algorithmic"
    MEMORY = "memory"
    IO = "io"
    DATABASE = "database"
    NETWORK = "network"
    CONCURRENCY = "concurrency"
    CACHING = "caching"
    RENDERING = "rendering"
    RESOURCE_MANAGEMENT = "resource_management"
    ANTI_PATTERN = "anti_pattern"


@dataclass
class PerformanceIssue:
    """Performance issue detection result"""

    id: str
    name: str
    description: str
    severity: PerformanceSeverity
    category: PerformanceCategory
    file_path: str
    line_number: int
    code_snippet: str
    impact_description: str
    optimization_suggestion: str
    confidence: float
    estimated_impact: str  # "high", "medium", "low"
    auto_fixable: bool = False


@dataclass
class PerformanceMetrics:
    """Performance analysis metrics"""

    overall_score: float
    algorithmic_complexity_score: float
    memory_efficiency_score: float
    io_efficiency_score: float
    concurrency_score: float
    resource_management_score: float
    total_issues: int
    critical_issues: int
    high_priority_issues: int
    estimated_performance_impact: str


class PerformanceAnalyzer:
    """
    Comprehensive performance analyzer for detecting bottlenecks,
    antipatterns, and optimization opportunities.
    """

    def __init__(self):
        """Initialize performance analyzer with pattern databases"""
        self.performance_patterns = self._load_performance_patterns()
        self.complexity_patterns = self._load_complexity_patterns()
        self.memory_patterns = self._load_memory_patterns()
        self.concurrency_patterns = self._load_concurrency_patterns()

        logger.info("PerformanceAnalyzer initialized")

    def _load_performance_patterns(self) -> Dict[str, Dict]:
        """Load performance antipattern detection rules"""
        return {
            "n_plus_one_queries": {
                "patterns": [
                    r"for\s+\w+\s+in\s+\w+:\s*\n\s*\w+\.query\(",
                    r"forEach\s*\(\s*\w+\s*=>\s*{[\s\S]*?query\(",
                    r"for\s*\(\s*\w+[\s\S]*?\)\s*{[\s\S]*?query\(",
                    r"while\s*\([\s\S]*?\)\s*{[\s\S]*?SELECT",
                ],
                "severity": PerformanceSeverity.HIGH,
                "category": PerformanceCategory.DATABASE,
                "description": "N+1 query problem - executing queries in loops",
                "impact": "Exponential increase in database calls",
                "solution": "Use bulk queries, joins, or eager loading",
            },
            "inefficient_loops": {
                "patterns": [
                    r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(\s*\w+\s*\)\s*\):",
                    r"for\s*\(\s*let\s+\w+\s*=\s*0;\s*\w+\s*<\s*\w+\.length",
                    r"for\s+\w+\s+in\s+\w+:\s*\n\s*for\s+\w+\s+in\s+\w+:",
                    r"while\s+\w+\s*<\s*len\s*\(\s*\w+\s*\):",
                ],
                "severity": PerformanceSeverity.MEDIUM,
                "category": PerformanceCategory.ALGORITHMIC,
                "description": "Inefficient loop patterns",
                "impact": "Unnecessary iterations and performance overhead",
                "solution": "Use efficient iteration patterns and avoid nested loops",
            },
            "string_concatenation": {
                "patterns": [
                    r'(\w+\s*\+=\s*["\'].*["\']|\w+\s*=\s*\w+\s*\+\s*["\'])',
                    r"for\s+\w+\s+in\s+\w+:\s*\n\s*\w+\s*\+=",
                    r'while\s+.*:\s*\n\s*\w+\s*\+=\s*["\']',
                    r"String\.concat\s*\(",
                ],
                "severity": PerformanceSeverity.MEDIUM,
                "category": PerformanceCategory.MEMORY,
                "description": "Inefficient string concatenation in loops",
                "impact": "Quadratic time complexity and memory waste",
                "solution": "Use string builders, join operations, or template literals",
            },
            "synchronous_io": {
                "patterns": [
                    r"open\s*\(\s*['\"][^'\"]*['\"].*?\)\.read\s*\(\s*\)",
                    r"fs\.readFileSync\s*\(",
                    r"requests\.get\s*\(",
                    r"urllib\.request\.urlopen\s*\(",
                    r"fetch\s*\([^)]*\)\.then",
                ],
                "severity": PerformanceSeverity.HIGH,
                "category": PerformanceCategory.IO,
                "description": "Synchronous I/O operations blocking execution",
                "impact": "Thread blocking and poor responsiveness",
                "solution": "Use asynchronous I/O operations",
            },
            "inefficient_data_structures": {
                "patterns": [
                    r"list\s*\(\s*set\s*\(\s*\w+\s*\)\s*\)",
                    r"for\s+\w+\s+in\s+\w+:\s*\n\s*if\s+\w+\s+in\s+\w+:",
                    r"\.index\s*\(\s*\w+\s*\)",
                    r"\.count\s*\(\s*\w+\s*\)",
                    r"Array\.prototype\.indexOf\.call",
                ],
                "severity": PerformanceSeverity.MEDIUM,
                "category": PerformanceCategory.ALGORITHMIC,
                "description": "Inefficient data structure usage",
                "impact": "Poor time complexity for operations",
                "solution": "Use appropriate data structures (sets, maps, etc.)",
            },
            "memory_leaks": {
                "patterns": [
                    r"addEventListener\s*\([^)]*\)(?![\s\S]*removeEventListener)",
                    r"setInterval\s*\([^)]*\)(?![\s\S]*clearInterval)",
                    r"setTimeout\s*\([^)]*\)(?![\s\S]*clearTimeout)",
                    r"new\s+\w+\s*\([^)]*\)(?![\s\S]*\.close\(\))",
                    r"open\s*\([^)]*\)(?![\s\S]*\.close\(\))",
                ],
                "severity": PerformanceSeverity.HIGH,
                "category": PerformanceCategory.MEMORY,
                "description": "Potential memory leaks from unclosed resources",
                "impact": "Memory growth and potential crashes",
                "solution": "Ensure proper resource cleanup and event listener removal",
            },
            "inefficient_regex": {
                "patterns": [
                    r"re\.compile\s*\([^)]*\).*?re\.compile\s*\(",
                    r"new\s+RegExp\s*\([^)]*\).*?new\s+RegExp\s*\(",
                    r"re\.search\s*\(['\"][^'\"]*\*[^'\"]*['\"]",
                    r"Pattern\.compile\s*\([^)]*\).*?Pattern\.compile\s*\(",
                ],
                "severity": PerformanceSeverity.MEDIUM,
                "category": PerformanceCategory.ALGORITHMIC,
                "description": "Inefficient regular expression usage",
                "impact": "Repeated compilation or catastrophic backtracking",
                "solution": "Compile regex once and avoid greedy quantifiers",
            },
            "blocking_ui_operations": {
                "patterns": [
                    r"document\.write\s*\(",
                    r"alert\s*\(",
                    r"confirm\s*\(",
                    r"prompt\s*\(",
                    r"while\s*\(\s*true\s*\)",
                    r"for\s*\(\s*;\s*;\s*\)",
                ],
                "severity": PerformanceSeverity.HIGH,
                "category": PerformanceCategory.RENDERING,
                "description": "Operations that block UI rendering",
                "impact": "Poor user experience and unresponsive interface",
                "solution": "Use asynchronous operations and avoid blocking calls",
            },
            "inefficient_dom_operations": {
                "patterns": [
                    r"for\s*\([^)]*\)\s*{\s*document\.",
                    r"while\s*\([^)]*\)\s*{\s*\w+\.appendChild",
                    r"getElementsBy.*\s*\([^)]*\).*getElementsBy",
                    r"querySelector.*\([^)]*\).*querySelector",
                ],
                "severity": PerformanceSeverity.MEDIUM,
                "category": PerformanceCategory.RENDERING,
                "description": "Inefficient DOM manipulation patterns",
                "impact": "Layout thrashing and rendering performance",
                "solution": "Batch DOM operations and cache element references",
            },
            "poor_error_handling": {
                "patterns": [
                    r"try:\s*\n[\s\S]*?\nexcept:\s*\n\s*pass",
                    r"try\s*{\s*[\s\S]*?\s*}\s*catch\s*\([^)]*\)\s*{\s*}",
                    r"@silenced",
                    r"error_reporting\s*\(\s*0\s*\)",
                ],
                "severity": PerformanceSeverity.LOW,
                "category": PerformanceCategory.ANTI_PATTERN,
                "description": "Poor error handling that hides performance issues",
                "impact": "Hidden errors that may cause performance degradation",
                "solution": "Implement proper error handling and logging",
            },
        }

    def _load_complexity_patterns(self) -> Dict[str, Dict]:
        """Load algorithmic complexity detection patterns"""
        return {
            "nested_loops": {
                "patterns": [
                    r"for\s+\w+.*:\s*\n.*for\s+\w+.*:",
                    r"for\s*\([^)]*\)\s*{\s*[^}]*for\s*\(",
                    r"while\s*\([^)]*\)\s*{\s*[^}]*while\s*\(",
                ],
                "complexity": "O(n²)",
                "severity": PerformanceSeverity.MEDIUM,
                "description": "Nested loops creating quadratic complexity",
            },
            "triple_nested_loops": {
                "patterns": [
                    r"for\s+\w+.*:\s*\n.*for\s+\w+.*:\s*\n.*for\s+\w+.*:",
                    r"for\s*\([^)]*\)\s*{\s*[^}]*for\s*\([^)]*\)\s*{\s*[^}]*for\s*\(",
                ],
                "complexity": "O(n³)",
                "severity": PerformanceSeverity.HIGH,
                "description": "Triple nested loops creating cubic complexity",
            },
            "recursive_without_memoization": {
                "patterns": [
                    r"def\s+(\w+)\s*\([^)]*\):\s*[^{]*return.*\1\s*\(",
                    r"function\s+(\w+)\s*\([^)]*\)\s*{\s*[^}]*return.*\1\s*\(",
                ],
                "complexity": "Exponential",
                "severity": PerformanceSeverity.HIGH,
                "description": "Recursive functions without memoization",
            },
        }

    def _load_memory_patterns(self) -> Dict[str, Dict]:
        """Load memory usage pattern detection"""
        return {
            "large_objects_in_loops": {
                "patterns": [
                    r"for\s+\w+.*:\s*\n.*\[\s*\]",
                    r"for\s+\w+.*:\s*\n.*\{\s*\}",
                    r"while\s*\([^)]*\)\s*{\s*[^}]*new\s+Array",
                    r"for\s*\([^)]*\)\s*{\s*[^}]*new\s+Object",
                ],
                "severity": PerformanceSeverity.MEDIUM,
                "description": "Creating large objects in loops",
            },
            "unnecessary_copying": {
                "patterns": [
                    r"list\s*\(\s*\w+\s*\)",
                    r"dict\s*\(\s*\w+\s*\)",
                    r"Array\.from\s*\(\s*\w+\s*\)",
                    r"Object\.assign\s*\(\s*\{\s*\}\s*,\s*\w+\s*\)",
                ],
                "severity": PerformanceSeverity.LOW,
                "description": "Unnecessary data copying operations",
            },
        }

    def _load_concurrency_patterns(self) -> Dict[str, Dict]:
        """Load concurrency and threading patterns"""
        return {
            "race_conditions": {
                "patterns": [
                    r"threading\.Thread.*shared_var",
                    r"asyncio\.create_task.*global\s+\w+",
                    r"new\s+Worker.*postMessage",
                ],
                "severity": PerformanceSeverity.HIGH,
                "description": "Potential race conditions",
            },
            "blocking_in_async": {
                "patterns": [
                    r"async\s+def\s+\w+.*:\s*[^{}]*time\.sleep",
                    r"async\s+function\s+\w+.*{\s*[^}]*Thread\.sleep",
                    r"await.*requests\.get",
                ],
                "severity": PerformanceSeverity.HIGH,
                "description": "Blocking operations in async functions",
            },
        }

    def analyze_performance(
        self, code: str, file_path: str, language: Optional[str] = None
    ) -> List[PerformanceIssue]:
        """
        Analyze code for performance issues and antipatterns

        Args:
            code: Source code to analyze
            file_path: Path to the file being analyzed
            language: Programming language (auto-detected if None)

        Returns:
            List of detected performance issues
        """
        if not language:
            language = self._detect_language(file_path)

        issues = []
        lines = code.split("\n")

        # Analyze performance patterns
        for pattern_name, pattern_info in self.performance_patterns.items():
            issues.extend(
                self._find_performance_issues(
                    pattern_name, pattern_info, code, lines, file_path, language
                )
            )

        # Analyze complexity patterns
        issues.extend(self._analyze_complexity_issues(code, lines, file_path))

        # Analyze memory patterns
        issues.extend(self._analyze_memory_issues(code, lines, file_path))

        # Analyze concurrency patterns
        issues.extend(
            self._analyze_concurrency_issues(code, lines, file_path, language)
        )

        # Language-specific analysis
        if language.lower() == "python":
            issues.extend(self._analyze_python_performance(code, lines, file_path))
        elif language.lower() in ["javascript", "typescript"]:
            issues.extend(self._analyze_javascript_performance(code, lines, file_path))
        elif language.lower() == "java":
            issues.extend(self._analyze_java_performance(code, lines, file_path))

        return issues

    def _find_performance_issues(
        self,
        pattern_name: str,
        pattern_info: Dict,
        code: str,
        lines: List[str],
        file_path: str,
        language: str,
    ) -> List[PerformanceIssue]:
        """Find performance issues using pattern matching"""
        issues = []

        for pattern in pattern_info["patterns"]:
            for match in re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE):
                line_num = code[: match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                confidence = self._calculate_confidence(
                    match, line_content, pattern_name, language
                )

                issue = PerformanceIssue(
                    id=f"{pattern_name}_{file_path}_{line_num}",
                    name=pattern_name.replace("_", " ").title(),
                    description=pattern_info["description"],
                    severity=pattern_info["severity"],
                    category=pattern_info["category"],
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    impact_description=pattern_info["impact"],
                    optimization_suggestion=pattern_info["solution"],
                    confidence=confidence,
                    estimated_impact=self._estimate_impact(pattern_info["severity"]),
                    auto_fixable=self._is_auto_fixable(pattern_name),
                )

                issues.append(issue)

        return issues

    def _analyze_complexity_issues(
        self, code: str, lines: List[str], file_path: str
    ) -> List[PerformanceIssue]:
        """Analyze algorithmic complexity issues"""
        issues = []

        for pattern_name, pattern_info in self.complexity_patterns.items():
            for pattern in pattern_info["patterns"]:
                for match in re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE):
                    line_num = code[: match.start()].count("\n") + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                    issue = PerformanceIssue(
                        id=f"complexity_{pattern_name}_{file_path}_{line_num}",
                        name=f"High Complexity: {pattern_name.replace('_', ' ').title()}",
                        description=pattern_info["description"],
                        severity=pattern_info["severity"],
                        category=PerformanceCategory.ALGORITHMIC,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line_content.strip(),
                        impact_description=f"Time complexity: {pattern_info['complexity']}",
                        optimization_suggestion=f"Consider optimizing to reduce complexity from {pattern_info['complexity']}",
                        confidence=0.8,
                        estimated_impact=self._estimate_impact(
                            pattern_info["severity"]
                        ),
                    )

                    issues.append(issue)

        return issues

    def _analyze_memory_issues(
        self, code: str, lines: List[str], file_path: str
    ) -> List[PerformanceIssue]:
        """Analyze memory usage issues"""
        issues = []

        for pattern_name, pattern_info in self.memory_patterns.items():
            for pattern in pattern_info["patterns"]:
                for match in re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE):
                    line_num = code[: match.start()].count("\n") + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                    issue = PerformanceIssue(
                        id=f"memory_{pattern_name}_{file_path}_{line_num}",
                        name=f"Memory Issue: {pattern_name.replace('_', ' ').title()}",
                        description=pattern_info["description"],
                        severity=pattern_info["severity"],
                        category=PerformanceCategory.MEMORY,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line_content.strip(),
                        impact_description="Potential memory waste or inefficiency",
                        optimization_suggestion="Optimize memory usage patterns",
                        confidence=0.7,
                        estimated_impact=self._estimate_impact(
                            pattern_info["severity"]
                        ),
                    )

                    issues.append(issue)

        return issues

    def _analyze_concurrency_issues(
        self, code: str, lines: List[str], file_path: str, language: str
    ) -> List[PerformanceIssue]:
        """Analyze concurrency and threading issues"""
        issues = []

        for pattern_name, pattern_info in self.concurrency_patterns.items():
            for pattern in pattern_info["patterns"]:
                for match in re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE):
                    line_num = code[: match.start()].count("\n") + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                    issue = PerformanceIssue(
                        id=f"concurrency_{pattern_name}_{file_path}_{line_num}",
                        name=f"Concurrency Issue: {pattern_name.replace('_', ' ').title()}",
                        description=pattern_info["description"],
                        severity=pattern_info["severity"],
                        category=PerformanceCategory.CONCURRENCY,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line_content.strip(),
                        impact_description="Potential concurrency problems affecting performance",
                        optimization_suggestion="Review concurrency patterns and synchronization",
                        confidence=0.6,
                        estimated_impact=self._estimate_impact(
                            pattern_info["severity"]
                        ),
                    )

                    issues.append(issue)

        return issues

    def _analyze_python_performance(
        self, code: str, lines: List[str], file_path: str
    ) -> List[PerformanceIssue]:
        """Python-specific performance analysis"""
        issues = []

        # Check for list comprehension opportunities
        list_comp_pattern = r"for\s+\w+\s+in\s+\w+:\s*\n\s*\w+\.append\s*\("
        for match in re.finditer(list_comp_pattern, code, re.MULTILINE):
            line_num = code[: match.start()].count("\n") + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""

            issues.append(
                PerformanceIssue(
                    id=f"python_list_comp_{file_path}_{line_num}",
                    name="List Comprehension Opportunity",
                    description="Loop that could be replaced with list comprehension",
                    severity=PerformanceSeverity.LOW,
                    category=PerformanceCategory.ALGORITHMIC,
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    impact_description="Minor performance improvement opportunity",
                    optimization_suggestion="Use list comprehension for better performance and readability",
                    confidence=0.8,
                    estimated_impact="low",
                    auto_fixable=True,
                )
            )

        return issues

    def _analyze_javascript_performance(
        self, code: str, lines: List[str], file_path: str
    ) -> List[PerformanceIssue]:
        """JavaScript-specific performance analysis"""
        issues = []

        # Check for inefficient array operations
        array_inefficiency_patterns = [
            r"for\s*\(\s*let\s+\w+\s*=\s*0;\s*\w+\s*<\s*\w+\.length;\s*\w+\+\+\s*\)",
            r"\.map\s*\([^)]*\)\.filter\s*\([^)]*\)",
            r"\.filter\s*\([^)]*\)\.map\s*\([^)]*\)",
        ]

        for pattern in array_inefficiency_patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                line_num = code[: match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                issues.append(
                    PerformanceIssue(
                        id=f"js_array_{file_path}_{line_num}",
                        name="Inefficient Array Operation",
                        description="Array operation that could be optimized",
                        severity=PerformanceSeverity.LOW,
                        category=PerformanceCategory.ALGORITHMIC,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line_content.strip(),
                        impact_description="Multiple array iterations when one would suffice",
                        optimization_suggestion="Combine operations or use for-of loops for better performance",
                        confidence=0.7,
                        estimated_impact="low",
                    )
                )

        return issues

    def _analyze_java_performance(
        self, code: str, lines: List[str], file_path: str
    ) -> List[PerformanceIssue]:
        """Java-specific performance analysis"""
        issues = []

        # Check for string concatenation in loops
        string_concat_pattern = r"for\s*\([^)]*\)\s*{\s*[^}]*\+\s*=.*String"
        for match in re.finditer(string_concat_pattern, code, re.MULTILINE):
            line_num = code[: match.start()].count("\n") + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""

            issues.append(
                PerformanceIssue(
                    id=f"java_string_{file_path}_{line_num}",
                    name="String Concatenation in Loop",
                    description="Inefficient string concatenation pattern",
                    severity=PerformanceSeverity.MEDIUM,
                    category=PerformanceCategory.MEMORY,
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    impact_description="Quadratic time complexity for string operations",
                    optimization_suggestion="Use StringBuilder for string concatenation in loops",
                    confidence=0.9,
                    estimated_impact="medium",
                    auto_fixable=True,
                )
            )

        return issues

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
        }
        return lang_map.get(ext, "unknown")

    def _calculate_confidence(
        self, match, line_content: str, pattern_name: str, language: str
    ) -> float:
        """Calculate confidence score for performance issue detection"""
        base_confidence = 0.7

        # Increase confidence for specific contexts
        if "for" in line_content.lower() and "loop" in pattern_name:
            base_confidence += 0.2
        if "query" in line_content.lower() and "database" in pattern_name:
            base_confidence += 0.2
        if "async" in line_content.lower() and "blocking" in pattern_name:
            base_confidence += 0.1

        # Decrease confidence for comments
        if line_content.strip().startswith(("#", "//", "/*", "*")):
            base_confidence -= 0.4

        return min(1.0, max(0.1, base_confidence))

    def _estimate_impact(self, severity: PerformanceSeverity) -> str:
        """Estimate performance impact based on severity"""
        impact_map = {
            PerformanceSeverity.CRITICAL: "high",
            PerformanceSeverity.HIGH: "high",
            PerformanceSeverity.MEDIUM: "medium",
            PerformanceSeverity.LOW: "low",
            PerformanceSeverity.INFO: "low",
        }
        return impact_map.get(severity, "medium")

    def _is_auto_fixable(self, pattern_name: str) -> bool:
        """Determine if performance issue is automatically fixable"""
        auto_fixable_patterns = {
            "inefficient_loops": True,
            "string_concatenation": True,
            "inefficient_data_structures": False,  # Requires design changes
            "n_plus_one_queries": False,  # Requires architectural changes
            "memory_leaks": False,  # Requires careful manual review
        }
        return auto_fixable_patterns.get(pattern_name, False)

    def calculate_performance_metrics(
        self, issues: List[PerformanceIssue]
    ) -> PerformanceMetrics:
        """Calculate overall performance metrics from issues"""
        if not issues:
            return PerformanceMetrics(
                overall_score=95.0,
                algorithmic_complexity_score=95.0,
                memory_efficiency_score=95.0,
                io_efficiency_score=95.0,
                concurrency_score=95.0,
                resource_management_score=95.0,
                total_issues=0,
                critical_issues=0,
                high_priority_issues=0,
                estimated_performance_impact="low",
            )

        # Count issues by severity
        severity_counts = Counter(issue.severity for issue in issues)
        category_scores = defaultdict(list)

        # Calculate category-specific scores
        severity_weights = {
            PerformanceSeverity.CRITICAL: 25,
            PerformanceSeverity.HIGH: 15,
            PerformanceSeverity.MEDIUM: 8,
            PerformanceSeverity.LOW: 3,
            PerformanceSeverity.INFO: 1,
        }

        for issue in issues:
            penalty = severity_weights[issue.severity]
            category_scores[issue.category].append(penalty)

        # Calculate scores for each category
        def calculate_category_score(penalties: List[int]) -> float:
            total_penalty = sum(penalties)
            return max(0.0, 100.0 - total_penalty)

        algorithmic_score = calculate_category_score(
            category_scores.get(PerformanceCategory.ALGORITHMIC, [])
        )
        memory_score = calculate_category_score(
            category_scores.get(PerformanceCategory.MEMORY, [])
        )
        io_score = calculate_category_score(
            category_scores.get(PerformanceCategory.IO, [])
        )
        concurrency_score = calculate_category_score(
            category_scores.get(PerformanceCategory.CONCURRENCY, [])
        )
        resource_score = calculate_category_score(
            category_scores.get(PerformanceCategory.RESOURCE_MANAGEMENT, [])
        )

        # Overall score
        all_penalties = [
            penalty for penalties in category_scores.values() for penalty in penalties
        ]
        overall_score = calculate_category_score(all_penalties)

        # Determine overall impact
        critical_count = severity_counts.get(PerformanceSeverity.CRITICAL, 0)
        high_count = severity_counts.get(PerformanceSeverity.HIGH, 0)

        if critical_count > 0:
            impact = "high"
        elif high_count > 2:
            impact = "high"
        elif high_count > 0 or severity_counts.get(PerformanceSeverity.MEDIUM, 0) > 3:
            impact = "medium"
        else:
            impact = "low"

        return PerformanceMetrics(
            overall_score=overall_score,
            algorithmic_complexity_score=algorithmic_score,
            memory_efficiency_score=memory_score,
            io_efficiency_score=io_score,
            concurrency_score=concurrency_score,
            resource_management_score=resource_score,
            total_issues=len(issues),
            critical_issues=severity_counts.get(PerformanceSeverity.CRITICAL, 0),
            high_priority_issues=severity_counts.get(PerformanceSeverity.HIGH, 0),
            estimated_performance_impact=impact,
        )

    def generate_performance_report(
        self, issues: List[PerformanceIssue], metrics: PerformanceMetrics
    ) -> Dict[str, Any]:
        """Generate comprehensive performance analysis report"""
        return {
            "performance_metrics": {
                "overall_score": metrics.overall_score,
                "grade": self._calculate_grade(metrics.overall_score),
                "algorithmic_complexity": metrics.algorithmic_complexity_score,
                "memory_efficiency": metrics.memory_efficiency_score,
                "io_efficiency": metrics.io_efficiency_score,
                "concurrency": metrics.concurrency_score,
                "resource_management": metrics.resource_management_score,
                "estimated_impact": metrics.estimated_performance_impact,
            },
            "issue_summary": {
                "total_issues": metrics.total_issues,
                "critical_issues": metrics.critical_issues,
                "high_priority_issues": metrics.high_priority_issues,
                "auto_fixable_issues": len([i for i in issues if i.auto_fixable]),
            },
            "issues_by_category": self._categorize_issues(issues),
            "issues_by_severity": self._group_by_severity(issues),
            "top_issues": [
                self._issue_to_dict(issue) for issue in issues[:10]
            ],  # Top 10
            "optimization_recommendations": self._generate_optimization_recommendations(
                issues, metrics
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _issue_to_dict(self, issue: PerformanceIssue) -> Dict[str, Any]:
        """Convert performance issue to dictionary"""
        return {
            "id": issue.id,
            "name": issue.name,
            "description": issue.description,
            "severity": issue.severity.value,
            "category": issue.category.value,
            "file_path": issue.file_path,
            "line_number": issue.line_number,
            "code_snippet": issue.code_snippet,
            "impact_description": issue.impact_description,
            "optimization_suggestion": issue.optimization_suggestion,
            "confidence": issue.confidence,
            "estimated_impact": issue.estimated_impact,
            "auto_fixable": issue.auto_fixable,
        }

    def _categorize_issues(self, issues: List[PerformanceIssue]) -> Dict[str, int]:
        """Categorize issues by performance category"""
        category_counts = {}
        for category in PerformanceCategory:
            category_counts[category.value] = len(
                [i for i in issues if i.category == category]
            )
        return category_counts

    def _group_by_severity(self, issues: List[PerformanceIssue]) -> Dict[str, int]:
        """Group issues by severity level"""
        severity_counts = {}
        for severity in PerformanceSeverity:
            severity_counts[severity.value] = len(
                [i for i in issues if i.severity == severity]
            )
        return severity_counts

    def _generate_optimization_recommendations(
        self, issues: List[PerformanceIssue], metrics: PerformanceMetrics
    ) -> List[str]:
        """Generate prioritized optimization recommendations"""
        recommendations = []

        # Critical issues first
        critical_issues = [
            i for i in issues if i.severity == PerformanceSeverity.CRITICAL
        ]
        if critical_issues:
            recommendations.append(
                f"🚨 Address {len(critical_issues)} critical performance issues immediately"
            )

        # Category-specific recommendations
        if metrics.algorithmic_complexity_score < 70:
            recommendations.append(
                "🔄 Optimize algorithmic complexity - consider better data structures and algorithms"
            )

        if metrics.memory_efficiency_score < 70:
            recommendations.append(
                "💾 Improve memory efficiency - reduce allocations and fix potential leaks"
            )

        if metrics.io_efficiency_score < 70:
            recommendations.append(
                "📡 Optimize I/O operations - use asynchronous patterns and caching"
            )

        if metrics.concurrency_score < 70:
            recommendations.append(
                "⚡ Review concurrency patterns - fix race conditions and blocking operations"
            )

        # Auto-fixable recommendations
        auto_fixable = [i for i in issues if i.auto_fixable]
        if auto_fixable:
            recommendations.append(
                f"🔧 Consider automated fixes for {len(auto_fixable)} performance issues"
            )

        # Database-specific
        db_issues = [i for i in issues if i.category == PerformanceCategory.DATABASE]
        if db_issues:
            recommendations.append(
                "🗃️ Optimize database queries - fix N+1 problems and add proper indexing"
            )

        return recommendations[:5]  # Top 5 recommendations

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from performance score"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


# Convenience function for service integration
def get_performance_analyzer() -> PerformanceAnalyzer:
    """Get PerformanceAnalyzer instance"""
    return PerformanceAnalyzer()
