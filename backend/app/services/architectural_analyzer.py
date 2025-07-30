# app/services/architectural_analyzer.py - Architectural Pattern Detection
"""
Architectural Pattern Analyzer for Code Evolution Tracker

This service detects architectural patterns, design patterns, and code organization
strategies from repository structure and code analysis.

🏗️ FRONTEND UPDATE NEEDED: New architectural analysis requires:
- Architecture diagram visualization
- Pattern relationship graphs
- Design pattern categorization
- Architecture quality metrics display
- Pattern evolution timeline
"""

import os
import re
import ast
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class ArchitecturalStyle(Enum):
    """Major architectural styles"""
    MONOLITHIC = "monolithic"
    MICROSERVICES = "microservices"
    LAYERED = "layered"
    MVC = "mvc"
    MVP = "mvp"
    MVVM = "mvvm"
    CLEAN_ARCHITECTURE = "clean_architecture"
    HEXAGONAL = "hexagonal"
    EVENT_DRIVEN = "event_driven"
    PIPE_AND_FILTER = "pipe_and_filter"
    COMPONENT_BASED = "component_based"
    SOA = "service_oriented"


class DesignPattern(Enum):
    """GoF and common design patterns"""
    # Creational
    SINGLETON = "singleton"
    FACTORY = "factory"
    ABSTRACT_FACTORY = "abstract_factory"
    BUILDER = "builder"
    PROTOTYPE = "prototype"
    
    # Structural
    ADAPTER = "adapter"
    BRIDGE = "bridge"
    COMPOSITE = "composite"
    DECORATOR = "decorator"
    FACADE = "facade"
    FLYWEIGHT = "flyweight"
    PROXY = "proxy"
    
    # Behavioral
    OBSERVER = "observer"
    STRATEGY = "strategy"
    COMMAND = "command"
    STATE = "state"
    TEMPLATE_METHOD = "template_method"
    VISITOR = "visitor"
    MEDIATOR = "mediator"
    CHAIN_OF_RESPONSIBILITY = "chain_of_responsibility"
    ITERATOR = "iterator"
    MEMENTO = "memento"
    INTERPRETER = "interpreter"
    
    # Modern patterns
    DEPENDENCY_INJECTION = "dependency_injection"
    REPOSITORY = "repository"
    UNIT_OF_WORK = "unit_of_work"
    CQRS = "cqrs"
    EVENT_SOURCING = "event_sourcing"


@dataclass
class PatternDetection:
    """Result of pattern detection"""
    pattern: DesignPattern
    confidence: float
    evidence: List[str]
    files_involved: List[str]
    description: str
    benefits: List[str]
    potential_issues: List[str]


@dataclass
class ArchitecturalAnalysis:
    """Complete architectural analysis result"""
    primary_style: ArchitecturalStyle
    confidence: float
    design_patterns: List[PatternDetection]
    architecture_quality_score: float
    modularity_score: float
    coupling_score: float
    cohesion_score: float
    complexity_score: float
    recommendations: List[str]
    directory_structure: Dict[str, Any]
    dependency_graph: Dict[str, List[str]]
    layer_analysis: Dict[str, Any]


class ArchitecturalAnalyzer:
    """
    Comprehensive architectural pattern detection and analysis
    """

    def __init__(self):
        """Initialize architectural analyzer"""
        self.file_patterns = self._load_file_patterns()
        self.code_patterns = self._load_code_patterns()
        self.directory_indicators = self._load_directory_indicators()
        
        logger.info("ArchitecturalAnalyzer initialized")

    def _load_file_patterns(self) -> Dict[str, Dict]:
        """Load file naming patterns that indicate architectural styles"""
        return {
            "mvc": {
                "controllers": [r".*[Cc]ontroller\..*", r".*[Cc]trl\..*"],
                "models": [r".*[Mm]odel\..*", r".*[Ee]ntity\..*"],
                "views": [r".*[Vv]iew\..*", r".*[Tt]emplate\..*", r".*\.html$", r".*\.jsx$", r".*\.vue$"],
                "required_patterns": 2  # Need at least 2 pattern types
            },
            
            "clean_architecture": {
                "entities": [r".*[Ee]ntit(y|ies).*", r".*[Dd]omain.*"],
                "use_cases": [r".*[Uu]se[Cc]ase.*", r".*[Ss]ervice.*", r".*[Ii]nteractor.*"],
                "adapters": [r".*[Aa]dapter.*", r".*[Gg]ateway.*", r".*[Rr]epository.*"],
                "frameworks": [r".*[Cc]ontroller.*", r".*[Pp]resenter.*"],
                "required_patterns": 3
            },
            
            "microservices": {
                "services": [r".*[Ss]ervice.*", r".*[Aa]pi.*"],
                "docker": [r"[Dd]ockerfile.*", r"docker-compose\..*"],
                "config": [r".*config.*", r".*\.env.*", r"k8s/.*", r"kubernetes/.*"],
                "required_patterns": 2
            }
        }

    def _load_code_patterns(self) -> Dict[str, Dict]:
        """Load code patterns for design pattern detection"""
        return {
            DesignPattern.SINGLETON: {
                "python": [
                    r"class\s+\w+.*:\s*\n.*_instance\s*=\s*None",
                    r"def\s+__new__\s*\(cls.*\):",
                    r"if\s+cls\._instance\s+is\s+None:"
                ],
                "javascript": [
                    r"var\s+\w+\s*=\s*\(\s*function\s*\(\s*\)\s*{",
                    r"return\s*{\s*getInstance\s*:",
                    r"if\s*\(\s*instance\s*===?\s*(undefined|null)\s*\)"
                ],
                "java": [
                    r"private\s+static\s+\w+\s+instance",
                    r"public\s+static\s+\w+\s+getInstance\s*\(\s*\)",
                    r"private\s+\w+\s*\(\s*\)\s*{"
                ]
            },
            
            DesignPattern.FACTORY: {
                "python": [
                    r"def\s+create_\w+\s*\(",
                    r"class\s+\w*Factory\w*:",
                    r"def\s+make_\w+\s*\("
                ],
                "javascript": [
                    r"function\s+create\w+\s*\(",
                    r"class\s+\w*Factory\w*",
                    r"\w+Factory\s*=\s*{"
                ],
                "java": [
                    r"class\s+\w*Factory\w*",
                    r"public\s+\w+\s+create\w+\s*\(",
                    r"static\s+\w+\s+create\s*\("
                ]
            },
            
            DesignPattern.OBSERVER: {
                "python": [
                    r"class\s+\w*Observer\w*:",
                    r"def\s+notify\s*\(",
                    r"def\s+update\s*\(",
                    r"def\s+subscribe\s*\(",
                    r"observers\s*=\s*\[\]"
                ],
                "javascript": [
                    r"class\s+\w*Observer\w*",
                    r"addEventListener\s*\(",
                    r"on\s*\(\s*['\"].*['\"]",
                    r"observers\s*=\s*\[\]"
                ],
                "java": [
                    r"class\s+\w*Observer\w*",
                    r"interface\s+\w*Observer\w*",
                    r"void\s+update\s*\(",
                    r"addObserver\s*\("
                ]
            },
            
            DesignPattern.STRATEGY: {
                "python": [
                    r"class\s+\w*Strategy\w*:",
                    r"def\s+execute\s*\(",
                    r"strategy\s*=\s*\w+Strategy"
                ],
                "javascript": [
                    r"class\s+\w*Strategy\w*",
                    r"strategy\s*:\s*\w+Strategy",
                    r"execute\s*:\s*function"
                ],
                "java": [
                    r"interface\s+\w*Strategy\w*",
                    r"class\s+\w*Strategy\w*",
                    r"void\s+execute\s*\("
                ]
            },
            
            DesignPattern.DECORATOR: {
                "python": [
                    r"@\w+",
                    r"def\s+\w*decorator\w*\s*\(",
                    r"def\s+wrapper\s*\(",
                    r"functools\.wraps"
                ],
                "javascript": [
                    r"function\s+\w*decorator\w*\s*\(",
                    r"class\s+\w*Decorator\w*",
                    r"wrapper\s*=\s*function"
                ],
                "java": [
                    r"@\w+",
                    r"class\s+\w*Decorator\w*",
                    r"extends\s+\w*Decorator\w*"
                ]
            },
            
            DesignPattern.REPOSITORY: {
                "python": [
                    r"class\s+\w*Repository\w*:",
                    r"def\s+find_by_\w+\s*\(",
                    r"def\s+save\s*\(",
                    r"def\s+delete\s*\("
                ],
                "javascript": [
                    r"class\s+\w*Repository\w*",
                    r"findBy\w+\s*\(",
                    r"save\s*\(",
                    r"delete\s*\("
                ],
                "java": [
                    r"interface\s+\w*Repository\w*",
                    r"class\s+\w*Repository\w*",
                    r"findBy\w+\s*\(",
                    r"@Repository"
                ]
            },
            
            DesignPattern.DEPENDENCY_INJECTION: {
                "python": [
                    r"def\s+__init__\s*\(self.*:\s*\w+",
                    r"@inject",
                    r"container\.register",
                    r"dependency\s*=\s*\w+\(\)"
                ],
                "javascript": [
                    r"constructor\s*\(\s*\w+\s*:\s*\w+",
                    r"@Injectable",
                    r"container\.register",
                    r"inject\s*\("
                ],
                "java": [
                    r"@Autowired",
                    r"@Inject",
                    r"@Component",
                    r"@Service"
                ]
            }
        }

    def _load_directory_indicators(self) -> Dict[str, List[str]]:
        """Load directory structure indicators"""
        return {
            "mvc": ["controllers", "models", "views", "templates"],
            "clean_architecture": ["domain", "usecases", "adapters", "frameworks", "entities"],
            "layered": ["presentation", "business", "data", "persistence"],
            "microservices": ["services", "api", "gateway", "discovery"],
            "component_based": ["components", "modules", "widgets"],
            "event_driven": ["events", "handlers", "subscribers", "publishers"]
        }

    def analyze_architecture(self, repository_path: str, file_list: List[str] = None) -> ArchitecturalAnalysis:
        """
        Perform comprehensive architectural analysis
        
        Args:
            repository_path: Path to repository root
            file_list: Optional list of files to analyze
            
        Returns:
            Complete architectural analysis
        """
        try:
            if file_list is None:
                file_list = self._get_all_files(repository_path)
            
            # Analyze directory structure
            directory_structure = self._analyze_directory_structure(repository_path, file_list)
            
            # Detect architectural style
            primary_style, style_confidence = self._detect_architectural_style(
                repository_path, file_list, directory_structure
            )
            
            # Detect design patterns
            design_patterns = self._detect_design_patterns(repository_path, file_list)
            
            # Analyze code quality metrics
            quality_metrics = self._analyze_architecture_quality(
                repository_path, file_list, design_patterns
            )
            
            # Generate dependency graph
            dependency_graph = self._build_dependency_graph(repository_path, file_list)
            
            # Analyze layers
            layer_analysis = self._analyze_layers(directory_structure, dependency_graph)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                primary_style, design_patterns, quality_metrics, layer_analysis
            )
            
            return ArchitecturalAnalysis(
                primary_style=primary_style,
                confidence=style_confidence,
                design_patterns=design_patterns,
                architecture_quality_score=quality_metrics["overall_score"],
                modularity_score=quality_metrics["modularity"],
                coupling_score=quality_metrics["coupling"],
                cohesion_score=quality_metrics["cohesion"],
                complexity_score=quality_metrics["complexity"],
                recommendations=recommendations,
                directory_structure=directory_structure,
                dependency_graph=dependency_graph,
                layer_analysis=layer_analysis
            )
            
        except Exception as e:
            logger.error(f"Architectural analysis failed: {e}")
            return self._create_fallback_analysis()

    def _get_all_files(self, repository_path: str) -> List[str]:
        """Get all relevant files from repository"""
        files = []
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache', 'venv', 'env'}
        
        for root, dirs, filenames in os.walk(repository_path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for filename in filenames:
                if self._is_code_file(filename):
                    rel_path = os.path.relpath(os.path.join(root, filename), repository_path)
                    files.append(rel_path)
        
        return files

    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file"""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cs', '.cpp', '.c', 
            '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
            '.html', '.css', '.scss', '.sass', '.vue', '.svelte'
        }
        return Path(filename).suffix.lower() in code_extensions

    def _analyze_directory_structure(self, repository_path: str, file_list: List[str]) -> Dict[str, Any]:
        """Analyze repository directory structure"""
        structure = defaultdict(list)
        depth_analysis = defaultdict(int)
        
        for file_path in file_list:
            parts = Path(file_path).parts
            depth = len(parts) - 1  # Exclude filename
            depth_analysis[depth] += 1
            
            # Categorize by top-level directories
            if len(parts) > 1:
                top_dir = parts[0]
                structure[top_dir].append(file_path)
            else:
                structure["root"].append(file_path)
        
        return {
            "directories": dict(structure),
            "depth_analysis": dict(depth_analysis),
            "max_depth": max(depth_analysis.keys()) if depth_analysis else 0,
            "avg_depth": sum(k * v for k, v in depth_analysis.items()) / sum(depth_analysis.values()) if depth_analysis else 0,
            "total_files": len(file_list),
            "directory_count": len(structure)
        }

    def _detect_architectural_style(self, repository_path: str, file_list: List[str], 
                                  directory_structure: Dict[str, Any]) -> Tuple[ArchitecturalStyle, float]:
        """Detect primary architectural style"""
        style_scores = defaultdict(float)
        
        # Check directory indicators
        directories = set(directory_structure["directories"].keys())
        
        for style, indicators in self.directory_indicators.items():
            matches = len([ind for ind in indicators if any(ind.lower() in d.lower() for d in directories)])
            if matches > 0:
                style_scores[style] += matches / len(indicators)
        
        # Check file patterns
        for style, patterns in self.file_patterns.items():
            pattern_matches = 0
            total_patterns = len(patterns) - 1  # Exclude 'required_patterns'
            
            for pattern_type, pattern_list in patterns.items():
                if pattern_type == "required_patterns":
                    continue
                    
                for pattern in pattern_list:
                    if any(re.search(pattern, file_path, re.IGNORECASE) for file_path in file_list):
                        pattern_matches += 1
                        break
            
            if pattern_matches >= patterns.get("required_patterns", 1):
                style_scores[style] += pattern_matches / total_patterns
        
        # Special detection logic
        if self._detect_microservices_indicators(file_list):
            style_scores["microservices"] += 0.5
            
        if self._detect_mvc_structure(file_list):
            style_scores["mvc"] += 0.3
        
        # Determine primary style
        if style_scores:
            primary_style_name = max(style_scores.items(), key=lambda x: x[1])[0]
            confidence = min(1.0, style_scores[primary_style_name])
            
            # Map string to enum
            style_map = {
                "mvc": ArchitecturalStyle.MVC,
                "microservices": ArchitecturalStyle.MICROSERVICES,
                "clean_architecture": ArchitecturalStyle.CLEAN_ARCHITECTURE,
                "layered": ArchitecturalStyle.LAYERED,
                "component_based": ArchitecturalStyle.COMPONENT_BASED,
                "event_driven": ArchitecturalStyle.EVENT_DRIVEN
            }
            
            primary_style = style_map.get(primary_style_name, ArchitecturalStyle.MONOLITHIC)
        else:
            primary_style = ArchitecturalStyle.MONOLITHIC
            confidence = 0.5
        
        return primary_style, confidence

    def _detect_microservices_indicators(self, file_list: List[str]) -> bool:
        """Detect microservices architecture indicators"""
        indicators = [
            any("docker" in f.lower() for f in file_list),
            any("kubernetes" in f.lower() or "k8s" in f.lower() for f in file_list),
            any("service" in f.lower() for f in file_list),
            len([f for f in file_list if "api" in f.lower()]) > 2,
            any("gateway" in f.lower() for f in file_list)
        ]
        return sum(indicators) >= 2

    def _detect_mvc_structure(self, file_list: List[str]) -> bool:
        """Detect MVC structure"""
        has_controllers = any("controller" in f.lower() for f in file_list)
        has_models = any("model" in f.lower() for f in file_list)
        has_views = any(f.endswith(('.html', '.jsx', '.vue', '.template')) for f in file_list)
        
        return sum([has_controllers, has_models, has_views]) >= 2

    def _detect_design_patterns(self, repository_path: str, file_list: List[str]) -> List[PatternDetection]:
        """Detect design patterns in code"""
        detected_patterns = []
        
        for file_path in file_list:
            full_path = os.path.join(repository_path, file_path)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                language = self._detect_file_language(file_path)
                patterns = self._analyze_file_patterns(content, language, file_path)
                detected_patterns.extend(patterns)
                
            except Exception as e:
                logger.debug(f"Could not analyze file {file_path}: {e}")
        
        # Consolidate patterns
        return self._consolidate_pattern_detections(detected_patterns)

    def _detect_file_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'javascript',
            '.jsx': 'javascript',
            '.tsx': 'javascript',
            '.java': 'java',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c'
        }
        return lang_map.get(ext, 'unknown')

    def _analyze_file_patterns(self, content: str, language: str, file_path: str) -> List[PatternDetection]:
        """Analyze file content for design patterns"""
        patterns = []
        
        for pattern_type, language_patterns in self.code_patterns.items():
            if language in language_patterns:
                pattern_regexes = language_patterns[language]
                matches = []
                
                for regex in pattern_regexes:
                    if re.search(regex, content, re.MULTILINE | re.IGNORECASE):
                        matches.append(regex)
                
                if matches:
                    confidence = len(matches) / len(pattern_regexes)
                    
                    patterns.append(PatternDetection(
                        pattern=pattern_type,
                        confidence=confidence,
                        evidence=matches,
                        files_involved=[file_path],
                        description=self._get_pattern_description(pattern_type),
                        benefits=self._get_pattern_benefits(pattern_type),
                        potential_issues=self._get_pattern_issues(pattern_type)
                    ))
        
        return patterns

    def _consolidate_pattern_detections(self, detections: List[PatternDetection]) -> List[PatternDetection]:
        """Consolidate multiple detections of the same pattern"""
        pattern_groups = defaultdict(list)
        
        for detection in detections:
            pattern_groups[detection.pattern].append(detection)
        
        consolidated = []
        for pattern, group in pattern_groups.items():
            if len(group) == 1:
                consolidated.append(group[0])
            else:
                # Merge multiple detections
                all_evidence = []
                all_files = []
                total_confidence = 0
                
                for detection in group:
                    all_evidence.extend(detection.evidence)
                    all_files.extend(detection.files_involved)
                    total_confidence += detection.confidence
                
                avg_confidence = total_confidence / len(group)
                
                consolidated.append(PatternDetection(
                    pattern=pattern,
                    confidence=min(1.0, avg_confidence),
                    evidence=list(set(all_evidence)),
                    files_involved=list(set(all_files)),
                    description=group[0].description,
                    benefits=group[0].benefits,
                    potential_issues=group[0].potential_issues
                ))
        
        return consolidated

    def _analyze_architecture_quality(self, repository_path: str, file_list: List[str], 
                                    design_patterns: List[PatternDetection]) -> Dict[str, float]:
        """Analyze architecture quality metrics"""
        # Modularity: based on directory structure and file organization
        modularity = self._calculate_modularity(file_list)
        
        # Coupling: based on imports and dependencies
        coupling = self._calculate_coupling(repository_path, file_list)
        
        # Cohesion: based on file organization and pattern usage
        cohesion = self._calculate_cohesion(file_list, design_patterns)
        
        # Complexity: based on directory depth and file distribution
        complexity = self._calculate_complexity(file_list)
        
        # Overall score
        overall = (modularity + (1 - coupling) + cohesion + (1 - complexity)) / 4
        
        return {
            "overall_score": overall,
            "modularity": modularity,
            "coupling": coupling,
            "cohesion": cohesion,
            "complexity": complexity
        }

    def _calculate_modularity(self, file_list: List[str]) -> float:
        """Calculate modularity score based on file organization"""
        if not file_list:
            return 0.0
        
        # Count files per directory
        dir_counts = defaultdict(int)
        for file_path in file_list:
            directory = os.path.dirname(file_path) or "root"
            dir_counts[directory] += 1
        
        # Ideal: balanced distribution across modules
        total_files = len(file_list)
        total_dirs = len(dir_counts)
        
        if total_dirs == 1:
            return 0.3  # All files in one directory = low modularity
        
        ideal_files_per_dir = total_files / total_dirs
        variance = sum((count - ideal_files_per_dir) ** 2 for count in dir_counts.values()) / total_dirs
        
        # Normalize variance to 0-1 scale
        max_variance = (total_files ** 2) / total_dirs
        normalized_variance = variance / max_variance if max_variance > 0 else 0
        
        return max(0.0, 1.0 - normalized_variance)

    def _calculate_coupling(self, repository_path: str, file_list: List[str]) -> float:
        """Calculate coupling score based on imports and dependencies"""
        import_counts = []
        
        for file_path in file_list:
            full_path = os.path.join(repository_path, file_path)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Count imports/includes
                import_count = len(re.findall(r'^(import|from|#include|require\()', content, re.MULTILINE))
                import_counts.append(import_count)
                
            except Exception:
                import_counts.append(0)
        
        if not import_counts:
            return 0.0
        
        avg_imports = sum(import_counts) / len(import_counts)
        # Normalize: assume more than 20 imports = high coupling
        return min(1.0, avg_imports / 20.0)

    def _calculate_cohesion(self, file_list: List[str], design_patterns: List[PatternDetection]) -> float:
        """Calculate cohesion score"""
        # Base cohesion on directory organization
        dir_types = defaultdict(set)
        
        for file_path in file_list:
            directory = os.path.dirname(file_path) or "root"
            extension = Path(file_path).suffix.lower()
            dir_types[directory].add(extension)
        
        # Higher cohesion if directories contain similar file types
        cohesion_scores = []
        for directory, extensions in dir_types.items():
            if len(extensions) == 1:
                cohesion_scores.append(1.0)  # Perfect cohesion
            else:
                cohesion_scores.append(1.0 / len(extensions))  # Lower with more types
        
        base_cohesion = sum(cohesion_scores) / len(cohesion_scores) if cohesion_scores else 0.0
        
        # Bonus for good design patterns
        pattern_bonus = len(design_patterns) * 0.1
        
        return min(1.0, base_cohesion + pattern_bonus)

    def _calculate_complexity(self, file_list: List[str]) -> float:
        """Calculate complexity score based on structure"""
        if not file_list:
            return 0.0
        
        # Analyze directory depth
        depths = [len(Path(f).parts) - 1 for f in file_list]
        max_depth = max(depths) if depths else 0
        avg_depth = sum(depths) / len(depths) if depths else 0
        
        # Normalize complexity (assume depth > 5 is complex)
        depth_complexity = min(1.0, avg_depth / 5.0)
        
        # File count complexity
        file_complexity = min(1.0, len(file_list) / 100.0)  # 100+ files = complex
        
        return (depth_complexity + file_complexity) / 2

    def _build_dependency_graph(self, repository_path: str, file_list: List[str]) -> Dict[str, List[str]]:
        """Build dependency graph between modules"""
        dependencies = defaultdict(list)
        
        for file_path in file_list:
            full_path = os.path.join(repository_path, file_path)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract local imports/dependencies
                local_imports = self._extract_local_imports(content, file_path)
                dependencies[file_path] = local_imports
                
            except Exception:
                dependencies[file_path] = []
        
        return dict(dependencies)

    def _extract_local_imports(self, content: str, current_file: str) -> List[str]:
        """Extract local project imports from file content"""
        imports = []
        
        # Python imports
        python_imports = re.findall(r'from\s+\..*?\s+import|import\s+\..*', content)
        imports.extend(python_imports)
        
        # JavaScript imports
        js_imports = re.findall(r'import.*?from\s+[\'"]\..*?[\'"]', content)
        imports.extend(js_imports)
        
        # Java imports (package-relative)
        current_package = os.path.dirname(current_file).replace('/', '.')
        java_imports = re.findall(rf'import\s+{current_package}\..*?;', content)
        imports.extend(java_imports)
        
        return imports

    def _analyze_layers(self, directory_structure: Dict[str, Any], 
                       dependency_graph: Dict[str, List[str]]) -> Dict[str, Any]:
        """Analyze architectural layers"""
        directories = directory_structure["directories"]
        
        # Identify potential layers
        layer_indicators = {
            "presentation": ["view", "ui", "frontend", "web", "controller"],
            "business": ["service", "business", "domain", "logic", "usecase"],
            "data": ["data", "repository", "dao", "persistence", "model"],
            "infrastructure": ["config", "util", "common", "shared", "infrastructure"]
        }
        
        identified_layers = {}
        for layer, indicators in layer_indicators.items():
            matching_dirs = []
            for directory in directories.keys():
                if any(indicator in directory.lower() for indicator in indicators):
                    matching_dirs.append(directory)
            
            if matching_dirs:
                identified_layers[layer] = {
                    "directories": matching_dirs,
                    "file_count": sum(len(directories[d]) for d in matching_dirs)
                }
        
        return {
            "identified_layers": identified_layers,
            "layer_count": len(identified_layers),
            "is_layered": len(identified_layers) >= 2
        }

    def _generate_recommendations(self, primary_style: ArchitecturalStyle, 
                                design_patterns: List[PatternDetection],
                                quality_metrics: Dict[str, float],
                                layer_analysis: Dict[str, Any]) -> List[str]:
        """Generate architectural improvement recommendations"""
        recommendations = []
        
        # Quality-based recommendations
        if quality_metrics["modularity"] < 0.6:
            recommendations.append("🏗️ Improve modularity by organizing code into focused, single-responsibility modules")
        
        if quality_metrics["coupling"] > 0.7:
            recommendations.append("🔗 Reduce coupling by minimizing dependencies between modules")
        
        if quality_metrics["cohesion"] < 0.5:
            recommendations.append("🎯 Improve cohesion by grouping related functionality together")
        
        if quality_metrics["complexity"] > 0.7:
            recommendations.append("📊 Reduce complexity by simplifying directory structure and file organization")
        
        # Pattern-based recommendations
        pattern_types = [p.pattern for p in design_patterns]
        
        if DesignPattern.SINGLETON not in pattern_types and primary_style != ArchitecturalStyle.MICROSERVICES:
            recommendations.append("🔧 Consider implementing Singleton pattern for shared resources")
        
        if DesignPattern.REPOSITORY not in pattern_types:
            recommendations.append("📚 Consider implementing Repository pattern for data access abstraction")
        
        if DesignPattern.DEPENDENCY_INJECTION not in pattern_types:
            recommendations.append("💉 Consider implementing Dependency Injection for better testability")
        
        # Style-specific recommendations
        if primary_style == ArchitecturalStyle.MONOLITHIC:
            recommendations.append("🎯 Consider modularizing large monolithic components")
        elif primary_style == ArchitecturalStyle.MICROSERVICES:
            recommendations.append("🔍 Ensure proper service boundaries and communication patterns")
        
        # Layer-specific recommendations
        if not layer_analysis["is_layered"]:
            recommendations.append("📋 Consider implementing a layered architecture for better separation of concerns")
        
        return recommendations[:5]  # Top 5 recommendations

    def _get_pattern_description(self, pattern: DesignPattern) -> str:
        """Get description for design pattern"""
        descriptions = {
            DesignPattern.SINGLETON: "Ensures a class has only one instance and provides global access",
            DesignPattern.FACTORY: "Creates objects without specifying exact classes",
            DesignPattern.OBSERVER: "Defines one-to-many dependency between objects",
            DesignPattern.STRATEGY: "Defines family of algorithms and makes them interchangeable",
            DesignPattern.DECORATOR: "Attaches additional responsibilities to objects dynamically",
            DesignPattern.REPOSITORY: "Encapsulates logic needed to access data sources",
            DesignPattern.DEPENDENCY_INJECTION: "Provides dependencies to an object rather than having it create them"
        }
        return descriptions.get(pattern, "Design pattern for code organization")

    def _get_pattern_benefits(self, pattern: DesignPattern) -> List[str]:
        """Get benefits of design pattern"""
        benefits = {
            DesignPattern.SINGLETON: ["Global access", "Memory efficiency", "Lazy initialization"],
            DesignPattern.FACTORY: ["Loose coupling", "Easy to extend", "Centralized object creation"],
            DesignPattern.OBSERVER: ["Loose coupling", "Dynamic relationships", "Event-driven design"],
            DesignPattern.STRATEGY: ["Runtime algorithm selection", "Easy to extend", "Eliminates conditionals"],
            DesignPattern.DECORATOR: ["Flexible alternative to subclassing", "Runtime behavior modification"],
            DesignPattern.REPOSITORY: ["Data access abstraction", "Testability", "Centralized query logic"],
            DesignPattern.DEPENDENCY_INJECTION: ["Testability", "Loose coupling", "Configuration flexibility"]
        }
        return benefits.get(pattern, ["Improved code organization"])

    def _get_pattern_issues(self, pattern: DesignPattern) -> List[str]:
        """Get potential issues with design pattern"""
        issues = {
            DesignPattern.SINGLETON: ["Global state", "Testing difficulties", "Thread safety concerns"],
            DesignPattern.FACTORY: ["Increased complexity", "Many small classes"],
            DesignPattern.OBSERVER: ["Memory leaks", "Performance overhead", "Debugging difficulty"],
            DesignPattern.STRATEGY: ["Increased number of classes", "Client awareness of strategies"],
            DesignPattern.DECORATOR: ["Many small objects", "Complexity in debugging"],
            DesignPattern.REPOSITORY: ["Abstraction overhead", "Potential over-engineering"],
            DesignPattern.DEPENDENCY_INJECTION: ["Configuration complexity", "Runtime errors"]
        }
        return issues.get(pattern, ["Potential over-engineering"])

    def _create_fallback_analysis(self) -> ArchitecturalAnalysis:
        """Create fallback analysis when detection fails"""
        return ArchitecturalAnalysis(
            primary_style=ArchitecturalStyle.MONOLITHIC,
            confidence=0.1,
            design_patterns=[],
            architecture_quality_score=0.5,
            modularity_score=0.5,
            coupling_score=0.5,
            cohesion_score=0.5,
            complexity_score=0.5,
            recommendations=["Manual architectural review recommended"],
            directory_structure={},
            dependency_graph={},
            layer_analysis={"identified_layers": {}, "layer_count": 0, "is_layered": False}
        )

    def generate_architecture_report(self, analysis: ArchitecturalAnalysis) -> Dict[str, Any]:
        """Generate comprehensive architecture report"""
        return {
            "architectural_style": {
                "primary": analysis.primary_style.value,
                "confidence": analysis.confidence,
                "description": self._get_style_description(analysis.primary_style)
            },
            "design_patterns": [
                {
                    "pattern": p.pattern.value,
                    "confidence": p.confidence,
                    "description": p.description,
                    "files_count": len(p.files_involved),
                    "benefits": p.benefits,
                    "potential_issues": p.potential_issues
                }
                for p in analysis.design_patterns
            ],
            "quality_metrics": {
                "overall_score": analysis.architecture_quality_score,
                "modularity": analysis.modularity_score,
                "coupling": analysis.coupling_score,
                "cohesion": analysis.cohesion_score,
                "complexity": analysis.complexity_score,
                "grade": self._calculate_grade(analysis.architecture_quality_score)
            },
            "structure_analysis": {
                "total_files": analysis.directory_structure.get("total_files", 0),
                "directory_count": analysis.directory_structure.get("directory_count", 0),
                "max_depth": analysis.directory_structure.get("max_depth", 0),
                "avg_depth": analysis.directory_structure.get("avg_depth", 0),
                "is_layered": analysis.layer_analysis.get("is_layered", False),
                "layer_count": analysis.layer_analysis.get("layer_count", 0)
            },
            "recommendations": analysis.recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _get_style_description(self, style: ArchitecturalStyle) -> str:
        """Get description for architectural style"""
        descriptions = {
            ArchitecturalStyle.MONOLITHIC: "Single deployable unit with all functionality",
            ArchitecturalStyle.MICROSERVICES: "Distributed architecture with independent services",
            ArchitecturalStyle.MVC: "Model-View-Controller pattern separating concerns",
            ArchitecturalStyle.LAYERED: "Hierarchical organization of components",
            ArchitecturalStyle.CLEAN_ARCHITECTURE: "Dependency rule with business logic at center",
            ArchitecturalStyle.EVENT_DRIVEN: "Asynchronous communication through events"
        }
        return descriptions.get(style, "Architectural pattern for organizing code")

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"


# Convenience function for service integration
def get_architectural_analyzer() -> ArchitecturalAnalyzer:
    """Get ArchitecturalAnalyzer instance"""
    return ArchitecturalAnalyzer()