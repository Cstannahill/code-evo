# Enhanced Technology Detection Service
"""
Comprehensive technology detection service that identifies:
- Programming languages and frameworks
- Build tools and package managers
- Testing frameworks
- Deployment and infrastructure tools
- Development tools and linters
- Cloud services and APIs
- Database technologies
- Monitoring and observability tools
"""

import json
import re
import logging
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TechnologyInfo:
    """Information about a detected technology"""
    name: str
    category: str
    confidence: float
    version: Optional[str] = None
    evidence: List[str] = None
    description: Optional[str] = None
    maturity: Optional[str] = None  # stable, beta, experimental


class EnhancedTechnologyDetector:
    """
    Enhanced technology detection with comprehensive pattern matching,
    semantic analysis, and confidence scoring.
    """

    def __init__(self):
        """Initialize with comprehensive technology databases"""
        self.tech_patterns = self._load_technology_patterns()
        self.framework_indicators = self._load_framework_indicators()
        self.tool_indicators = self._load_tool_indicators()
        self.cloud_indicators = self._load_cloud_indicators()
        self.database_indicators = self._load_database_indicators()
        
        logger.info("EnhancedTechnologyDetector initialized with comprehensive databases")

    def _load_technology_patterns(self) -> Dict[str, Dict]:
        """Load comprehensive technology detection patterns"""
        return {
            "frontend_frameworks": {
                "react": {
                    "patterns": [
                        r"import\s+React\s+from\s+['\"]react['\"]",
                        r"from\s+['\"]react['\"]",
                        r"React\.(Component|useState|useEffect)",
                        r"\.jsx?$",
                        r"\.tsx?$"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["react", "@types/react"],
                    "config_files": ["next.config.js", "craco.config.js"],
                    "description": "React - A JavaScript library for building user interfaces",
                    "maturity": "stable"
                },
                "vue": {
                    "patterns": [
                        r"import\s+.*\s+from\s+['\"]vue['\"]",
                        r"Vue\.(component|directive|mixin)",
                        r"\.vue$",
                        r"<template>",
                        r"vue-cli|@vue/cli"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["vue", "@vue/cli-service"],
                    "config_files": ["vue.config.js", "vite.config.js"],
                    "description": "Vue.js - Progressive JavaScript framework",
                    "maturity": "stable"
                },
                "angular": {
                    "patterns": [
                        r"import\s+.*\s+from\s+['\"]@angular/",
                        r"@Component\s*\(",
                        r"@Injectable\s*\(",
                        r"@NgModule\s*\(",
                        r"\.module\.ts$"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["@angular/core", "@angular/cli"],
                    "config_files": ["angular.json", "ng-package.json"],
                    "description": "Angular - Platform for building mobile and desktop web applications",
                    "maturity": "stable"
                },
                "svelte": {
                    "patterns": [
                        r"<script\s+context=['\"]module['\"]>",
                        r"svelte:",
                        r"\.svelte$",
                        r"import.*from\s+['\"]svelte['\"]"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["svelte", "svelte-preprocess"],
                    "config_files": ["svelte.config.js", "rollup.config.js"],
                    "description": "Svelte - Cybernetically enhanced web apps",
                    "maturity": "stable"
                }
            },
            
            "backend_frameworks": {
                "express": {
                    "patterns": [
                        r"const\s+express\s*=\s*require\s*\(\s*['\"]express['\"]\s*\)",
                        r"import\s+express\s+from\s+['\"]express['\"]",
                        r"app\.(get|post|put|delete)\s*\(",
                        r"express\.Router\s*\("
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["express"],
                    "description": "Express.js - Fast, unopinionated web framework",
                    "maturity": "stable"
                },
                "fastapi": {
                    "patterns": [
                        r"from\s+fastapi\s+import",
                        r"@app\.(get|post|put|delete)\s*\(",
                        r"FastAPI\s*\(",
                        r"from\s+pydantic\s+import"
                    ],
                    "package_files": ["requirements.txt", "pyproject.toml"],
                    "dependencies": ["fastapi", "uvicorn"],
                    "description": "FastAPI - Modern, fast web framework for building APIs",
                    "maturity": "stable"
                },
                "django": {
                    "patterns": [
                        r"from\s+django\s+import",
                        r"Django\s+version",
                        r"INSTALLED_APPS\s*=",
                        r"urlpatterns\s*="
                    ],
                    "package_files": ["requirements.txt"],
                    "dependencies": ["django"],
                    "config_files": ["settings.py", "manage.py"],
                    "description": "Django - High-level Python web framework",
                    "maturity": "stable"
                },
                "spring_boot": {
                    "patterns": [
                        r"@SpringBootApplication",
                        r"@RestController",
                        r"@Service",
                        r"@Repository",
                        r"org\.springframework"
                    ],
                    "package_files": ["pom.xml", "build.gradle"],
                    "dependencies": ["spring-boot-starter"],
                    "description": "Spring Boot - Java-based framework for microservices",
                    "maturity": "stable"
                }
            },
            
            "mobile_frameworks": {
                "react_native": {
                    "patterns": [
                        r"import\s+.*\s+from\s+['\"]react-native['\"]",
                        r"View|Text|Image.*from\s+['\"]react-native['\"]",
                        r"\.android\.js$",
                        r"\.ios\.js$"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["react-native"],
                    "config_files": ["metro.config.js"],
                    "description": "React Native - Cross-platform mobile development",
                    "maturity": "stable"
                },
                "flutter": {
                    "patterns": [
                        r"import\s+'package:flutter/",
                        r"Widget\s+",
                        r"StatelessWidget|StatefulWidget",
                        r"\.dart$"
                    ],
                    "package_files": ["pubspec.yaml"],
                    "dependencies": ["flutter"],
                    "description": "Flutter - UI toolkit for building natively compiled applications",
                    "maturity": "stable"
                },
                "ionic": {
                    "patterns": [
                        r"@ionic/",
                        r"ion-",
                        r"ionic-angular",
                        r"@ionic/react"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["@ionic/core", "@ionic/react"],
                    "description": "Ionic - Cross-platform mobile app development",
                    "maturity": "stable"
                }
            },
            
            "build_tools": {
                "webpack": {
                    "patterns": [
                        r"webpack\.config\.",
                        r"require\s*\(\s*['\"]webpack['\"]\s*\)",
                        r"module\.exports\s*=\s*{",
                        r"entry:\s*"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["webpack"],
                    "config_files": ["webpack.config.js"],
                    "description": "Webpack - Module bundler for JavaScript",
                    "maturity": "stable"
                },
                "vite": {
                    "patterns": [
                        r"vite\.config\.",
                        r"import\s+.*\s+from\s+['\"]vite['\"]",
                        r"defineConfig\s*\("
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["vite"],
                    "config_files": ["vite.config.js", "vite.config.ts"],
                    "description": "Vite - Next generation frontend tooling",
                    "maturity": "stable"
                },
                "rollup": {
                    "patterns": [
                        r"rollup\.config\.",
                        r"import\s+.*\s+from\s+['\"]rollup['\"]"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["rollup"],
                    "config_files": ["rollup.config.js"],
                    "description": "Rollup - JavaScript module bundler",
                    "maturity": "stable"
                }
            },
            
            "testing_frameworks": {
                "jest": {
                    "patterns": [
                        r"describe\s*\(",
                        r"it\s*\(",
                        r"test\s*\(",
                        r"expect\s*\(",
                        r"\.test\.js$",
                        r"\.spec\.js$"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["jest"],
                    "config_files": ["jest.config.js"],
                    "description": "Jest - JavaScript testing framework",
                    "maturity": "stable"
                },
                "cypress": {
                    "patterns": [
                        r"cy\.(get|visit|click)",
                        r"describe\s*\(",
                        r"it\s*\(",
                        r"cypress\.json"
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["cypress"],
                    "config_files": ["cypress.json"],
                    "description": "Cypress - End-to-end testing framework",
                    "maturity": "stable"
                },
                "playwright": {
                    "patterns": [
                        r"from\s+playwright\s+import",
                        r"page\.(click|fill|get)",
                        r"test\s*\(",
                        r"playwright\.config\."
                    ],
                    "package_files": ["package.json"],
                    "dependencies": ["playwright", "@playwright/test"],
                    "config_files": ["playwright.config.js"],
                    "description": "Playwright - End-to-end testing framework",
                    "maturity": "stable"
                }
            }
        }

    def _load_framework_indicators(self) -> Dict[str, List[str]]:
        """Load framework-specific indicators"""
        return {
            "react": ["jsx", "tsx", "component", "hooks", "props"],
            "vue": ["template", "script", "style", "computed", "watch"],
            "angular": ["component", "service", "module", "directive", "pipe"],
            "svelte": ["script", "style", "reactive", "store"],
            "express": ["middleware", "router", "app.get", "app.post"],
            "django": ["model", "view", "template", "url", "form"],
            "fastapi": ["router", "dependency", "response", "request"],
            "spring": ["controller", "service", "repository", "entity"]
        }

    def _load_tool_indicators(self) -> Dict[str, List[str]]:
        """Load development tool indicators"""
        return {
            "eslint": ["eslint", ".eslintrc", "eslint-config"],
            "prettier": ["prettier", ".prettierrc", "prettier-config"],
            "typescript": ["typescript", "tsconfig", "@types/"],
            "babel": ["babel", "@babel/", "babel.config"],
            "postcss": ["postcss", "postcss.config", "autoprefixer"],
            "tailwind": ["tailwind", "tailwindcss", "@tailwind/"],
            "sass": ["sass", "scss", "node-sass"],
            "less": ["less", "less-loader"]
        }

    def _load_cloud_indicators(self) -> Dict[str, List[str]]:
        """Load cloud service indicators"""
        return {
            "aws": ["aws-sdk", "amazon-web-services", "lambda", "s3", "ec2"],
            "azure": ["azure", "@azure/", "microsoft-azure"],
            "gcp": ["google-cloud", "@google-cloud/", "firebase"],
            "vercel": ["vercel", "vercel.json", "@vercel/"],
            "netlify": ["netlify", "netlify.toml", "@netlify/"],
            "heroku": ["heroku", "Procfile", "heroku-buildpack"],
            "railway": ["railway", "railway.json", "@railway/"]
        }

    def _load_database_indicators(self) -> Dict[str, List[str]]:
        """Load database technology indicators"""
        return {
            "mongodb": ["mongodb", "mongoose", "@mongodb/", "mongo"],
            "postgresql": ["postgres", "pg", "postgresql", "prisma"],
            "mysql": ["mysql", "mysql2", "sequelize"],
            "redis": ["redis", "ioredis", "@redis/"],
            "sqlite": ["sqlite", "sqlite3", "better-sqlite3"],
            "dynamodb": ["dynamodb", "aws-sdk"],
            "firestore": ["firestore", "@google-cloud/firestore"]
        }

    def detect_technologies(self, repo_path: str, file_list: List[str]) -> Dict[str, List[TechnologyInfo]]:
        """
        Comprehensive technology detection for a repository
        
        Args:
            repo_path: Path to the repository
            file_list: List of file paths in the repository
            
        Returns:
            Dictionary of detected technologies by category
        """
        detected_tech = defaultdict(list)
        
        try:
            # Analyze package files
            package_tech = self._analyze_package_files(repo_path, file_list)
            for category, tech_list in package_tech.items():
                detected_tech[category].extend(tech_list)
            
            # Analyze source code patterns
            source_tech = self._analyze_source_patterns(repo_path, file_list)
            for category, tech_list in source_tech.items():
                detected_tech[category].extend(tech_list)
            
            # Analyze configuration files
            config_tech = self._analyze_config_files(repo_path, file_list)
            for category, tech_list in config_tech.items():
                detected_tech[category].extend(tech_list)
            
            # Analyze deployment files
            deploy_tech = self._analyze_deployment_files(repo_path, file_list)
            for category, tech_list in deploy_tech.items():
                detected_tech[category].extend(tech_list)
            
            # Remove duplicates and sort by confidence
            for category in detected_tech:
                detected_tech[category] = self._deduplicate_and_rank(detected_tech[category])
            
            logger.info(f"Detected {sum(len(tech_list) for tech_list in detected_tech.values())} technologies")
            return dict(detected_tech)
            
        except Exception as e:
            logger.error(f"Error detecting technologies: {e}")
            return {}

    def _analyze_package_files(self, repo_path: str, file_list: List[str]) -> Dict[str, List[TechnologyInfo]]:
        """Analyze package management files"""
        detected = defaultdict(list)
        
        for file_path in file_list:
            full_path = Path(repo_path) / file_path
            
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                file_name = Path(file_path).name.lower()
                
                # JavaScript/TypeScript ecosystem
                if file_name == "package.json":
                    detected.update(self._parse_package_json(content, file_path))
                elif file_name in ["yarn.lock", "package-lock.json", "pnpm-lock.yaml"]:
                    detected["package_managers"].append(TechnologyInfo(
                        name=file_name.split('.')[0].title(),
                        category="package_managers",
                        confidence=1.0,
                        evidence=[file_path],
                        description=f"{file_name.split('.')[0].title()} package manager lock file"
                    ))
                
                # Python ecosystem
                elif file_name == "requirements.txt":
                    detected.update(self._parse_requirements_txt(content, file_path))
                elif file_name == "pyproject.toml":
                    detected.update(self._parse_pyproject_toml(content, file_path))
                
                # Java ecosystem
                elif file_name == "pom.xml":
                    detected.update(self._parse_pom_xml(content, file_path))
                elif file_name in ["build.gradle", "build.gradle.kts"]:
                    detected.update(self._parse_gradle(content, file_path))
                
                # Rust ecosystem
                elif file_name == "cargo.toml":
                    detected.update(self._parse_cargo_toml(content, file_path))
                
                # Go ecosystem
                elif file_name == "go.mod":
                    detected.update(self._parse_go_mod(content, file_path))
                
                # Ruby ecosystem
                elif file_name == "gemfile":
                    detected.update(self._parse_gemfile(content, file_path))
                
                # PHP ecosystem
                elif file_name == "composer.json":
                    detected.update(self._parse_composer_json(content, file_path))
                
                # Dart/Flutter ecosystem
                elif file_name == "pubspec.yaml":
                    detected.update(self._parse_pubspec_yaml(content, file_path))
                
                # Clojure ecosystem
                elif file_name == "project.clj":
                    detected.update(self._parse_project_clj(content, file_path))
                
                # Elixir ecosystem
                elif file_name == "mix.exs":
                    detected.update(self._parse_mix_exs(content, file_path))
                
                # Deno ecosystem
                elif file_name in ["deno.json", "deno.jsonc"]:
                    detected.update(self._parse_deno_json(content, file_path))
                
            except Exception as e:
                logger.debug(f"Error analyzing package file {file_path}: {e}")
        
        return dict(detected)

    def _parse_package_json(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse package.json for comprehensive technology detection"""
        detected = defaultdict(list)
        
        try:
            data = json.loads(content)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            scripts = data.get("scripts", {})
            
            # Detect frameworks and libraries
            for dep_name, version in deps.items():
                tech_info = self._identify_npm_package(dep_name, version, file_path)
                if tech_info:
                    detected[tech_info.category].append(tech_info)
            
            # Detect build tools from scripts
            for script_name, script_content in scripts.items():
                build_tool = self._detect_build_tool_from_script(script_content)
                if build_tool:
                    detected["build_tools"].append(TechnologyInfo(
                        name=build_tool,
                        category="build_tools",
                        confidence=0.8,
                        evidence=[f"script: {script_name} in {file_path}"],
                        description=f"Build tool detected from script: {script_name}"
                    ))
            
            # Detect Node.js version requirements
            engines = data.get("engines", {})
            if "node" in engines:
                detected["runtimes"].append(TechnologyInfo(
                    name=f"Node.js {engines['node']}",
                    category="runtimes",
                    confidence=1.0,
                    evidence=[file_path],
                    description=f"Node.js version requirement: {engines['node']}"
                ))
            
        except Exception as e:
            logger.debug(f"Error parsing package.json: {e}")
        
        return dict(detected)

    def _identify_npm_package(self, package_name: str, version: str, file_path: str) -> Optional[TechnologyInfo]:
        """Identify technology category for npm package"""
        
        # Frontend frameworks
        if package_name in ["react", "@types/react"]:
            return TechnologyInfo(
                name="React",
                category="frontend_frameworks",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description="React - JavaScript library for building user interfaces",
                maturity="stable"
            )
        elif package_name in ["vue", "@vue/cli-service"]:
            return TechnologyInfo(
                name="Vue.js",
                category="frontend_frameworks",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description="Vue.js - Progressive JavaScript framework",
                maturity="stable"
            )
        elif package_name.startswith("@angular/"):
            return TechnologyInfo(
                name="Angular",
                category="frontend_frameworks",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description="Angular - Platform for building mobile and desktop web applications",
                maturity="stable"
            )
        
        # Backend frameworks
        elif package_name == "express":
            return TechnologyInfo(
                name="Express.js",
                category="backend_frameworks",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description="Express.js - Fast, unopinionated web framework",
                maturity="stable"
            )
        elif package_name in ["next", "nuxt", "gatsby"]:
            return TechnologyInfo(
                name=package_name.title(),
                category="frontend_frameworks",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description=f"{package_name.title()} - Full-stack React/Vue framework",
                maturity="stable"
            )
        
        # Testing frameworks
        elif package_name in ["jest", "vitest", "mocha", "jasmine"]:
            return TechnologyInfo(
                name=package_name.title(),
                category="testing_frameworks",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description=f"{package_name.title()} - JavaScript testing framework",
                maturity="stable"
            )
        elif package_name in ["cypress", "playwright", "@playwright/test"]:
            return TechnologyInfo(
                name=package_name.replace("@", "").title(),
                category="testing_frameworks",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description=f"{package_name.replace('@', '').title()} - End-to-end testing framework",
                maturity="stable"
            )
        
        # Build tools
        elif package_name in ["webpack", "vite", "rollup", "parcel"]:
            return TechnologyInfo(
                name=package_name.title(),
                category="build_tools",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description=f"{package_name.title()} - JavaScript module bundler",
                maturity="stable"
            )
        
        # Development tools
        elif package_name in ["eslint", "prettier", "typescript"]:
            return TechnologyInfo(
                name=package_name.title(),
                category="development_tools",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description=f"{package_name.title()} - Development tool",
                maturity="stable"
            )
        
        # Database libraries
        elif package_name in ["mongoose", "sequelize", "prisma", "@prisma/client"]:
            db_name = "MongoDB" if package_name == "mongoose" else "Prisma" if "prisma" in package_name else "Sequelize"
            return TechnologyInfo(
                name=db_name,
                category="databases",
                confidence=0.9,
                version=version,
                evidence=[file_path],
                description=f"{db_name} - Database library/ORM",
                maturity="stable"
            )
        
        # Cloud services
        elif package_name.startswith("aws-") or package_name == "aws-sdk":
            return TechnologyInfo(
                name="AWS SDK",
                category="cloud_services",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description="AWS SDK - Amazon Web Services integration",
                maturity="stable"
            )
        elif package_name.startswith("@azure/"):
            return TechnologyInfo(
                name="Azure SDK",
                category="cloud_services",
                confidence=1.0,
                version=version,
                evidence=[file_path],
                description="Azure SDK - Microsoft Azure integration",
                maturity="stable"
            )
        
        return None

    def _detect_build_tool_from_script(self, script_content: str) -> Optional[str]:
        """Detect build tool from npm script content"""
        script_lower = script_content.lower()
        
        if "webpack" in script_lower:
            return "Webpack"
        elif "vite" in script_lower:
            return "Vite"
        elif "rollup" in script_lower:
            return "Rollup"
        elif "parcel" in script_lower:
            return "Parcel"
        elif "next" in script_lower:
            return "Next.js"
        elif "nuxt" in script_lower:
            return "Nuxt.js"
        elif "gatsby" in script_lower:
            return "Gatsby"
        
        return None

    def _analyze_source_patterns(self, repo_path: str, file_list: List[str]) -> Dict[str, List[TechnologyInfo]]:
        """Analyze source code for technology patterns"""
        detected = defaultdict(list)
        
        # Focus on key source files
        source_files = [f for f in file_list if self._is_source_file(f)]
        
        for file_path in source_files[:50]:  # Limit to avoid performance issues
            full_path = Path(repo_path) / file_path
            
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Detect patterns in each technology category
                for category, technologies in self.tech_patterns.items():
                    for tech_name, tech_info in technologies.items():
                        patterns = tech_info.get("patterns", [])
                        confidence = 0.0
                        matches = []
                        
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                                confidence += 0.3
                                matches.append(pattern)
                        
                        if confidence > 0.0:
                            detected[category].append(TechnologyInfo(
                                name=tech_name.replace("_", " ").title(),
                                category=category,
                                confidence=min(confidence, 1.0),
                                evidence=[f"{file_path}: {', '.join(matches[:3])}"],
                                description=tech_info.get("description", ""),
                                maturity=tech_info.get("maturity", "stable")
                            ))
                
            except Exception as e:
                logger.debug(f"Error analyzing source file {file_path}: {e}")
        
        return dict(detected)

    def _analyze_config_files(self, repo_path: str, file_list: List[str]) -> Dict[str, List[TechnologyInfo]]:
        """Analyze configuration files for technology detection"""
        detected = defaultdict(list)
        
        config_patterns = {
            "webpack.config.js": ("Webpack", "build_tools"),
            "vite.config.js": ("Vite", "build_tools"),
            "rollup.config.js": ("Rollup", "build_tools"),
            "next.config.js": ("Next.js", "frontend_frameworks"),
            "nuxt.config.js": ("Nuxt.js", "frontend_frameworks"),
            "gatsby-config.js": ("Gatsby", "frontend_frameworks"),
            "tailwind.config.js": ("Tailwind CSS", "css_frameworks"),
            "postcss.config.js": ("PostCSS", "css_tools"),
            "eslint.config.js": ("ESLint", "development_tools"),
            "prettier.config.js": ("Prettier", "development_tools"),
            "jest.config.js": ("Jest", "testing_frameworks"),
            "cypress.json": ("Cypress", "testing_frameworks"),
            "playwright.config.js": ("Playwright", "testing_frameworks"),
            "tsconfig.json": ("TypeScript", "development_tools"),
            "babel.config.js": ("Babel", "development_tools")
        }
        
        for file_path in file_list:
            file_name = Path(file_path).name.lower()
            
            if file_name in config_patterns:
                tech_name, category = config_patterns[file_name]
                detected[category].append(TechnologyInfo(
                    name=tech_name,
                    category=category,
                    confidence=1.0,
                    evidence=[file_path],
                    description=f"{tech_name} configuration detected"
                ))
        
        return dict(detected)

    def _analyze_deployment_files(self, repo_path: str, file_list: List[str]) -> Dict[str, List[TechnologyInfo]]:
        """Analyze deployment and infrastructure files"""
        detected = defaultdict(list)
        
        deployment_patterns = {
            "dockerfile": ("Docker", "containerization"),
            "docker-compose.yml": ("Docker Compose", "containerization"),
            "docker-compose.yaml": ("Docker Compose", "containerization"),
            "vercel.json": ("Vercel", "cloud_platforms"),
            "netlify.toml": ("Netlify", "cloud_platforms"),
            "railway.json": ("Railway", "cloud_platforms"),
            "heroku.yml": ("Heroku", "cloud_platforms"),
            "procfile": ("Heroku", "cloud_platforms"),
            "k8s.yml": ("Kubernetes", "container_orchestration"),
            "kubernetes.yml": ("Kubernetes", "container_orchestration"),
            ".github/workflows/": ("GitHub Actions", "ci_cd"),
            ".gitlab-ci.yml": ("GitLab CI", "ci_cd"),
            "jenkinsfile": ("Jenkins", "ci_cd"),
            "travis.yml": ("Travis CI", "ci_cd"),
            "circle.yml": ("CircleCI", "ci_cd")
        }
        
        for file_path in file_list:
            file_name = Path(file_path).name.lower()
            
            # Check for exact matches
            if file_name in deployment_patterns:
                tech_name, category = deployment_patterns[file_name]
                detected[category].append(TechnologyInfo(
                    name=tech_name,
                    category=category,
                    confidence=1.0,
                    evidence=[file_path],
                    description=f"{tech_name} deployment configuration"
                ))
            
            # Check for path-based matches
            elif "/" in file_path:
                for pattern, (tech_name, category) in deployment_patterns.items():
                    if pattern in file_path.lower():
                        detected[category].append(TechnologyInfo(
                            name=tech_name,
                            category=category,
                            confidence=1.0,
                            evidence=[file_path],
                            description=f"{tech_name} configuration in {file_path}"
                        ))
        
        return dict(detected)

    def _is_source_file(self, file_path: str) -> bool:
        """Check if file is a source code file"""
        source_extensions = {
            '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.cs',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.clj',
            '.hs', '.ml', '.fs', '.dart', '.vue', '.svelte'
        }
        
        return Path(file_path).suffix.lower() in source_extensions

    def _deduplicate_and_rank(self, tech_list: List[TechnologyInfo]) -> List[TechnologyInfo]:
        """Remove duplicates and rank by confidence"""
        seen = set()
        unique_tech = []
        
        for tech in tech_list:
            key = (tech.name, tech.category)
            if key not in seen:
                seen.add(key)
                unique_tech.append(tech)
        
        # Sort by confidence (descending)
        return sorted(unique_tech, key=lambda x: x.confidence, reverse=True)

    # Placeholder methods for parsing different package files
    def _parse_requirements_txt(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Python requirements.txt"""
        detected = defaultdict(list)
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                package_name = line.split('==')[0].split('>=')[0].split('<=')[0]
                
                if package_name == "fastapi":
                    detected["backend_frameworks"].append(TechnologyInfo(
                        name="FastAPI",
                        category="backend_frameworks",
                        confidence=1.0,
                        evidence=[file_path],
                        description="FastAPI - Modern Python web framework"
                    ))
                elif package_name == "django":
                    detected["backend_frameworks"].append(TechnologyInfo(
                        name="Django",
                        category="backend_frameworks",
                        confidence=1.0,
                        evidence=[file_path],
                        description="Django - High-level Python web framework"
                    ))
                elif package_name == "flask":
                    detected["backend_frameworks"].append(TechnologyInfo(
                        name="Flask",
                        category="backend_frameworks",
                        confidence=1.0,
                        evidence=[file_path],
                        description="Flask - Lightweight Python web framework"
                    ))
        
        return dict(detected)

    def _parse_pyproject_toml(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse pyproject.toml"""
        # Implementation for pyproject.toml parsing
        return {}

    def _parse_pom_xml(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Maven pom.xml"""
        # Implementation for Maven parsing
        return {}

    def _parse_gradle(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Gradle build files"""
        # Implementation for Gradle parsing
        return {}

    def _parse_cargo_toml(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Rust Cargo.toml"""
        # Implementation for Cargo parsing
        return {}

    def _parse_go_mod(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Go go.mod"""
        # Implementation for Go module parsing
        return {}

    def _parse_gemfile(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Ruby Gemfile"""
        # Implementation for Gemfile parsing
        return {}

    def _parse_composer_json(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse PHP composer.json"""
        # Implementation for Composer parsing
        return {}

    def _parse_pubspec_yaml(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Dart pubspec.yaml"""
        # Implementation for pubspec parsing
        return {}

    def _parse_project_clj(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Clojure project.clj"""
        # Implementation for Leiningen parsing
        return {}

    def _parse_mix_exs(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Elixir mix.exs"""
        # Implementation for Mix parsing
        return {}

    def _parse_deno_json(self, content: str, file_path: str) -> Dict[str, List[TechnologyInfo]]:
        """Parse Deno deno.json"""
        # Implementation for Deno parsing
        return {}
