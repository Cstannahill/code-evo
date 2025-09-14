# Enhanced Pattern Detection Service
"""
Advanced pattern detection system that identifies:
- Design patterns (GoF, architectural, etc.)
- Code quality patterns and anti-patterns
- Performance patterns and bottlenecks
- Security patterns and vulnerabilities
- Modern development patterns
- Framework-specific patterns
"""

import re
import logging
import ast
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """Represents a detected pattern match"""
    pattern_name: str
    category: str
    confidence: float
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    severity: str = "info"  # info, warning, error
    suggestion: Optional[str] = None
    complexity_score: Optional[float] = None


class EnhancedPatternDetector:
    """
    Advanced pattern detection with semantic analysis,
    confidence scoring, and comprehensive pattern databases.
    """

    def __init__(self):
        """Initialize with comprehensive pattern databases"""
        self.design_patterns = self._load_design_patterns()
        self.quality_patterns = self._load_quality_patterns()
        self.performance_patterns = self._load_performance_patterns()
        self.security_patterns = self._load_security_patterns()
        self.modern_patterns = self._load_modern_patterns()
        self.antipatterns = self._load_antipatterns()
        
        logger.info("EnhancedPatternDetector initialized with comprehensive pattern databases")

    def _load_design_patterns(self) -> Dict[str, Dict]:
        """Load Gang of Four and architectural design patterns"""
        return {
            "creational": {
                "singleton": {
                    "patterns": [
                        r"class\s+\w+.*:\s*\n.*__instance\s*=\s*None",
                        r"def\s+__new__\s*\(cls\):\s*\n.*if\s+cls\.__instance\s+is\s+None",
                        r"private\s+static\s+\w+\s+instance\s*=\s*null",
                        r"getInstance\s*\(\s*\)\s*\{[\s\S]*?if\s*\(\s*instance\s*==\s*null\s*\)",
                        r"export\s+default\s+new\s+\w+\s*\(\s*\)"
                    ],
                    "description": "Singleton pattern - ensures only one instance exists",
                    "benefits": ["Global access point", "Lazy initialization", "Memory efficiency"],
                    "complexity": "intermediate"
                },
                "factory": {
                    "patterns": [
                        r"class\s+\w+Factory.*:\s*\n.*def\s+create\w+\s*\(",
                        r"interface\s+\w+Factory\s*\{[\s\S]*?create\w+\s*\(",
                        r"static\s+\w+\s+create\w+\s*\(",
                        r"export\s+const\s+create\w+\s*=\s*\("
                    ],
                    "description": "Factory pattern - creates objects without specifying exact classes",
                    "benefits": ["Loose coupling", "Extensibility", "Centralized creation"],
                    "complexity": "intermediate"
                },
                "builder": {
                    "patterns": [
                        r"class\s+\w+Builder.*:\s*\n.*def\s+with\w+\s*\(",
                        r"\.with\w+\s*\([^)]*\)\s*\.with\w+\s*\(",
                        r"return\s+this\s*;",
                        r"chain\s*=\s*true"
                    ],
                    "description": "Builder pattern - constructs complex objects step by step",
                    "benefits": ["Flexible construction", "Readable code", "Immutable objects"],
                    "complexity": "intermediate"
                }
            },
            
            "structural": {
                "adapter": {
                    "patterns": [
                        r"class\s+\w+Adapter.*:\s*\n.*def\s+adapt\w*\s*\(",
                        r"implements\s+\w+Target\s*\{[\s\S]*?adapt\w*\s*\(",
                        r"\.adapt\w*\s*\(",
                        r"wrapper.*class"
                    ],
                    "description": "Adapter pattern - allows incompatible interfaces to work together",
                    "benefits": ["Interface compatibility", "Reusability", "Legacy integration"],
                    "complexity": "intermediate"
                },
                "decorator": {
                    "patterns": [
                        r"@\w+\s*\n\s*def\s+\w+\s*\(",
                        r"class\s+\w+Decorator.*:\s*\n.*def\s+__call__\s*\(",
                        r"decorator\s*\(\s*\w+\s*\)",
                        r"\.decorate\s*\("
                    ],
                    "description": "Decorator pattern - adds behavior to objects dynamically",
                    "benefits": ["Flexible enhancement", "Single responsibility", "Composition over inheritance"],
                    "complexity": "advanced"
                },
                "facade": {
                    "patterns": [
                        r"class\s+\w+Facade.*:\s*\n.*def\s+simplify\w*\s*\(",
                        r"interface\s+\w+Facade\s*\{[\s\S]*?simplify\w*\s*\(",
                        r"\.facade\s*\(",
                        r"unified\s+interface"
                    ],
                    "description": "Facade pattern - provides simplified interface to complex subsystem",
                    "benefits": ["Simplified interface", "Loose coupling", "Easier maintenance"],
                    "complexity": "intermediate"
                }
            },
            
            "behavioral": {
                "observer": {
                    "patterns": [
                        r"class\s+\w+Observer.*:\s*\n.*def\s+update\s*\(",
                        r"interface\s+\w+Observer\s*\{[\s\S]*?update\s*\(",
                        r"\.notify\w*\s*\(",
                        r"\.subscribe\s*\(",
                        r"\.addEventListener\s*\("
                    ],
                    "description": "Observer pattern - defines one-to-many dependency between objects",
                    "benefits": ["Loose coupling", "Dynamic relationships", "Event handling"],
                    "complexity": "intermediate"
                },
                "strategy": {
                    "patterns": [
                        r"interface\s+\w+Strategy\s*\{[\s\S]*?execute\s*\(",
                        r"class\s+\w+Strategy.*:\s*\n.*def\s+execute\s*\(",
                        r"\.strategy\s*\.execute\s*\(",
                        r"\.setStrategy\s*\("
                    ],
                    "description": "Strategy pattern - defines family of algorithms and makes them interchangeable",
                    "benefits": ["Algorithm flexibility", "Runtime selection", "Eliminates conditionals"],
                    "complexity": "intermediate"
                },
                "command": {
                    "patterns": [
                        r"interface\s+\w+Command\s*\{[\s\S]*?execute\s*\(",
                        r"class\s+\w+Command.*:\s*\n.*def\s+execute\s*\(",
                        r"\.execute\s*\(",
                        r"\.undo\s*\("
                    ],
                    "description": "Command pattern - encapsulates requests as objects",
                    "benefits": ["Request queuing", "Undo functionality", "Macro commands"],
                    "complexity": "intermediate"
                }
            }
        }

    def _load_quality_patterns(self) -> Dict[str, Dict]:
        """Load code quality patterns"""
        return {
            "positive": {
                "clean_code": {
                    "patterns": [
                        r"def\s+\w+\s*\([^)]*\):\s*\n\s*\"\"\".*\"\"\"",  # Docstrings
                        r"const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*\{",  # Arrow functions
                        r"async\s+function\s+\w+\s*\(",  # Async/await
                        r"try:\s*\n[\s\S]*?except\s+\w+:",  # Error handling
                        r"class\s+\w+\s*\([^)]*\):\s*\n\s*\"\"\".*\"\"\"",  # Class docstrings
                    ],
                    "description": "Clean code practices - readable, maintainable code",
                    "benefits": ["Readability", "Maintainability", "Team collaboration"],
                    "severity": "info"
                },
                "solid_principles": {
                    "patterns": [
                        r"interface\s+\w+\s*\{",  # Interface segregation
                        r"abstract\s+class\s+\w+\s*\{",  # Dependency inversion
                        r"class\s+\w+\s+implements\s+\w+",  # Single responsibility
                        r"private\s+\w+\s+",  # Encapsulation
                        r"final\s+class\s+\w+\s*\{",  # Open/closed principle
                    ],
                    "description": "SOLID principles - object-oriented design principles",
                    "benefits": ["Flexible design", "Maintainable code", "Testable architecture"],
                    "severity": "info"
                },
                "functional_programming": {
                    "patterns": [
                        r"\.map\s*\([^)]*\)",  # Map function
                        r"\.filter\s*\([^)]*\)",  # Filter function
                        r"\.reduce\s*\([^)]*\)",  # Reduce function
                        r"const\s+\w+\s*=\s*\([^)]*\)\s*=>",  # Pure functions
                        r"immutable",  # Immutability
                        r"\.pipe\s*\(",  # Function composition
                    ],
                    "description": "Functional programming patterns - declarative, immutable code",
                    "benefits": ["Predictability", "Testability", "Concurrency safety"],
                    "severity": "info"
                }
            },
            "negative": {
                "code_smells": {
                    "patterns": [
                        r"if\s+.*\s+and\s+.*\s+and\s+.*\s+and\s+",  # Long conditions
                        r"function\s+\w+\s*\([^)]{100,}\)",  # Too many parameters
                        r"for\s*\([^)]*\)\s*\{[\s\S]{500,}\}",  # Long functions
                        r"var\s+\w+\s*=\s*\w+\s*;\s*var\s+\w+\s*=\s*\w+\s*;",  # Variable declarations
                        r"TODO\s*:|FIXME\s*:|HACK\s*:",  # Technical debt
                    ],
                    "description": "Code smells - indicators of deeper problems",
                    "benefits": ["Early problem detection", "Code improvement opportunities"],
                    "severity": "warning"
                },
                "duplicate_code": {
                    "patterns": [
                        r"def\s+\w+\s*\([^)]*\):\s*\n[\s\S]{50,}\ndef\s+\w+\s*\([^)]*\):\s*\n[\s\S]{50,}",  # Similar functions
                        r"if\s+.*:\s*\n[\s\S]{20,}\nif\s+.*:\s*\n[\s\S]{20,}",  # Repeated conditions
                        r"class\s+\w+\s*\{[\s\S]{100,}\}\s*class\s+\w+\s*\{[\s\S]{100,}\}",  # Similar classes
                    ],
                    "description": "Duplicate code - repeated code blocks",
                    "benefits": ["DRY principle", "Maintainability", "Consistency"],
                    "severity": "warning"
                }
            }
        }

    def _load_performance_patterns(self) -> Dict[str, Dict]:
        """Load performance-related patterns"""
        return {
            "optimizations": {
                "lazy_loading": {
                    "patterns": [
                        r"lazy\s*\(\s*\(\)\s*=>\s*import\s*\(",
                        r"React\.lazy\s*\(",
                        r"\.lazy\s*\(",
                        r"dynamic\s+import\s*\(",
                        r"require\.ensure\s*\("
                    ],
                    "description": "Lazy loading - loads resources only when needed",
                    "benefits": ["Faster initial load", "Memory efficiency", "Better UX"],
                    "severity": "info"
                },
                "memoization": {
                    "patterns": [
                        r"React\.memo\s*\(",
                        r"useMemo\s*\(",
                        r"useCallback\s*\(",
                        r"@memoize",
                        r"\.memoize\s*\(",
                        r"functools\.lru_cache"
                    ],
                    "description": "Memoization - caches function results",
                    "benefits": ["Performance optimization", "Reduced computation", "Faster execution"],
                    "severity": "info"
                },
                "pagination": {
                    "patterns": [
                        r"\.skip\s*\(\s*\d+\s*\)\s*\.limit\s*\(",
                        r"OFFSET\s+\d+\s+LIMIT\s+\d+",
                        r"\.slice\s*\(\s*\d+\s*,\s*\d+\s*\)",
                        r"page\s*=\s*\d+",
                        r"cursor\s*="
                    ],
                    "description": "Pagination - handles large datasets efficiently",
                    "benefits": ["Memory efficiency", "Faster queries", "Better UX"],
                    "severity": "info"
                }
            },
            "bottlenecks": {
                "n_plus_one": {
                    "patterns": [
                        r"for\s+\w+\s+in\s+\w+:\s*\n\s*\w+\.query\s*\(",
                        r"forEach\s*\([^)]*\)\s*\{[\s\S]*?\.query\s*\(",
                        r"while\s*\([^)]*\)\s*\{[\s\S]*?SELECT",
                        r"\.map\s*\([^)]*\)\s*\.query\s*\("
                    ],
                    "description": "N+1 query problem - executes queries in loops",
                    "benefits": ["Database optimization", "Performance improvement"],
                    "severity": "error"
                },
                "inefficient_loops": {
                    "patterns": [
                        r"for\s*\([^)]*\)\s*\{[\s\S]*?for\s*\([^)]*\)\s*\{[\s\S]*?for\s*\([^)]*\)\s*\{",  # Nested loops
                        r"\.indexOf\s*\([^)]*\)\s*!=\s*-1",  # Inefficient search
                        r"\.split\s*\([^)]*\)\[0\]",  # Unnecessary split
                        r"JSON\.parse\s*\([^)]*\)\s*in\s+loop",  # Parse in loop
                    ],
                    "description": "Inefficient loops - performance bottlenecks",
                    "benefits": ["Performance optimization", "Better algorithms"],
                    "severity": "warning"
                }
            }
        }

    def _load_security_patterns(self) -> Dict[str, Dict]:
        """Load security-related patterns"""
        return {
            "vulnerabilities": {
                "sql_injection": {
                    "patterns": [
                        r"SELECT\s+.*\+.*['\"]",
                        r"INSERT\s+.*\+.*['\"]",
                        r"UPDATE\s+.*\+.*['\"]",
                        r"DELETE\s+.*\+.*['\"]",
                        r"cursor\.execute\s*\(\s*['\"][^'\"]*['\"].+\+.+\)",
                        r"Statement.*executeQuery\s*\([^?]*\+"
                    ],
                    "description": "SQL injection vulnerability - dynamic query construction",
                    "benefits": ["Security improvement", "Data protection"],
                    "severity": "error"
                },
                "xss": {
                    "patterns": [
                        r"innerHTML\s*=\s*[^;]*\+",
                        r"document\.write\s*\([^)]*\+",
                        r"\.html\s*\([^)]*\+",
                        r"dangerouslySetInnerHTML",
                        r"eval\s*\("
                    ],
                    "description": "Cross-site scripting vulnerability",
                    "benefits": ["Security improvement", "XSS prevention"],
                    "severity": "error"
                },
                "hardcoded_secrets": {
                    "patterns": [
                        r"password\s*=\s*['\"][^'\"]{8,}['\"]",
                        r"api_key\s*=\s*['\"][^'\"]{20,}['\"]",
                        r"secret\s*=\s*['\"][^'\"]{10,}['\"]",
                        r"token\s*=\s*['\"][^'\"]{20,}['\"]",
                        r"AWS_SECRET_ACCESS_KEY\s*=",
                        r"PRIVATE_KEY\s*="
                    ],
                    "description": "Hardcoded secrets - sensitive data in code",
                    "benefits": ["Security improvement", "Secret management"],
                    "severity": "error"
                }
            },
            "best_practices": {
                "input_validation": {
                    "patterns": [
                        r"validate\s*\([^)]*\)",
                        r"sanitize\s*\([^)]*\)",
                        r"\.isEmail\s*\(",
                        r"\.isLength\s*\(",
                        r"\.matches\s*\(",
                        r"validator\."
                    ],
                    "description": "Input validation - validates and sanitizes user input",
                    "benefits": ["Security improvement", "Data integrity"],
                    "severity": "info"
                },
                "authentication": {
                    "patterns": [
                        r"bcrypt\.",
                        r"jwt\.",
                        r"passport\.",
                        r"oauth\.",
                        r"session\.",
                        r"middleware.*auth"
                    ],
                    "description": "Authentication patterns - secure user authentication",
                    "benefits": ["Security improvement", "User management"],
                    "severity": "info"
                }
            }
        }

    def _load_modern_patterns(self) -> Dict[str, Dict]:
        """Load modern development patterns"""
        return {
            "microservices": {
                "patterns": [
                    r"@RestController",
                    r"@Service",
                    r"@Repository",
                    r"@Component",
                    r"@Microservice",
                    r"@EnableEurekaClient",
                    r"docker-compose",
                    r"kubernetes"
                ],
                "description": "Microservices architecture patterns",
                "benefits": ["Scalability", "Independence", "Technology diversity"],
                "complexity": "advanced"
            },
            "reactive": {
                "patterns": [
                    r"Observable\.",
                    r"\.subscribe\s*\(",
                    r"\.map\s*\([^)]*\)\s*\.filter\s*\(",
                    r"@Reactive",
                    r"Flux\.",
                    r"Mono\.",
                    r"\.flatMap\s*\("
                ],
                "description": "Reactive programming patterns",
                "benefits": ["Asynchronous processing", "Backpressure handling", "Composability"],
                "complexity": "advanced"
            },
            "serverless": {
                "patterns": [
                    r"@Function",
                    r"exports\.handler\s*=",
                    r"lambda\s+function",
                    r"serverless\.",
                    r"@aws_lambda",
                    r"vercel\.",
                    r"netlify\."
                ],
                "description": "Serverless architecture patterns",
                "benefits": ["Cost efficiency", "Auto-scaling", "No server management"],
                "complexity": "intermediate"
            }
        }

    def _load_antipatterns(self) -> Dict[str, Dict]:
        """Load common antipatterns"""
        return {
            "god_object": {
                "patterns": [
                    r"class\s+\w+\s*\{[\s\S]{1000,}\}",  # Very large classes
                    r"def\s+\w+\s*\([^)]*\):\s*\n[\s\S]{200,}",  # Very large methods
                    r"class\s+\w+\s*\{[\s\S]*?def\s+\w+[\s\S]*?def\s+\w+[\s\S]*?def\s+\w+[\s\S]*?def\s+\w+[\s\S]*?def\s+\w+",  # Too many methods
                ],
                "description": "God object - classes/methods that do too much",
                "benefits": ["Single responsibility", "Maintainability", "Testability"],
                "severity": "warning"
            },
            "spaghetti_code": {
                "patterns": [
                    r"goto\s+\w+",  # Goto statements
                    r"if\s+.*:\s*\n[\s\S]*?else:\s*\n[\s\S]*?if\s+.*:\s*\n[\s\S]*?else:\s*\n[\s\S]*?if\s+.*:",  # Deep nesting
                    r"while\s+.*:\s*\n[\s\S]*?while\s+.*:\s*\n[\s\S]*?while\s+.*:",  # Nested loops
                ],
                "description": "Spaghetti code - complex, tangled code structure",
                "benefits": ["Code clarity", "Maintainability", "Debugging"],
                "severity": "warning"
            },
            "copy_paste": {
                "patterns": [
                    r"def\s+\w+\s*\([^)]*\):\s*\n[\s\S]{50,}\ndef\s+\w+\s*\([^)]*\):\s*\n[\s\S]{50,}",  # Similar functions
                    r"class\s+\w+\s*\{[\s\S]{100,}\}\s*class\s+\w+\s*\{[\s\S]{100,}\}",  # Similar classes
                ],
                "description": "Copy-paste programming - duplicated code",
                "benefits": ["DRY principle", "Maintainability", "Consistency"],
                "severity": "warning"
            }
        }

    def detect_patterns(self, repo_path: str, file_list: List[str]) -> Dict[str, List[PatternMatch]]:
        """
        Comprehensive pattern detection for a repository
        
        Args:
            repo_path: Path to the repository
            file_list: List of file paths in the repository
            
        Returns:
            Dictionary of detected patterns by category
        """
        detected_patterns = defaultdict(list)
        
        try:
            # Analyze source files
            source_files = [f for f in file_list if self._is_source_file(f)]
            
            for file_path in source_files[:100]:  # Limit for performance
                full_path = Path(repo_path) / file_path
                
                if not full_path.exists():
                    continue
                    
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Detect different pattern categories
                    design_matches = self._detect_design_patterns(content, file_path)
                    quality_matches = self._detect_quality_patterns(content, file_path)
                    performance_matches = self._detect_performance_patterns(content, file_path)
                    security_matches = self._detect_security_patterns(content, file_path)
                    modern_matches = self._detect_modern_patterns(content, file_path)
                    antipattern_matches = self._detect_antipatterns(content, file_path)
                    
                    # Combine all matches
                    all_matches = (design_matches + quality_matches + performance_matches + 
                                 security_matches + modern_matches + antipattern_matches)
                    
                    for match in all_matches:
                        detected_patterns[match.category].append(match)
                        
                except Exception as e:
                    logger.debug(f"Error analyzing file {file_path}: {e}")
            
            # Remove duplicates and rank by confidence
            for category in detected_patterns:
                detected_patterns[category] = self._deduplicate_and_rank_patterns(
                    detected_patterns[category]
                )
            
            logger.info(f"Detected {sum(len(matches) for matches in detected_patterns.values())} patterns")
            return dict(detected_patterns)
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return {}

    def _detect_design_patterns(self, content: str, file_path: str) -> List[PatternMatch]:
        """Detect design patterns in code"""
        matches = []
        lines = content.split('\n')
        
        for category, patterns in self.design_patterns.items():
            for pattern_name, pattern_info in patterns.items():
                for pattern_regex in pattern_info["patterns"]:
                    for i, line in enumerate(lines):
                        if re.search(pattern_regex, line, re.IGNORECASE | re.MULTILINE):
                            matches.append(PatternMatch(
                                pattern_name=pattern_name.replace("_", " ").title(),
                                category=f"design_patterns_{category}",
                                confidence=0.8,
                                file_path=file_path,
                                line_number=i + 1,
                                code_snippet=line.strip()[:100],
                                description=pattern_info["description"],
                                complexity_score=self._calculate_complexity_score(pattern_info.get("complexity", "intermediate"))
                            ))
        
        return matches

    def _detect_quality_patterns(self, content: str, file_path: str) -> List[PatternMatch]:
        """Detect code quality patterns"""
        matches = []
        lines = content.split('\n')
        
        for category, patterns in self.quality_patterns.items():
            for pattern_name, pattern_info in patterns.items():
                for pattern_regex in pattern_info["patterns"]:
                    for i, line in enumerate(lines):
                        if re.search(pattern_regex, line, re.IGNORECASE | re.MULTILINE):
                            matches.append(PatternMatch(
                                pattern_name=pattern_name.replace("_", " ").title(),
                                category=f"quality_patterns_{category}",
                                confidence=0.7,
                                file_path=file_path,
                                line_number=i + 1,
                                code_snippet=line.strip()[:100],
                                description=pattern_info["description"],
                                severity=pattern_info.get("severity", "info")
                            ))
        
        return matches

    def _detect_performance_patterns(self, content: str, file_path: str) -> List[PatternMatch]:
        """Detect performance patterns"""
        matches = []
        lines = content.split('\n')
        
        for category, patterns in self.performance_patterns.items():
            for pattern_name, pattern_info in patterns.items():
                for pattern_regex in pattern_info["patterns"]:
                    for i, line in enumerate(lines):
                        if re.search(pattern_regex, line, re.IGNORECASE | re.MULTILINE):
                            matches.append(PatternMatch(
                                pattern_name=pattern_name.replace("_", " ").title(),
                                category=f"performance_patterns_{category}",
                                confidence=0.8,
                                file_path=file_path,
                                line_number=i + 1,
                                code_snippet=line.strip()[:100],
                                description=pattern_info["description"],
                                severity=pattern_info.get("severity", "info")
                            ))
        
        return matches

    def _detect_security_patterns(self, content: str, file_path: str) -> List[PatternMatch]:
        """Detect security patterns"""
        matches = []
        lines = content.split('\n')
        
        for category, patterns in self.security_patterns.items():
            for pattern_name, pattern_info in patterns.items():
                for pattern_regex in pattern_info["patterns"]:
                    for i, line in enumerate(lines):
                        if re.search(pattern_regex, line, re.IGNORECASE | re.MULTILINE):
                            matches.append(PatternMatch(
                                pattern_name=pattern_name.replace("_", " ").title(),
                                category=f"security_patterns_{category}",
                                confidence=0.9,
                                file_path=file_path,
                                line_number=i + 1,
                                code_snippet=line.strip()[:100],
                                description=pattern_info["description"],
                                severity=pattern_info.get("severity", "error")
                            ))
        
        return matches

    def _detect_modern_patterns(self, content: str, file_path: str) -> List[PatternMatch]:
        """Detect modern development patterns"""
        matches = []
        lines = content.split('\n')
        
        for pattern_name, pattern_info in self.modern_patterns.items():
            for pattern_regex in pattern_info["patterns"]:
                for i, line in enumerate(lines):
                    if re.search(pattern_regex, line, re.IGNORECASE | re.MULTILINE):
                        matches.append(PatternMatch(
                            pattern_name=pattern_name.replace("_", " ").title(),
                            category="modern_patterns",
                            confidence=0.8,
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip()[:100],
                            description=pattern_info["description"],
                            complexity_score=self._calculate_complexity_score(pattern_info.get("complexity", "intermediate"))
                        ))
        
        return matches

    def _detect_antipatterns(self, content: str, file_path: str) -> List[PatternMatch]:
        """Detect antipatterns"""
        matches = []
        lines = content.split('\n')
        
        for pattern_name, pattern_info in self.antipatterns.items():
            for pattern_regex in pattern_info["patterns"]:
                for i, line in enumerate(lines):
                    if re.search(pattern_regex, line, re.IGNORECASE | re.MULTILINE):
                        matches.append(PatternMatch(
                            pattern_name=pattern_name.replace("_", " ").title(),
                            category="antipatterns",
                            confidence=0.8,
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip()[:100],
                            description=pattern_info["description"],
                            severity=pattern_info.get("severity", "warning")
                        ))
        
        return matches

    def _is_source_file(self, file_path: str) -> bool:
        """Check if file is a source code file"""
        source_extensions = {
            '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.cs',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.clj',
            '.hs', '.ml', '.fs', '.dart', '.vue', '.svelte'
        }
        
        return Path(file_path).suffix.lower() in source_extensions

    def _calculate_complexity_score(self, complexity: str) -> float:
        """Calculate complexity score based on complexity level"""
        complexity_map = {
            "simple": 1.0,
            "intermediate": 2.0,
            "advanced": 3.0
        }
        return complexity_map.get(complexity, 2.0)

    def _deduplicate_and_rank_patterns(self, pattern_list: List[PatternMatch]) -> List[PatternMatch]:
        """Remove duplicates and rank by confidence"""
        seen = set()
        unique_patterns = []
        
        for pattern in pattern_list:
            key = (pattern.pattern_name, pattern.file_path, pattern.line_number)
            if key not in seen:
                seen.add(key)
                unique_patterns.append(pattern)
        
        # Sort by confidence (descending)
        return sorted(unique_patterns, key=lambda x: x.confidence, reverse=True)
