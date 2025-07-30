# app/services/security_analyzer.py - Security Pattern Detection Service
"""
Security Analyzer for Code Evolution Tracker

This service provides comprehensive security vulnerability detection using
pattern matching, static analysis, and AI-powered assessment.

🔒 FRONTEND UPDATE NEEDED: New security analysis data structure requires:
- Security score display in metrics
- Vulnerability categorization in charts  
- Security timeline and trends
- Risk assessment dashboard
"""

import re
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecuritySeverity(Enum):
    """Security issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityCategory(Enum):
    """Security vulnerability categories"""
    INJECTION = "injection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CRYPTOGRAPHY = "cryptography"
    INPUT_VALIDATION = "input_validation"
    OUTPUT_ENCODING = "output_encoding"
    SESSION_MANAGEMENT = "session_management"
    ERROR_HANDLING = "error_handling"
    LOGGING_MONITORING = "logging_monitoring"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    CODE_QUALITY = "code_quality"


@dataclass
class SecurityVulnerability:
    """Security vulnerability detection result"""
    id: str
    name: str
    description: str
    severity: SecuritySeverity
    category: SecurityCategory
    cwe_id: Optional[str]
    owasp_category: Optional[str]
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str
    confidence: float
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None


class SecurityAnalyzer:
    """
    Comprehensive security vulnerability analyzer supporting multiple languages
    and security frameworks with OWASP Top 10 coverage.
    """

    def __init__(self):
        """Initialize security analyzer with comprehensive pattern databases"""
        self.patterns = self._load_security_patterns()
        self.crypto_patterns = self._load_crypto_patterns()
        self.dependency_patterns = self._load_dependency_patterns()
        
        logger.info("SecurityAnalyzer initialized with comprehensive pattern database")

    def _load_security_patterns(self) -> Dict[str, Dict]:
        """Load comprehensive security patterns for multiple languages"""
        return {
            "sql_injection": {
                "patterns": [
                    r"(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+.*\+.*['\"]",
                    r"(?i)cursor\.execute\s*\(\s*['\"][^'\"]*['\"].+\+.+\)",
                    r"(?i)query\s*=.*\+.*['\"]",
                    r"(?i)Statement.*executeQuery\s*\([^?]*\+",
                    r"(?i)PreparedStatement.*setString\(\d+,.*\+.*\)"
                ],
                "severity": SecuritySeverity.HIGH,
                "category": SecurityCategory.INJECTION,
                "cwe": "CWE-89",
                "owasp": "A03:2021-Injection",
                "description": "SQL injection vulnerability through dynamic query construction",
                "recommendation": "Use parameterized queries, prepared statements, or ORM methods"
            },
            
            "command_injection": {
                "patterns": [
                    r"(?i)(exec|system|shell_exec|passthru|popen|proc_open)\s*\([^)]*\$",
                    r"(?i)subprocess\.(run|call|check_output|Popen).*shell\s*=\s*True",
                    r"(?i)os\.(system|popen|exec)\s*\([^)]*\+",
                    r"(?i)Runtime\.getRuntime\(\)\.exec\s*\([^)]*\+",
                    r"(?i)Process\.Start\s*\([^)]*\+.*\)"
                ],
                "severity": SecuritySeverity.CRITICAL,
                "category": SecurityCategory.INJECTION,
                "cwe": "CWE-78",
                "owasp": "A03:2021-Injection",
                "description": "Command injection vulnerability",
                "recommendation": "Validate and sanitize input, use safe APIs, avoid shell execution"
            },
            
            "xss_vulnerability": {
                "patterns": [
                    r"(?i)innerHTML\s*=.*\+",
                    r"(?i)document\.write\s*\([^)]*\+",
                    r"(?i)eval\s*\([^)]*\+",
                    r"(?i)echo\s+.*\$_(GET|POST|REQUEST)",
                    r"(?i)print\s*\([^)]*\+.*request\.",
                    r"(?i)response\.write\s*\([^)]*\+"
                ],
                "severity": SecuritySeverity.HIGH,
                "category": SecurityCategory.OUTPUT_ENCODING,
                "cwe": "CWE-79",
                "owasp": "A03:2021-Injection",
                "description": "Cross-site scripting (XSS) vulnerability",
                "recommendation": "Sanitize and encode output, use templating engines, CSP headers"
            },
            
            "hardcoded_secrets": {
                "patterns": [
                    r"(?i)(password|secret|key|token|api_key)\s*=\s*['\"][^'\"]{8,}['\"]",
                    r"(?i)(aws_access_key|aws_secret|github_token)\s*=\s*['\"][^'\"]+['\"]",
                    r"(?i)conn\s*=.*password\s*=\s*['\"][^'\"]+['\"]",
                    r"['\"][A-Za-z0-9]{20,}['\"].*(?i)(key|secret|token)",
                    r"(?i)private_key\s*=\s*['\"]-----BEGIN"
                ],
                "severity": SecuritySeverity.CRITICAL,
                "category": SecurityCategory.CRYPTOGRAPHY,
                "cwe": "CWE-798",
                "owasp": "A07:2021-Identification and Authentication Failures",
                "description": "Hardcoded secrets or credentials in source code",
                "recommendation": "Use environment variables, secure credential storage, key management systems"
            },
            
            "weak_crypto": {
                "patterns": [
                    r"(?i)(md5|sha1|des|rc4)\s*\(",
                    r"(?i)MessageDigest\.getInstance\s*\(\s*['\"]MD5['\"]",
                    r"(?i)hashlib\.(md5|sha1)\s*\(",
                    r"(?i)CryptoJS\.(MD5|SHA1)",
                    r"(?i)Random\(\)\.next"
                ],
                "severity": SecuritySeverity.MEDIUM,
                "category": SecurityCategory.CRYPTOGRAPHY,
                "cwe": "CWE-327",
                "owasp": "A02:2021-Cryptographic Failures",
                "description": "Use of weak cryptographic algorithms",
                "recommendation": "Use strong algorithms: SHA-256+, AES, secure random generators"
            },
            
            "unsafe_deserialization": {
                "patterns": [
                    r"(?i)pickle\.loads?\s*\(",
                    r"(?i)yaml\.load\s*\([^)]*(?!Loader\s*=\s*yaml\.SafeLoader)",
                    r"(?i)ObjectInputStream\.readObject",
                    r"(?i)JsonConvert\.DeserializeObject.*<.*>",
                    r"(?i)unserialize\s*\("
                ],
                "severity": SecuritySeverity.HIGH,
                "category": SecurityCategory.INPUT_VALIDATION,
                "cwe": "CWE-502",
                "owasp": "A08:2021-Software and Data Integrity Failures",
                "description": "Unsafe deserialization vulnerability",
                "recommendation": "Use safe deserialization methods, validate input, use allowlists"
            },
            
            "path_traversal": {
                "patterns": [
                    r"(?i)(open|file|read).*\.\./",
                    r"(?i)File\s*\([^)]*\.\./",
                    r"(?i)Path\.join\s*\([^)]*\.\./",
                    r"(?i)include\s*\([^)]*\$_(GET|POST)",
                    r"(?i)require\s*\([^)]*\$_(GET|POST)"
                ],
                "severity": SecuritySeverity.HIGH,
                "category": SecurityCategory.INPUT_VALIDATION,
                "cwe": "CWE-22",
                "owasp": "A01:2021-Broken Access Control",
                "description": "Path traversal vulnerability",
                "recommendation": "Validate file paths, use allowlists, restrict file access"
            },
            
            "insecure_redirect": {
                "patterns": [
                    r"(?i)redirect\s*\([^)]*\$_(GET|POST)",
                    r"(?i)Response\.Redirect\s*\([^)]*Request\.",
                    r"(?i)sendRedirect\s*\([^)]*request\.getParameter",
                    r"(?i)window\.location\s*=.*\+",
                    r"(?i)header\s*\(\s*['\"]Location:"
                ],
                "severity": SecuritySeverity.MEDIUM,
                "category": SecurityCategory.AUTHENTICATION,
                "cwe": "CWE-601",
                "owasp": "A01:2021-Broken Access Control",
                "description": "Unvalidated redirect vulnerability",
                "recommendation": "Validate redirect URLs, use allowlists, avoid user-controlled redirects"
            },

            "missing_authorization": {
                "patterns": [
                    r"@app\.route.*methods.*POST(?!.*@.*auth)",
                    r"@app\.route.*methods.*DELETE(?!.*@.*auth)",
                    r"@app\.route.*methods.*PUT(?!.*@.*auth)",
                    r"(?i)def.*delete.*\((?!.*auth.*\))",
                    r"(?i)app\.(post|put|delete)\s*\([^)]*(?!.*auth)"
                ],
                "severity": SecuritySeverity.HIGH,
                "category": SecurityCategory.AUTHORIZATION,
                "cwe": "CWE-862",
                "owasp": "A01:2021-Broken Access Control",
                "description": "Missing authorization checks on sensitive endpoints",
                "recommendation": "Add authentication decorators, implement access controls"
            },

            "debug_code": {
                "patterns": [
                    r"(?i)print\s*\([^)]*password",
                    r"(?i)console\.log\s*\([^)]*token",
                    r"(?i)System\.out\.println\s*\([^)]*secret",
                    r"(?i)debug\s*=\s*True",
                    r"(?i)app\.config\[.*DEBUG.*\]\s*=\s*True"
                ],
                "severity": SecuritySeverity.MEDIUM,
                "category": SecurityCategory.ERROR_HANDLING,
                "cwe": "CWE-489",
                "owasp": "A09:2021-Security Logging and Monitoring Failures",
                "description": "Debug code exposing sensitive information",
                "recommendation": "Remove debug statements, disable debug mode in production"
            }
        }

    def _load_crypto_patterns(self) -> Dict[str, Dict]:
        """Load cryptographic vulnerability patterns"""
        return {
            "weak_ssl": {
                "patterns": [
                    r"(?i)SSLContext\.PROTOCOL_TLS",
                    r"(?i)ssl\.PROTOCOL_SSLv2",
                    r"(?i)ssl\.PROTOCOL_SSLv3",
                    r"(?i)verify_mode\s*=\s*ssl\.CERT_NONE",
                    r"(?i)check_hostname\s*=\s*False"
                ],
                "severity": SecuritySeverity.HIGH,
                "category": SecurityCategory.CRYPTOGRAPHY,
                "recommendation": "Use TLS 1.2+, enable certificate verification"
            },
            
            "weak_random": {
                "patterns": [
                    r"(?i)Math\.random\s*\(",
                    r"(?i)Random\(\)\.next",
                    r"(?i)rand\s*\(",
                    r"(?i)mt_rand\s*\("
                ],
                "severity": SecuritySeverity.MEDIUM,
                "category": SecurityCategory.CRYPTOGRAPHY,
                "recommendation": "Use cryptographically secure random generators"
            }
        }

    def _load_dependency_patterns(self) -> Dict[str, Dict]:
        """Load patterns for dependency vulnerability detection"""
        return {
            "vulnerable_packages": {
                # Common vulnerable package patterns
                "python": {
                    "pillow": {"versions": ["<8.3.2"], "cve": "CVE-2021-34552"},
                    "requests": {"versions": ["<2.25.1"], "cve": "CVE-2021-33503"},
                    "urllib3": {"versions": ["<1.26.5"], "cve": "CVE-2021-33503"}
                },
                "javascript": {
                    "lodash": {"versions": ["<4.17.21"], "cve": "CVE-2021-23337"},
                    "axios": {"versions": ["<0.21.1"], "cve": "CVE-2020-28168"},
                    "minimist": {"versions": ["<1.2.6"], "cve": "CVE-2021-44906"}
                }
            }
        }

    def analyze_code(self, code: str, file_path: str, language: str = None) -> List[SecurityVulnerability]:
        """
        Analyze code for security vulnerabilities
        
        Args:
            code: Source code to analyze
            file_path: Path to the file being analyzed
            language: Programming language (auto-detected if None)
            
        Returns:
            List of detected security vulnerabilities
        """
        if not language:
            language = self._detect_language(file_path)
            
        vulnerabilities = []
        lines = code.split('\n')
        
        # Analyze each pattern category
        for pattern_name, pattern_info in self.patterns.items():
            for pattern in pattern_info["patterns"]:
                vulnerabilities.extend(
                    self._find_pattern_matches(
                        pattern, pattern_name, pattern_info, 
                        code, lines, file_path, language
                    )
                )
        
        # Add crypto-specific analysis
        vulnerabilities.extend(self._analyze_crypto_usage(code, lines, file_path))
        
        # Add language-specific analysis
        if language.lower() in ['javascript', 'typescript']:
            vulnerabilities.extend(self._analyze_javascript_security(code, lines, file_path))
        elif language.lower() == 'python':
            vulnerabilities.extend(self._analyze_python_security(code, lines, file_path))
        elif language.lower() == 'java':
            vulnerabilities.extend(self._analyze_java_security(code, lines, file_path))
            
        return vulnerabilities

    def _find_pattern_matches(self, pattern: str, pattern_name: str, pattern_info: Dict,
                            code: str, lines: List[str], file_path: str, language: str) -> List[SecurityVulnerability]:
        """Find matches for a specific security pattern"""
        vulnerabilities = []
        
        for match in re.finditer(pattern, code, re.MULTILINE):
            # Find line number
            line_num = code[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
            
            # Calculate confidence based on context
            confidence = self._calculate_confidence(match, line_content, pattern_name, language)
            
            vuln_id = self._generate_vulnerability_id(pattern_name, file_path, line_num)
            
            vulnerability = SecurityVulnerability(
                id=vuln_id,
                name=pattern_name.replace('_', ' ').title(),
                description=pattern_info["description"],
                severity=pattern_info["severity"],
                category=pattern_info["category"],
                cwe_id=pattern_info.get("cwe"),
                owasp_category=pattern_info.get("owasp"),
                file_path=file_path,
                line_number=line_num,
                code_snippet=line_content.strip(),
                recommendation=pattern_info["recommendation"],
                confidence=confidence,
                auto_fixable=self._is_auto_fixable(pattern_name),
                fix_suggestion=self._get_fix_suggestion(pattern_name, match.group())
            )
            
            vulnerabilities.append(vulnerability)
            
        return vulnerabilities

    def _analyze_crypto_usage(self, code: str, lines: List[str], file_path: str) -> List[SecurityVulnerability]:
        """Analyze cryptographic implementations"""
        vulnerabilities = []
        
        for pattern_name, pattern_info in self.crypto_patterns.items():
            for pattern in pattern_info["patterns"]:
                for match in re.finditer(pattern, code, re.MULTILINE):
                    line_num = code[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    vuln_id = self._generate_vulnerability_id(pattern_name, file_path, line_num)
                    
                    vulnerability = SecurityVulnerability(
                        id=vuln_id,
                        name=pattern_name.replace('_', ' ').title(),
                        description=f"Cryptographic vulnerability: {pattern_name}",
                        severity=pattern_info["severity"],
                        category=pattern_info["category"],
                        cwe_id="CWE-327",
                        owasp_category="A02:2021-Cryptographic Failures",
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line_content.strip(),
                        recommendation=pattern_info["recommendation"],
                        confidence=0.8
                    )
                    
                    vulnerabilities.append(vulnerability)
                    
        return vulnerabilities

    def _analyze_javascript_security(self, code: str, lines: List[str], file_path: str) -> List[SecurityVulnerability]:
        """JavaScript-specific security analysis"""
        vulnerabilities = []
        
        # Check for prototype pollution
        prototype_pollution_patterns = [
            r"(?i)Object\.assign\s*\([^)]*\$",
            r"(?i)\[\s*key\s*\]\s*=.*\$",
            r"(?i)merge\s*\([^)]*req\."
        ]
        
        for pattern in prototype_pollution_patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                line_num = code[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                vuln_id = self._generate_vulnerability_id("prototype_pollution", file_path, line_num)
                
                vulnerability = SecurityVulnerability(
                    id=vuln_id,
                    name="Prototype Pollution",
                    description="Potential prototype pollution vulnerability",
                    severity=SecuritySeverity.HIGH,
                    category=SecurityCategory.INPUT_VALIDATION,
                    cwe_id="CWE-1321",
                    owasp_category="A08:2021-Software and Data Integrity Failures",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    recommendation="Validate object keys, use Object.create(null), freeze prototypes",
                    confidence=0.7
                )
                
                vulnerabilities.append(vulnerability)
                
        return vulnerabilities

    def _analyze_python_security(self, code: str, lines: List[str], file_path: str) -> List[SecurityVulnerability]:
        """Python-specific security analysis"""
        vulnerabilities = []
        
        # Check for dangerous eval usage
        dangerous_eval_patterns = [
            r"(?i)eval\s*\([^)]*input\s*\(",
            r"(?i)exec\s*\([^)]*input\s*\(",
            r"(?i)eval\s*\([^)]*request\."
        ]
        
        for pattern in dangerous_eval_patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                line_num = code[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                vuln_id = self._generate_vulnerability_id("dangerous_eval", file_path, line_num)
                
                vulnerability = SecurityVulnerability(
                    id=vuln_id,
                    name="Dangerous Eval Usage",
                    description="Use of eval() with user input",
                    severity=SecuritySeverity.CRITICAL,
                    category=SecurityCategory.INJECTION,
                    cwe_id="CWE-95",
                    owasp_category="A03:2021-Injection",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    recommendation="Never use eval() with user input, use ast.literal_eval() for safe evaluation",
                    confidence=0.9
                )
                
                vulnerabilities.append(vulnerability)
                
        return vulnerabilities

    def _analyze_java_security(self, code: str, lines: List[str], file_path: str) -> List[SecurityVulnerability]:
        """Java-specific security analysis"""
        vulnerabilities = []
        
        # Check for unsafe reflection
        unsafe_reflection_patterns = [
            r"(?i)Class\.forName\s*\([^)]*request\.",
            r"(?i)Method\.invoke\s*\([^)]*request\.",
            r"(?i)Constructor\.newInstance\s*\([^)]*request\."
        ]
        
        for pattern in unsafe_reflection_patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                line_num = code[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                vuln_id = self._generate_vulnerability_id("unsafe_reflection", file_path, line_num)
                
                vulnerability = SecurityVulnerability(
                    id=vuln_id,
                    name="Unsafe Reflection",
                    description="Unsafe use of reflection with user input",
                    severity=SecuritySeverity.HIGH,
                    category=SecurityCategory.INJECTION,
                    cwe_id="CWE-470",
                    owasp_category="A03:2021-Injection",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line_content.strip(),
                    recommendation="Validate class names, use allowlists, avoid reflection with user input",
                    confidence=0.8
                )
                
                vulnerabilities.append(vulnerability)
                
        return vulnerabilities

    def _calculate_confidence(self, match, line_content: str, pattern_name: str, language: str) -> float:
        """Calculate confidence score for a security finding"""
        base_confidence = 0.7
        
        # Increase confidence for specific contexts
        if "password" in line_content.lower() and "hardcoded" in pattern_name:
            base_confidence += 0.2
        if "admin" in line_content.lower() and "auth" in pattern_name:
            base_confidence += 0.2
        if any(word in line_content.lower() for word in ["secret", "key", "token"]):
            base_confidence += 0.1
            
        # Decrease confidence for comments or strings
        if line_content.strip().startswith(('#', '//', '/*', '*')):
            base_confidence -= 0.3
        if line_content.strip().startswith(('"""', "'''", '"', "'")):
            base_confidence -= 0.2
            
        return min(1.0, max(0.1, base_confidence))

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = file_path.split('.')[-1].lower()
        
        lang_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust',
            'cs': 'csharp',
            'cpp': 'cpp',
            'c': 'c'
        }
        
        return lang_map.get(ext, 'unknown')

    def _generate_vulnerability_id(self, pattern_name: str, file_path: str, line_num: int) -> str:
        """Generate unique vulnerability ID"""
        content = f"{pattern_name}:{file_path}:{line_num}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _is_auto_fixable(self, pattern_name: str) -> bool:
        """Determine if a vulnerability is automatically fixable"""
        auto_fixable_patterns = {
            "debug_code": True,
            "weak_crypto": True,
            "hardcoded_secrets": False,  # Requires manual review
            "sql_injection": False,     # Requires code restructuring
        }
        return auto_fixable_patterns.get(pattern_name, False)

    def _get_fix_suggestion(self, pattern_name: str, matched_code: str) -> Optional[str]:
        """Get automated fix suggestion for specific patterns"""
        fix_suggestions = {
            "debug_code": "Remove debug statement or wrap in conditional",
            "weak_crypto": "Replace with SHA-256 or stronger algorithm",
            "hardcoded_secrets": "Move to environment variables or secure storage",
        }
        return fix_suggestions.get(pattern_name)

    def generate_security_report(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, Any]:
        """Generate comprehensive security analysis report"""
        if not vulnerabilities:
            return {
                "overall_score": 100,
                "risk_level": "low",
                "total_vulnerabilities": 0,
                "summary": "No security vulnerabilities detected",
                "recommendations": ["Continue following secure coding practices"]
            }

        # Calculate security score
        severity_weights = {
            SecuritySeverity.CRITICAL: 25,
            SecuritySeverity.HIGH: 15,
            SecuritySeverity.MEDIUM: 8,
            SecuritySeverity.LOW: 3,
            SecuritySeverity.INFO: 1
        }
        
        total_penalty = sum(severity_weights[vuln.severity] for vuln in vulnerabilities)
        security_score = max(0, 100 - total_penalty)
        
        # Categorize by severity
        severity_counts = {}
        for severity in SecuritySeverity:
            severity_counts[severity.value] = len([v for v in vulnerabilities if v.severity == severity])
        
        # Categorize by type
        category_counts = {}
        for category in SecurityCategory:
            category_counts[category.value] = len([v for v in vulnerabilities if v.category == category])
        
        # Determine risk level
        if severity_counts.get("critical", 0) > 0:
            risk_level = "critical"
        elif severity_counts.get("high", 0) > 2:
            risk_level = "high"
        elif severity_counts.get("high", 0) > 0 or severity_counts.get("medium", 0) > 3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate top recommendations
        recommendations = self._generate_recommendations(vulnerabilities)
        
        return {
            "overall_score": security_score,
            "risk_level": risk_level,
            "total_vulnerabilities": len(vulnerabilities),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "vulnerabilities": [self._vulnerability_to_dict(v) for v in vulnerabilities],
            "recommendations": recommendations,
            "owasp_coverage": self._analyze_owasp_coverage(vulnerabilities),
            "auto_fixable_count": len([v for v in vulnerabilities if v.auto_fixable]),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _vulnerability_to_dict(self, vuln: SecurityVulnerability) -> Dict[str, Any]:
        """Convert vulnerability to dictionary format"""
        return {
            "id": vuln.id,
            "name": vuln.name,
            "description": vuln.description,
            "severity": vuln.severity.value,
            "category": vuln.category.value,
            "cwe_id": vuln.cwe_id,
            "owasp_category": vuln.owasp_category,
            "file_path": vuln.file_path,
            "line_number": vuln.line_number,
            "code_snippet": vuln.code_snippet,
            "recommendation": vuln.recommendation,
            "confidence": vuln.confidence,
            "auto_fixable": vuln.auto_fixable,
            "fix_suggestion": vuln.fix_suggestion
        }

    def _generate_recommendations(self, vulnerabilities: List[SecurityVulnerability]) -> List[str]:
        """Generate prioritized security recommendations"""
        recommendations = []
        
        # Critical issues first
        critical_vulns = [v for v in vulnerabilities if v.severity == SecuritySeverity.CRITICAL]
        if critical_vulns:
            recommendations.append(f"🚨 Address {len(critical_vulns)} critical vulnerabilities immediately")
        
        # Category-specific recommendations
        categories = set(v.category for v in vulnerabilities)
        
        if SecurityCategory.INJECTION in categories:
            recommendations.append("Implement input validation and parameterized queries")
        if SecurityCategory.CRYPTOGRAPHY in categories:
            recommendations.append("Upgrade cryptographic implementations to use strong algorithms")
        if SecurityCategory.AUTHENTICATION in categories:
            recommendations.append("Strengthen authentication and authorization mechanisms")
        if SecurityCategory.INPUT_VALIDATION in categories:
            recommendations.append("Implement comprehensive input validation and sanitization")
            
        # Auto-fixable recommendations
        auto_fixable = [v for v in vulnerabilities if v.auto_fixable]
        if auto_fixable:
            recommendations.append(f"Consider automated fixes for {len(auto_fixable)} low-risk issues")
            
        return recommendations[:5]  # Top 5 recommendations

    def _analyze_owasp_coverage(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, int]:
        """Analyze OWASP Top 10 coverage"""
        owasp_categories = {}
        for vuln in vulnerabilities:
            if vuln.owasp_category:
                owasp_categories[vuln.owasp_category] = owasp_categories.get(vuln.owasp_category, 0) + 1
        return owasp_categories


# Convenience function for service integration
def get_security_analyzer() -> SecurityAnalyzer:
    """Get SecurityAnalyzer instance"""
    return SecurityAnalyzer()