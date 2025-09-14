# Enhanced Code Quality Analyzer
"""
Advanced code quality analysis system that provides:
- Comprehensive quality metrics and scoring
- Detailed maintainability assessment
- Testability evaluation
- Documentation analysis
- Complexity measurement
- Code style and consistency analysis
- Technical debt quantification
"""

import re
import ast
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict, Counter
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class QualityMetric:
    """Represents a code quality metric"""
    name: str
    value: float
    score: float  # 0-100
    category: str
    description: str
    recommendations: List[str]
    severity: str = "info"  # info, warning, error


@dataclass
class QualityReport:
    """Comprehensive code quality report"""
    overall_score: float
    metrics: List[QualityMetric]
    summary: Dict[str, Any]
    recommendations: List[str]
    technical_debt_score: float
    maintainability_index: float
    testability_score: float


class EnhancedCodeQualityAnalyzer:
    """
    Advanced code quality analyzer with comprehensive metrics,
    detailed assessments, and actionable recommendations.
    """

    def __init__(self):
        """Initialize with comprehensive quality assessment capabilities"""
        self.complexity_weights = self._load_complexity_weights()
        self.quality_thresholds = self._load_quality_thresholds()
        self.style_patterns = self._load_style_patterns()
        self.documentation_patterns = self._load_documentation_patterns()
        
        logger.info("EnhancedCodeQualityAnalyzer initialized")

    def _load_complexity_weights(self) -> Dict[str, float]:
        """Load complexity calculation weights"""
        return {
            "cyclomatic": 0.3,
            "cognitive": 0.2,
            "nesting": 0.2,
            "lines_per_function": 0.15,
            "parameters": 0.1,
            "variables": 0.05
        }

    def _load_quality_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load quality assessment thresholds"""
        return {
            "complexity": {
                "excellent": 5.0,
                "good": 10.0,
                "fair": 20.0,
                "poor": 50.0
            },
            "maintainability": {
                "excellent": 90.0,
                "good": 80.0,
                "fair": 60.0,
                "poor": 40.0
            },
            "testability": {
                "excellent": 90.0,
                "good": 80.0,
                "fair": 60.0,
                "poor": 40.0
            },
            "documentation": {
                "excellent": 80.0,
                "good": 60.0,
                "fair": 40.0,
                "poor": 20.0
            }
        }

    def _load_style_patterns(self) -> Dict[str, List[str]]:
        """Load code style analysis patterns"""
        return {
            "naming_conventions": [
                r"function\s+[a-z][a-zA-Z0-9]*\s*\(",  # camelCase functions
                r"class\s+[A-Z][a-zA-Z0-9]*",  # PascalCase classes
                r"const\s+[A-Z_][A-Z0-9_]*\s*=",  # UPPER_CASE constants
                r"var\s+[a-z][a-zA-Z0-9]*",  # camelCase variables
            ],
            "formatting": [
                r"^\s{2,4}\w",  # Consistent indentation
                r";\s*$",  # Semicolon usage
                r"\{\s*\n",  # Brace placement
                r"//\s+",  # Comment formatting
            ],
            "bad_practices": [
                r"var\s+\w+\s*=",  # var usage (should use let/const)
                r"==\s+",  # Loose equality (should use ===)
                r"eval\s*\(",  # eval usage
                r"with\s*\(",  # with statement
                r"document\.write\s*\(",  # document.write
            ]
        }

    def _load_documentation_patterns(self) -> Dict[str, List[str]]:
        """Load documentation analysis patterns"""
        return {
            "function_docs": [
                r"def\s+\w+\s*\([^)]*\):\s*\n\s*\"\"\".*\"\"\"",  # Python docstrings
                r"function\s+\w+\s*\([^)]*\)\s*\{[\s\S]*?\/\*\*[\s\S]*?\*\/",  # JSDoc
                r"/\*\*[\s\S]*?\*\/\s*function\s+\w+\s*\(",  # JSDoc before function
            ],
            "class_docs": [
                r"class\s+\w+\s*\([^)]*\):\s*\n\s*\"\"\".*\"\"\"",  # Python class docs
                r"class\s+\w+\s*\{[\s\S]*?\/\*\*[\s\S]*?\*\/",  # JSDoc classes
            ],
            "inline_comments": [
                r"//\s+\w+",  # Single line comments
                r"/\*[\s\S]*?\*/",  # Multi-line comments
                r"#\s+\w+",  # Hash comments
            ]
        }

    def analyze_code_quality(self, repo_path: str, file_list: List[str]) -> QualityReport:
        """
        Comprehensive code quality analysis
        
        Args:
            repo_path: Path to the repository
            file_list: List of file paths in the repository
            
        Returns:
            Comprehensive quality report
        """
        try:
            # Analyze source files
            source_files = [f for f in file_list if self._is_source_file(f)]
            
            all_metrics = []
            file_analyses = []
            
            for file_path in source_files[:50]:  # Limit for performance
                full_path = Path(repo_path) / file_path
                
                if not full_path.exists():
                    continue
                    
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    file_analysis = self._analyze_file_quality(content, file_path)
                    file_analyses.append(file_analysis)
                    all_metrics.extend(file_analysis["metrics"])
                    
                except Exception as e:
                    logger.debug(f"Error analyzing file {file_path}: {e}")
            
            # Aggregate metrics
            aggregated_metrics = self._aggregate_metrics(all_metrics)
            
            # Calculate overall scores
            overall_score = self._calculate_overall_score(aggregated_metrics)
            technical_debt_score = self._calculate_technical_debt_score(aggregated_metrics)
            maintainability_index = self._calculate_maintainability_index(aggregated_metrics)
            testability_score = self._calculate_testability_score(aggregated_metrics)
            
            # Generate recommendations
            recommendations = self._generate_quality_recommendations(aggregated_metrics)
            
            # Create summary
            summary = {
                "files_analyzed": len(file_analyses),
                "total_lines": sum(analysis["lines"] for analysis in file_analyses),
                "average_complexity": sum(analysis["complexity"] for analysis in file_analyses) / len(file_analyses) if file_analyses else 0,
                "documentation_coverage": sum(analysis["documentation_coverage"] for analysis in file_analyses) / len(file_analyses) if file_analyses else 0,
                "style_consistency": sum(analysis["style_score"] for analysis in file_analyses) / len(file_analyses) if file_analyses else 0
            }
            
            return QualityReport(
                overall_score=overall_score,
                metrics=aggregated_metrics,
                summary=summary,
                recommendations=recommendations,
                technical_debt_score=technical_debt_score,
                maintainability_index=maintainability_index,
                testability_score=testability_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing code quality: {e}")
            return self._create_empty_report()

    def _analyze_file_quality(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze quality metrics for a single file"""
        lines = content.split('\n')
        line_count = len(lines)
        
        # Calculate various metrics
        complexity = self._calculate_file_complexity(content, lines)
        documentation_coverage = self._calculate_documentation_coverage(content)
        style_score = self._calculate_style_score(content)
        maintainability = self._calculate_maintainability(content, lines)
        testability = self._calculate_testability(content, lines)
        
        # Create metrics
        metrics = [
            QualityMetric(
                name="Cyclomatic Complexity",
                value=complexity["cyclomatic"],
                score=self._score_complexity(complexity["cyclomatic"]),
                category="complexity",
                description=f"Cyclomatic complexity of {complexity['cyclomatic']}",
                recommendations=self._get_complexity_recommendations(complexity["cyclomatic"]),
                severity="warning" if complexity["cyclomatic"] > 10 else "info"
            ),
            QualityMetric(
                name="Documentation Coverage",
                value=documentation_coverage,
                score=documentation_coverage,
                category="documentation",
                description=f"Documentation coverage of {documentation_coverage:.1f}%",
                recommendations=self._get_documentation_recommendations(documentation_coverage),
                severity="warning" if documentation_coverage < 50 else "info"
            ),
            QualityMetric(
                name="Style Consistency",
                value=style_score,
                score=style_score,
                category="style",
                description=f"Code style consistency score of {style_score:.1f}%",
                recommendations=self._get_style_recommendations(style_score),
                severity="warning" if style_score < 70 else "info"
            )
        ]
        
        return {
            "file_path": file_path,
            "lines": line_count,
            "complexity": complexity["cyclomatic"],
            "documentation_coverage": documentation_coverage,
            "style_score": style_score,
            "maintainability": maintainability,
            "testability": testability,
            "metrics": metrics
        }

    def _calculate_file_complexity(self, content: str, lines: List[str]) -> Dict[str, float]:
        """Calculate various complexity metrics for a file"""
        complexity = {
            "cyclomatic": 1.0,  # Start with 1 for the main path
            "cognitive": 0.0,
            "nesting": 0.0,
            "lines_per_function": 0.0,
            "parameters": 0.0,
            "variables": 0.0
        }
        
        # Cyclomatic complexity - count decision points
        decision_patterns = [
            r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b', r'\bswitch\b',
            r'\bcase\b', r'\bcatch\b', r'\bthrow\b', r'\breturn\b',
            r'&&', r'\|\|', r'\?', r':'
        ]
        
        for pattern in decision_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            complexity["cyclomatic"] += matches
        
        # Cognitive complexity - nested conditions
        nesting_level = 0
        max_nesting = 0
        
        for line in lines:
            line = line.strip()
            if re.match(r'\b(if|while|for|switch|catch)\b', line):
                nesting_level += 1
                max_nesting = max(max_nesting, nesting_level)
            elif re.match(r'\b(else|elif|case)\b', line):
                pass  # Don't increase nesting for else/elif
            elif line.startswith('}'):
                nesting_level = max(0, nesting_level - 1)
        
        complexity["nesting"] = max_nesting
        complexity["cognitive"] = complexity["cyclomatic"] + max_nesting * 2
        
        # Function complexity
        functions = re.findall(r'function\s+\w+\s*\([^)]*\)', content)
        if functions:
            total_lines = len(lines)
            complexity["lines_per_function"] = total_lines / len(functions)
        
        # Parameter complexity
        param_matches = re.findall(r'\([^)]*\)', content)
        if param_matches:
            param_counts = [len(re.findall(r'\w+', params)) for params in param_matches]
            complexity["parameters"] = sum(param_counts) / len(param_counts) if param_counts else 0
        
        # Variable complexity
        variable_matches = re.findall(r'\b(var|let|const)\s+\w+', content)
        complexity["variables"] = len(variable_matches)
        
        return complexity

    def _calculate_documentation_coverage(self, content: str) -> float:
        """Calculate documentation coverage percentage"""
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        
        if total_lines == 0:
            return 0.0
        
        documented_lines = 0
        
        # Count documented functions
        function_docs = len(re.findall(self.documentation_patterns["function_docs"][0], content, re.MULTILINE))
        documented_lines += function_docs * 5  # Assume 5 lines per documented function
        
        # Count documented classes
        class_docs = len(re.findall(self.documentation_patterns["class_docs"][0], content, re.MULTILINE))
        documented_lines += class_docs * 10  # Assume 10 lines per documented class
        
        # Count inline comments
        comment_lines = len([line for line in lines if line.strip().startswith(('//', '/*', '*', '#'))])
        documented_lines += comment_lines
        
        return min(100.0, (documented_lines / total_lines) * 100)

    def _calculate_style_score(self, content: str) -> float:
        """Calculate code style consistency score"""
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        
        if total_lines == 0:
            return 0.0
        
        style_violations = 0
        
        # Check naming conventions
        for pattern in self.style_patterns["naming_conventions"]:
            violations = len(re.findall(pattern, content))
            style_violations += violations
        
        # Check bad practices
        for pattern in self.style_patterns["bad_practices"]:
            violations = len(re.findall(pattern, content))
            style_violations += violations * 2  # Weight bad practices more heavily
        
        # Check formatting
        for line in lines:
            if line.strip():
                # Check indentation consistency
                if re.match(r'^\s+', line) and not re.match(r'^\s{2,4}', line):
                    style_violations += 1
        
        # Calculate score (lower violations = higher score)
        violation_rate = style_violations / total_lines
        return max(0.0, 100.0 - (violation_rate * 100))

    def _calculate_maintainability(self, content: str, lines: List[str]) -> float:
        """Calculate maintainability score"""
        complexity = self._calculate_file_complexity(content, lines)
        documentation = self._calculate_documentation_coverage(content)
        style = self._calculate_style_score(content)
        
        # Weighted maintainability score
        maintainability = (
            max(0, 100 - complexity["cyclomatic"] * 5) * 0.4 +  # Complexity impact
            documentation * 0.3 +  # Documentation impact
            style * 0.3  # Style impact
        )
        
        return min(100.0, maintainability)

    def _calculate_testability(self, content: str, lines: List[str]) -> float:
        """Calculate testability score"""
        complexity = self._calculate_file_complexity(content, lines)
        
        # Factors that affect testability
        testability_factors = []
        
        # Function size (smaller functions are more testable)
        if complexity["lines_per_function"] > 0:
            if complexity["lines_per_function"] < 20:
                testability_factors.append(90)
            elif complexity["lines_per_function"] < 50:
                testability_factors.append(70)
            else:
                testability_factors.append(50)
        
        # Cyclomatic complexity (lower is more testable)
        if complexity["cyclomatic"] < 5:
            testability_factors.append(90)
        elif complexity["cyclomatic"] < 10:
            testability_factors.append(70)
        elif complexity["cyclomatic"] < 20:
            testability_factors.append(50)
        else:
            testability_factors.append(30)
        
        # Parameter count (fewer parameters are more testable)
        if complexity["parameters"] < 3:
            testability_factors.append(90)
        elif complexity["parameters"] < 6:
            testability_factors.append(70)
        else:
            testability_factors.append(50)
        
        return sum(testability_factors) / len(testability_factors) if testability_factors else 50.0

    def _score_complexity(self, complexity: float) -> float:
        """Convert complexity value to 0-100 score"""
        if complexity <= 5:
            return 90
        elif complexity <= 10:
            return 70
        elif complexity <= 20:
            return 50
        else:
            return max(0, 100 - complexity * 2)

    def _get_complexity_recommendations(self, complexity: float) -> List[str]:
        """Get recommendations based on complexity score"""
        if complexity <= 5:
            return ["Maintain current complexity level", "Continue good practices"]
        elif complexity <= 10:
            return ["Consider breaking down complex functions", "Extract helper functions"]
        elif complexity <= 20:
            return [
                "Refactor complex functions into smaller ones",
                "Apply design patterns to reduce complexity",
                "Consider using strategy or command patterns"
            ]
        else:
            return [
                "Urgent refactoring needed",
                "Break down into multiple smaller functions",
                "Apply design patterns extensively",
                "Consider architectural changes"
            ]

    def _get_documentation_recommendations(self, coverage: float) -> List[str]:
        """Get recommendations based on documentation coverage"""
        if coverage >= 80:
            return ["Maintain current documentation standards"]
        elif coverage >= 60:
            return ["Add documentation for complex functions", "Improve inline comments"]
        elif coverage >= 40:
            return [
                "Add comprehensive function documentation",
                "Document complex algorithms",
                "Add class-level documentation"
            ]
        else:
            return [
                "Add extensive documentation",
                "Document all public APIs",
                "Add inline comments for complex logic",
                "Consider using documentation generators"
            ]

    def _get_style_recommendations(self, score: float) -> List[str]:
        """Get recommendations based on style score"""
        if score >= 90:
            return ["Maintain current style standards"]
        elif score >= 70:
            return ["Fix minor style inconsistencies", "Use consistent naming conventions"]
        elif score >= 50:
            return [
                "Establish coding style guide",
                "Use linters and formatters",
                "Fix naming convention violations"
            ]
        else:
            return [
                "Implement strict coding standards",
                "Use automated formatting tools",
                "Fix all style violations",
                "Consider code review process"
            ]

    def _aggregate_metrics(self, all_metrics: List[QualityMetric]) -> List[QualityMetric]:
        """Aggregate metrics across all files"""
        metric_groups = defaultdict(list)
        
        for metric in all_metrics:
            metric_groups[metric.name].append(metric)
        
        aggregated = []
        for name, metrics in metric_groups.items():
            if metrics:
                avg_value = sum(m.value for m in metrics) / len(metrics)
                avg_score = sum(m.score for m in metrics) / len(metrics)
                
                aggregated.append(QualityMetric(
                    name=name,
                    value=avg_value,
                    score=avg_score,
                    category=metrics[0].category,
                    description=f"Average {name.lower()} across {len(metrics)} files",
                    recommendations=self._aggregate_recommendations(metrics),
                    severity=metrics[0].severity
                ))
        
        return aggregated

    def _aggregate_recommendations(self, metrics: List[QualityMetric]) -> List[str]:
        """Aggregate recommendations from multiple metrics"""
        all_recommendations = []
        for metric in metrics:
            all_recommendations.extend(metric.recommendations)
        
        # Remove duplicates and prioritize
        unique_recommendations = list(set(all_recommendations))
        
        # Prioritize based on frequency and severity
        recommendation_counts = Counter(all_recommendations)
        return sorted(unique_recommendations, key=lambda x: recommendation_counts[x], reverse=True)

    def _calculate_overall_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate overall quality score"""
        if not metrics:
            return 0.0
        
        # Weight different categories
        weights = {
            "complexity": 0.3,
            "documentation": 0.2,
            "style": 0.2,
            "maintainability": 0.15,
            "testability": 0.15
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            weight = weights.get(metric.category, 0.1)
            weighted_score += metric.score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _calculate_technical_debt_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate technical debt score (higher = more debt)"""
        debt_factors = []
        
        for metric in metrics:
            if metric.score < 60:  # Poor scores contribute to debt
                debt_factors.append(100 - metric.score)
        
        return sum(debt_factors) / len(debt_factors) if debt_factors else 0.0

    def _calculate_maintainability_index(self, metrics: List[QualityMetric]) -> float:
        """Calculate maintainability index"""
        maintainability_metrics = [m for m in metrics if m.category in ["complexity", "documentation", "style"]]
        
        if not maintainability_metrics:
            return 50.0
        
        return sum(m.score for m in maintainability_metrics) / len(maintainability_metrics)

    def _calculate_testability_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate testability score"""
        testability_metrics = [m for m in metrics if "complexity" in m.category.lower()]
        
        if not testability_metrics:
            return 50.0
        
        return sum(m.score for m in testability_metrics) / len(testability_metrics)

    def _generate_quality_recommendations(self, metrics: List[QualityMetric]) -> List[str]:
        """Generate overall quality recommendations"""
        recommendations = []
        
        # Analyze metrics and generate recommendations
        for metric in metrics:
            if metric.score < 60:
                recommendations.extend(metric.recommendations[:2])  # Top 2 recommendations per metric
        
        # Remove duplicates and limit to top recommendations
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:10]  # Top 10 recommendations

    def _is_source_file(self, file_path: str) -> bool:
        """Check if file is a source code file"""
        source_extensions = {
            '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.cs',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.clj',
            '.hs', '.ml', '.fs', '.dart', '.vue', '.svelte'
        }
        
        return Path(file_path).suffix.lower() in source_extensions

    def _create_empty_report(self) -> QualityReport:
        """Create empty quality report for error cases"""
        return QualityReport(
            overall_score=0.0,
            metrics=[],
            summary={"error": "Failed to analyze code quality"},
            recommendations=["Fix analysis errors and retry"],
            technical_debt_score=0.0,
            maintainability_index=0.0,
            testability_score=0.0
        )
