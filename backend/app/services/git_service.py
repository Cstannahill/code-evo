from git import Repo, GitCommandError
import tempfile
import os
import stat
import shutil
import re
import logging
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class GitService:
    """Enhanced Git service with robust URL handling, repository analysis, and cleanup"""

    def __init__(self):
        # Track temp directories for cleanup
        self.temp_dirs: List[str] = []
        # Language detection mapping (comprehensive)
        self.language_map: Dict[str, str] = {
            # JavaScript ecosystem
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".mjs": "JavaScript",
            ".cjs": "JavaScript",
            # Python
            ".py": "Python",
            ".pyw": "Python",
            ".pyx": "Python",
            # Java ecosystem
            ".java": "Java",
            ".kt": "Kotlin",
            ".scala": "Scala",
            # C family
            ".c": "C",
            ".cpp": "C++",
            ".cc": "C++",
            ".cxx": "C++",
            ".cs": "C#",
            ".h": "C/C++",
            ".hpp": "C++",
            # Web
            ".html": "HTML",
            ".htm": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sass": "Sass",
            ".less": "Less",
            # Data & Config
            ".json": "JSON",
            ".xml": "XML",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".toml": "TOML",
            # Other languages
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".r": "R",
            ".sql": "SQL",
            ".sh": "Shell",
            ".bash": "Bash",
            ".zsh": "Zsh",
            ".fish": "Fish",
            # Modern languages
            ".dart": "Dart",
            ".elm": "Elm",
            ".ex": "Elixir",
            ".exs": "Elixir",
            ".erl": "Erlang",
            ".f90": "Fortran",
            ".f95": "Fortran",
            ".jl": "Julia",
            ".nim": "Nim",
            ".cr": "Crystal",
            ".zig": "Zig",
            ".v": "V",
            ".sol": "Solidity",
            ".move": "Move",
            ".clj": "Clojure",
            ".cljs": "ClojureScript",
            ".hs": "Haskell",
            ".ml": "OCaml",
            ".fs": "F#",
            ".lua": "Lua",
            ".pl": "Perl",
            ".m": "Objective-C",
            ".mm": "Objective-C++",
            # Assembly and low-level
            ".asm": "Assembly",
            ".s": "Assembly",
            # Functional languages
            ".purs": "PureScript",
            ".reason": "Reason",
            ".re": "Reason",
            # Documentation
            ".md": "Markdown",
            ".rst": "reStructuredText",
            ".tex": "LaTeX",
        }
        logger.info("Git service initialized")

    def _normalize_git_url(self, url: str) -> str:
        """
        Handle various Git URL formats (SSH, git://, HTTPS) and normalize to HTTPS .git
        """
        url = url.strip()
        # SSH style: git@host:user/repo.git
        ssh_pattern = r"^git@([^:]+):(.+?)(\.git)?$"
        match = re.match(ssh_pattern, url)
        if match:
            host, path = match.group(1), match.group(2)
            normalized = f"https://{host}/{path}"
            if not normalized.endswith(".git"):
                normalized += ".git"
            logger.info(f"Converted SSH URL to HTTPS: {normalized}")
            return normalized
        # git:// -> https://
        if url.startswith("git://"):
            url = url.replace("git://", "https://", 1)
            logger.info(f"Converted git:// URL to HTTPS: {url}")
        # Parse and ensure valid
        parsed = urlparse(url if "://" in url else f"https://{url}")
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            raise ValueError(f"Unsupported Git URL scheme: {scheme}")
        netloc = parsed.netloc
        path = parsed.path
        # Ensure .git extension
        if any(
            host in netloc for host in ("github.com", "gitlab.com", "bitbucket.org")
        ) and not path.endswith(".git"):
            path += ".git"
        normalized = urlunparse(parsed._replace(path=path))
        logger.info(f"Normalized Git URL: {normalized}")
        return normalized

    def clone_repository(self, repo_url: str, branch: str = "main") -> Repo:
        """Clone a repository (shallow) with fallback on default branch"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        try:
            url = self._normalize_git_url(repo_url)
            repo_name = Path(urlparse(url).path).stem
            logger.info(f"Cloning {url} into {temp_dir}")
            try:
                repo = Repo.clone_from(url, temp_dir, branch=branch, depth=1)
                logger.info(f"✅ Cloned {repo_name}@{branch}")
            except Exception:
                logger.warning(f"Branch '{branch}' not found, cloning default branch")
                repo = Repo.clone_from(url, temp_dir, depth=1)
            # Fetch more history for analysis
            repo.remotes.origin.fetch(depth=200)
            return repo
        except ValueError as ve:
            logger.error(str(ve))
            raise
        except GitCommandError as ge:
            msg = str(ge)
            if "not found" in msg.lower():
                raise ValueError(f"Repository not found: {repo_url}")
            raise ValueError(f"Git clone error: {msg}")

    def get_repository_info(self, repo: Repo) -> Dict:
        """Basic repo info: commit count, dates, authors, branches"""
        try:
            all_commits = list(repo.iter_commits())
            authors = {
                c.author.email for c in all_commits if c.author and c.author.email
            }
            return {
                "total_commits": len(all_commits),
                "first_commit_date": (
                    all_commits[-1].committed_datetime if all_commits else None
                ),
                "last_commit_date": (
                    all_commits[0].committed_datetime if all_commits else None
                ),
                "authors": list(authors),
                "branches": [b.name for b in repo.branches],
            }
        except Exception as e:
            logger.error(f"Error getting repository info: {e}")
            return {
                "total_commits": 0,
                "first_commit_date": None,
                "last_commit_date": None,
                "authors": [],
                "branches": [],
            }

    def get_commit_history(self, repo: Repo, limit: int = 100) -> List[Dict]:
        """Detailed commit history with diffs up to limit"""
        commits: List[Dict] = []
        try:
            commit_list = list(repo.iter_commits(max_count=limit))
            for idx, commit in enumerate(commit_list):
                data = {
                    "hash": commit.hexsha,
                    "author": str(commit.author),
                    "author_email": getattr(commit.author, "email", ""),
                    "date": commit.committed_datetime,
                    "message": commit.message.strip(),
                    "files_changed": [],
                    "stats": {"additions": 0, "deletions": 0, "files": 0},
                }
                parent = commit.parents[0] if commit.parents else None
                diffs = commit.diff(parent)
                for diff in diffs:
                    info = self._analyze_file_change(diff)
                    if info:
                        data["files_changed"].append(info)
                        data["stats"]["additions"] += info.get("additions", 0)
                        data["stats"]["deletions"] += info.get("deletions", 0)
                data["stats"]["files"] = len(data["files_changed"])
                commits.append(data)
            return commits
        except Exception as e:
            logger.error(f"Error processing commit history: {e}")
            raise

    def _analyze_file_change(self, diff) -> Optional[Dict]:
        """Analyze a single file diff for metadata and snippet"""
        try:
            path = diff.b_path or diff.a_path
            if not path or self._should_skip_file(path):
                return None
            ext = Path(path).suffix.lower()
            language = self.language_map.get(ext, "Other")
            info = {
                "file_path": path,
                "change_type": self._get_change_type(diff),
                "language": language,
                "additions": 0,
                "deletions": 0,
                "content": None,
            }
            if diff.b_blob:
                try:
                    raw = diff.b_blob.data_stream.read().decode(
                        "utf-8", errors="ignore"
                    )
                    info["content"] = raw[:5000]
                except:
                    pass
            try:
                text = diff.diff.decode("utf-8", errors="ignore")
                info["additions"] = text.count("\n+")
                info["deletions"] = text.count("\n-")
            except:
                pass
            return info
        except Exception as e:
            logger.warning(f"Error analyzing diff: {e}")
            return None

    def _get_change_type(self, diff) -> str:
        if diff.new_file:
            return "added"
        if diff.deleted_file:
            return "deleted"
        if diff.renamed_file:
            return "renamed"
        return "modified"

    def _should_skip_file(self, path: str) -> bool:
        patterns = [
            r"\.git/",
            r"node_modules/",
            r"__pycache__/",
            r"\.(jpg|jpeg|png|gif|pdf|docx?)$",
            r"\.(pyc|lock)$",
            r"\.env",
        ]
        return any(re.search(p, path, re.IGNORECASE) for p in patterns)

    def extract_technologies(self, repo: Repo) -> Dict:
        """Scan latest commit tree for languages, frameworks, tools"""
        tech: Dict = {
            "languages": {},
            "frameworks": set(),
            "libraries": set(),
            "tools": set(),
        }
        try:
            latest = next(repo.iter_commits())
            for item in latest.tree.traverse():
                if item.type != "blob":
                    continue
                ext = Path(item.path).suffix.lower()
                lang = self.language_map.get(ext, "Other")
                if lang != "Other":
                    tech["languages"][lang] = tech["languages"].get(lang, 0) + 1
                name = Path(item.path).name.lower()
                # parse known package files
                if name == "package.json":
                    self._parse_package_json(item.data_stream.read().decode(), tech)
                elif name == "requirements.txt":
                    self._parse_requirements_txt(item.data_stream.read().decode(), tech)
                elif name == "cargo.toml":
                    self._parse_cargo_toml(item.data_stream.read().decode(), tech)
                elif name == "go.mod":
                    self._parse_go_mod(item.data_stream.read().decode(), tech)
                elif name == "gemfile":
                    self._parse_gemfile(item.data_stream.read().decode(), tech)
                elif name == "composer.json":
                    self._parse_composer_json(item.data_stream.read().decode(), tech)
                elif name == "pom.xml":
                    self._parse_pom_xml(item.data_stream.read().decode(), tech)
                elif name in ("build.gradle", "build.gradle.kts"):
                    self._parse_gradle(item.data_stream.read().decode(), tech)
                elif name == "pubspec.yaml":
                    self._parse_pubspec_yaml(item.data_stream.read().decode(), tech)
                elif name == "project.clj":
                    self._parse_project_clj(item.data_stream.read().decode(), tech)
                elif name == "mix.exs":
                    self._parse_mix_exs(item.data_stream.read().decode(), tech)
                elif name == "deno.json" or name == "deno.jsonc":
                    self._parse_deno_json(item.data_stream.read().decode(), tech)
                elif name == "pyproject.toml":
                    self._parse_pyproject_toml(item.data_stream.read().decode(), tech)
                # Docker detection
                elif name in ("dockerfile", "dockerfile.dev", "dockerfile.prod", "dockerfile.test"):
                    tech["tools"].add("Docker")
                    self._parse_dockerfile(item.data_stream.read().decode(), tech)
                elif name in ("docker-compose.yml", "docker-compose.yaml", "docker-compose.dev.yml", "docker-compose.prod.yml"):
                    tech["tools"].add("Docker Compose")
                    self._parse_docker_compose(item.data_stream.read().decode(), tech)
                elif name == ".dockerignore":
                    tech["tools"].add("Docker")
        except Exception as e:
            logger.error(f"Error extracting technologies: {e}")
        tech["frameworks"] = list(tech["frameworks"])
        tech["libraries"] = list(tech["libraries"])
        tech["tools"] = list(tech["tools"])
        return tech

    def _parse_package_json(self, content: str, tech: Dict) -> None:
        import json

        try:
            data = json.loads(content)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            
            # Frameworks
            framework_map = {
                "react": "React",
                "vue": "Vue.js",
                "angular": "Angular",
                "@angular/core": "Angular",
                "express": "Express.js",
                "koa": "Koa",
                "fastify": "Fastify",
                "next": "Next.js",
                "nuxt": "Nuxt.js",
                "gatsby": "Gatsby",
                "svelte": "Svelte",
                "solid-js": "SolidJS",
                "qwik": "Qwik",
                "remix": "Remix",
                "nestjs": "NestJS",
                "@nestjs/core": "NestJS",
                "@tauri-apps/api": "Tauri",
                "@tauri-apps/cli": "Tauri"
            }
            
            # Libraries
            library_map = {
                "lodash": "Lodash",
                "axios": "Axios",
                "moment": "Moment.js",
                "dayjs": "Day.js",
                "rxjs": "RxJS",
                "redux": "Redux",
                "mobx": "MobX",
                "zustand": "Zustand",
                "d3": "D3.js",
                "three": "Three.js",
                "socket.io": "Socket.IO"
            }
            
            # Tools
            tool_map = {
                "webpack": "Webpack",
                "vite": "Vite",
                "rollup": "Rollup",
                "parcel": "Parcel",
                "eslint": "ESLint",
                "prettier": "Prettier",
                "typescript": "TypeScript",
                "babel": "Babel",
                "@babel/core": "Babel",
                "jest": "Jest",
                "vitest": "Vitest",
                "cypress": "Cypress",
                "playwright": "Playwright",
                "storybook": "Storybook"
            }
            
            # Parse dependencies
            for dep in deps:
                if dep in framework_map:
                    tech["frameworks"].add(framework_map[dep])
                elif dep in library_map:
                    tech["libraries"].add(library_map[dep])
                elif dep in tool_map:
                    tech["tools"].add(tool_map[dep])
                    
        except Exception as e:
            logger.warning(f"Error parsing package.json: {e}")

    def _parse_requirements_txt(self, content: str, tech: Dict) -> None:
        framework_map = {
            "django": "Django",
            "flask": "Flask", 
            "fastapi": "FastAPI",
            "tornado": "Tornado",
            "pyramid": "Pyramid",
            "bottle": "Bottle",
            "aiohttp": "aiohttp",
            "starlette": "Starlette",
            "sanic": "Sanic"
        }
        
        library_map = {
            "numpy": "NumPy",
            "pandas": "Pandas", 
            "scipy": "SciPy",
            "matplotlib": "Matplotlib",
            "seaborn": "Seaborn",
            "plotly": "Plotly",
            "scikit-learn": "scikit-learn",
            "tensorflow": "TensorFlow",
            "torch": "PyTorch",
            "keras": "Keras",
            "opencv-python": "OpenCV",
            "pillow": "Pillow",
            "requests": "Requests",
            "beautifulsoup4": "BeautifulSoup",
            "scrapy": "Scrapy",
            "sqlalchemy": "SQLAlchemy",
            "psycopg2": "psycopg2",
            "pymongo": "PyMongo",
            "redis": "Redis-py",
            "celery": "Celery"
        }
        
        tool_map = {
            "pytest": "pytest",
            "black": "Black",
            "flake8": "flake8",
            "mypy": "mypy",
            "pylint": "Pylint",
            "jupyterlab": "JupyterLab",
            "notebook": "Jupyter Notebook"
        }
        
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = line.split("==")[0].split(">=")[0].split("~=")[0].strip().lower()
            
            if pkg in framework_map:
                tech["frameworks"].add(framework_map[pkg])
            elif pkg in library_map:
                tech["libraries"].add(library_map[pkg])
            elif pkg in tool_map:
                tech["tools"].add(tool_map[pkg])

    def _parse_cargo_toml(self, content: str, tech: Dict) -> None:
        """Parse Rust Cargo.toml for dependencies"""
        try:
            import toml
            data = toml.loads(content)
            deps = data.get("dependencies", {})
            
            framework_map = {
                # Web frameworks
                "actix-web": "Actix Web",
                "warp": "Warp",
                "rocket": "Rocket",
                "axum": "Axum",
                "tide": "Tide",
                "tokio": "Tokio",
                "async-std": "async-std",
                "hyper": "Hyper",
                # Desktop/GUI frameworks
                "tauri": "Tauri",
                "egui": "egui",
                "iced": "Iced",
                "druid": "Druid",
                "slint": "Slint",
                "gtk4": "GTK4",
                "fltk": "FLTK",
                # Game engines
                "bevy": "Bevy",
                "amethyst": "Amethyst",
                "ggez": "ggez",
                # Other frameworks
                "yew": "Yew",
                "leptos": "Leptos",
                "dioxus": "Dioxus"
            }
            
            library_map = {
                # Serialization
                "serde": "Serde",
                "serde_json": "Serde JSON",
                "toml": "TOML",
                # HTTP/Networking
                "reqwest": "Reqwest",
                "hyper": "Hyper",
                "surf": "Surf",
                # CLI
                "clap": "Clap",
                "structopt": "StructOpt",
                # Database
                "diesel": "Diesel",
                "sqlx": "SQLx",
                "rusqlite": "rusqlite",
                "mongodb": "MongoDB",
                # Date/Time
                "chrono": "Chrono",
                "time": "Time",
                # Utils
                "uuid": "UUID",
                "regex": "Regex",
                "thiserror": "thiserror",
                "anyhow": "anyhow",
                # Logging
                "log": "log",
                "env_logger": "env_logger",
                "tracing": "Tracing",
                # Crypto
                "ring": "Ring",
                "rustls": "rustls",
                # Testing
                "proptest": "proptest",
                "quickcheck": "quickcheck"
            }
            
            for dep in deps:
                if dep in framework_map:
                    tech["frameworks"].add(framework_map[dep])
                elif dep in library_map:
                    tech["libraries"].add(library_map[dep])
                    
        except Exception as e:
            logger.warning(f"Error parsing Cargo.toml: {e}")

    def _parse_go_mod(self, content: str, tech: Dict) -> None:
        """Parse Go go.mod for modules"""
        try:
            framework_map = {
                # Web frameworks
                "github.com/gin-gonic/gin": "Gin",
                "github.com/gorilla/mux": "Gorilla Mux", 
                "github.com/labstack/echo": "Echo",
                "github.com/gofiber/fiber": "Fiber",
                "github.com/beego/beego": "Beego",
                "github.com/go-chi/chi": "Chi",
                "github.com/valyala/fasthttp": "FastHTTP",
                "github.com/iris-contrib/middleware": "Iris",
                "github.com/kataras/iris": "Iris",
                "github.com/go-martini/martini": "Martini",
                "github.com/revel/revel": "Revel",
                "github.com/astaxie/beego": "Beego",
                # Microservices frameworks  
                "github.com/grpc/grpc-go": "gRPC",
                "go.micro.dev/v4": "Go Micro",
                "github.com/go-kit/kit": "Go Kit",
                # GraphQL
                "github.com/99designs/gqlgen": "gqlgen",
                "github.com/graphql-go/graphql": "GraphQL Go",
                # CLI frameworks
                "github.com/spf13/cobra": "Cobra",
                "github.com/urfave/cli": "CLI"
            }
            
            library_map = {
                # Database
                "gorm.io/gorm": "GORM",
                "github.com/jmoiron/sqlx": "SQLx",
                "go.mongodb.org/mongo-driver": "MongoDB Driver",
                "github.com/go-redis/redis": "Redis Client",
                "github.com/go-sql-driver/mysql": "MySQL Driver",
                "github.com/lib/pq": "PostgreSQL Driver",
                "github.com/mattn/go-sqlite3": "SQLite Driver",
                # Serialization
                "github.com/golang/protobuf": "Protocol Buffers",
                "google.golang.org/protobuf": "Protocol Buffers",
                "github.com/json-iterator/go": "JSON Iterator",
                "gopkg.in/yaml.v3": "YAML",
                "github.com/BurntSushi/toml": "TOML",
                # HTTP/Networking
                "github.com/gorilla/websocket": "Gorilla WebSocket",
                "github.com/valyala/fasthttp": "FastHTTP",
                "golang.org/x/net": "Go Net",
                # Logging
                "github.com/sirupsen/logrus": "Logrus",
                "go.uber.org/zap": "Zap",
                "github.com/rs/zerolog": "Zerolog",
                # Configuration
                "github.com/spf13/viper": "Viper",
                "github.com/kelseyhightower/envconfig": "Envconfig",
                # Testing
                "github.com/stretchr/testify": "Testify",
                "github.com/golang/mock": "GoMock",
                "github.com/onsi/ginkgo": "Ginkgo",
                "github.com/onsi/gomega": "Gomega",
                # Crypto
                "golang.org/x/crypto": "Go Crypto",
                # Time
                "github.com/jinzhu/now": "Now",
                # Validation
                "github.com/go-playground/validator": "Validator",
                # Utils
                "github.com/google/uuid": "UUID",
                "github.com/pkg/errors": "Errors"
            }
            
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("require"):
                    continue
                if "//" in line:
                    line = line.split("//")[0].strip()
                
                for mod in framework_map:
                    if mod in line:
                        tech["frameworks"].add(framework_map[mod])
                for mod in library_map:
                    if mod in line:
                        tech["libraries"].add(library_map[mod])
                        
        except Exception as e:
            logger.warning(f"Error parsing go.mod: {e}")

    def _parse_gemfile(self, content: str, tech: Dict) -> None:
        """Parse Ruby Gemfile for gems"""
        try:
            framework_map = {
                "rails": "Ruby on Rails",
                "sinatra": "Sinatra",
                "hanami": "Hanami",
                "roda": "Roda",
                "grape": "Grape"
            }
            
            library_map = {
                "devise": "Devise",
                "rspec": "RSpec",
                "factory_bot": "Factory Bot",
                "sidekiq": "Sidekiq",
                "redis": "Redis",
                "pg": "PostgreSQL"
            }
            
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("gem"):
                    gem_name = line.split("'")[1] if "'" in line else line.split('"')[1]
                    if gem_name in framework_map:
                        tech["frameworks"].add(framework_map[gem_name])
                    elif gem_name in library_map:
                        tech["libraries"].add(library_map[gem_name])
                        
        except Exception as e:
            logger.warning(f"Error parsing Gemfile: {e}")

    def _parse_composer_json(self, content: str, tech: Dict) -> None:
        """Parse PHP composer.json for packages"""
        try:
            import json
            data = json.loads(content)
            deps = {**data.get("require", {}), **data.get("require-dev", {})}
            
            framework_map = {
                "laravel/framework": "Laravel",
                "symfony/symfony": "Symfony",
                "cakephp/cakephp": "CakePHP",
                "codeigniter4/framework": "CodeIgniter",
                "slim/slim": "Slim"
            }
            
            library_map = {
                "doctrine/orm": "Doctrine ORM",
                "monolog/monolog": "Monolog",
                "guzzlehttp/guzzle": "Guzzle",
                "phpunit/phpunit": "PHPUnit",
                "predis/predis": "Predis"
            }
            
            for dep in deps:
                if dep in framework_map:
                    tech["frameworks"].add(framework_map[dep])
                elif dep in library_map:
                    tech["libraries"].add(library_map[dep])
                    
        except Exception as e:
            logger.warning(f"Error parsing composer.json: {e}")

    def _parse_pom_xml(self, content: str, tech: Dict) -> None:
        """Parse Java pom.xml for dependencies"""
        try:
            framework_map = {
                "spring-boot": "Spring Boot",
                "spring-framework": "Spring Framework", 
                "quarkus": "Quarkus",
                "micronaut": "Micronaut",
                "dropwizard": "Dropwizard"
            }
            
            library_map = {
                "junit": "JUnit",
                "mockito": "Mockito",
                "jackson": "Jackson",
                "gson": "Gson",
                "hibernate": "Hibernate"
            }
            
            for framework in framework_map:
                if framework in content.lower():
                    tech["frameworks"].add(framework_map[framework])
            for library in library_map:
                if library in content.lower():
                    tech["libraries"].add(library_map[library])
                    
        except Exception as e:
            logger.warning(f"Error parsing pom.xml: {e}")

    def _parse_gradle(self, content: str, tech: Dict) -> None:
        """Parse Gradle build files for dependencies"""
        try:
            framework_map = {
                "spring-boot": "Spring Boot",
                "ktor": "Ktor",
                "android": "Android"
            }
            
            for framework in framework_map:
                if framework in content.lower():
                    tech["frameworks"].add(framework_map[framework])
                    
        except Exception as e:
            logger.warning(f"Error parsing Gradle file: {e}")

    def _parse_pubspec_yaml(self, content: str, tech: Dict) -> None:
        """Parse Dart pubspec.yaml for packages"""
        try:
            import yaml
            data = yaml.safe_load(content)
            deps = {**data.get("dependencies", {}), **data.get("dev_dependencies", {})}
            
            framework_map = {
                "flutter": "Flutter",
                "angular": "AngularDart",
                "shelf": "Shelf"
            }
            
            library_map = {
                "http": "HTTP",
                "dio": "Dio",
                "provider": "Provider",
                "bloc": "BLoC",
                "riverpod": "Riverpod"
            }
            
            for dep in deps:
                if dep in framework_map:
                    tech["frameworks"].add(framework_map[dep])
                elif dep in library_map:
                    tech["libraries"].add(library_map[dep])
                    
        except Exception as e:
            logger.warning(f"Error parsing pubspec.yaml: {e}")

    def _parse_project_clj(self, content: str, tech: Dict) -> None:
        """Parse Clojure project.clj for dependencies"""
        try:
            framework_map = {
                "ring": "Ring",
                "compojure": "Compojure",
                "luminus": "Luminus"
            }
            
            for framework in framework_map:
                if framework in content:
                    tech["frameworks"].add(framework_map[framework])
                    
        except Exception as e:
            logger.warning(f"Error parsing project.clj: {e}")

    def _parse_mix_exs(self, content: str, tech: Dict) -> None:
        """Parse Elixir mix.exs for dependencies"""
        try:
            framework_map = {
                "phoenix": "Phoenix",
                "plug": "Plug",
                "absinthe": "Absinthe"
            }
            
            library_map = {
                "ecto": "Ecto",
                "genserver": "GenServer",
                "httpoison": "HTTPoison"
            }
            
            for framework in framework_map:
                if framework in content:
                    tech["frameworks"].add(framework_map[framework])
            for library in library_map:
                if library in content:
                    tech["libraries"].add(library_map[library])
                    
        except Exception as e:
            logger.warning(f"Error parsing mix.exs: {e}")

    def _parse_deno_json(self, content: str, tech: Dict) -> None:
        """Parse Deno configuration for imports"""
        try:
            import json
            data = json.loads(content)
            
            tech["tools"].add("Deno")
            
            imports = data.get("imports", {})
            for imp in imports:
                if "oak" in imp:
                    tech["frameworks"].add("Oak")
                elif "fresh" in imp:
                    tech["frameworks"].add("Fresh")
                    
        except Exception as e:
            logger.warning(f"Error parsing deno.json: {e}")

    def _parse_pyproject_toml(self, content: str, tech: Dict) -> None:
        """Parse Python pyproject.toml for modern Python projects"""
        try:
            import toml
            data = toml.loads(content)
            
            # Check build system
            build_system = data.get("build-system", {})
            if "poetry" in build_system.get("build-backend", ""):
                tech["tools"].add("Poetry")
            elif "setuptools" in build_system.get("build-backend", ""):
                tech["tools"].add("Setuptools")
            elif "flit" in build_system.get("build-backend", ""):
                tech["tools"].add("Flit")
            elif "hatch" in build_system.get("build-backend", ""):
                tech["tools"].add("Hatch")
                
            # Check dependencies in poetry format
            poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            for dep in poetry_deps:
                if dep == "django":
                    tech["frameworks"].add("Django")
                elif dep == "fastapi":
                    tech["frameworks"].add("FastAPI")
                    
        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {e}")

    def get_pattern_candidates(self, commits: List[Dict]) -> List[Dict]:
        """Extract code snippets for pattern analysis"""
        candidates = []
        for c in commits:
            for f in c["files_changed"]:
                if f.get("content") and f["language"] != "Other":
                    snips = self._extract_code_snippets(f["content"], f["language"])
                    for s in snips:
                        candidates.append(
                            {
                                "code": s,
                                "language": f["language"],
                                "file_path": f["file_path"],
                                "commit_hash": c["hash"],
                                "commit_date": c["date"],
                                "author": c["author_email"],
                            }
                        )

        # Sort by quality and return the best candidates
        candidates.sort(key=lambda x: len(x["code"]), reverse=True)
        return candidates[:50]  # Return top 50 candidates

    def _extract_code_snippets(self, content: str, language: str) -> List[str]:
        lines = content.split("\n")
        out = []
        if language in ("JavaScript", "TypeScript"):
            out.extend(self._extract_js_snippets(lines))
        if language == "Python":
            out.extend(self._extract_python_snippets(lines))
        return [s for s in out if len(s) > 20]

    def _extract_js_snippets(self, lines: List[str]) -> List[str]:
        snippets = []
        curr = []
        in_fn = False
        braces = 0
        for line in lines:
            s = line.strip()
            if not s or s.startswith("//"):
                continue
            if any(tok in s for tok in ("function ", "const ", "useState", "class ")):
                if in_fn and len("\n".join(curr)) > 50:
                    snippets.append("\n".join(curr))
                curr = [line]
                in_fn = True
                braces = s.count("{") - s.count("}")
            elif in_fn:
                curr.append(line)
                braces += s.count("{") - s.count("}")
                if braces <= 0:
                    in_fn = False
                    if len("\n".join(curr)) > 50:
                        snippets.append("\n".join(curr))
                    curr = []
        return snippets

    def _extract_python_snippets(self, lines: List[str]) -> List[str]:
        snippets = []
        curr = []
        in_fn = False
        indent = 0
        for line in lines:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            lvl = len(line) - len(line.lstrip())
            if s.startswith(("def ", "class ")):
                if in_fn and len("\n".join(curr)) > 50:
                    snippets.append("\n".join(curr))
                curr = [line]
                in_fn = True
                indent = lvl
            elif in_fn:
                if lvl > indent:
                    curr.append(line)
                else:
                    in_fn = False
                    if len("\n".join(curr)) > 50:
                        snippets.append("\n".join(curr))
                    curr = []
                    if s.startswith(("def ", "class ")):
                        curr = [line]
                        in_fn = True
                        indent = lvl
        return snippets

    def _parse_dockerfile(self, content: str, tech: Dict) -> None:
        """Parse Dockerfile for base images and tools"""
        try:
            lines = content.split('\n')
            for line in lines:
                line = line.strip().upper()
                if line.startswith('FROM '):
                    base_image = line.split('FROM ')[1].split(':')[0].split(' ')[0]
                    
                    # Detect base technologies from Docker images
                    base_image_lower = base_image.lower()
                    if 'node' in base_image_lower:
                        tech["tools"].add("Node.js")
                    elif 'python' in base_image_lower:
                        tech["tools"].add("Python")
                    elif 'nginx' in base_image_lower:
                        tech["tools"].add("Nginx")
                    elif 'apache' in base_image_lower:
                        tech["tools"].add("Apache")
                    elif 'postgres' in base_image_lower:
                        tech["tools"].add("PostgreSQL")
                    elif 'mysql' in base_image_lower:
                        tech["tools"].add("MySQL")
                    elif 'redis' in base_image_lower:
                        tech["tools"].add("Redis")
                    elif 'mongo' in base_image_lower:
                        tech["tools"].add("MongoDB")
                    elif 'golang' in base_image_lower or 'go:' in base_image_lower:
                        tech["tools"].add("Go")
                    elif 'rust' in base_image_lower:
                        tech["tools"].add("Rust")
                    elif 'openjdk' in base_image_lower or 'java' in base_image_lower:
                        tech["tools"].add("Java")
                    elif 'alpine' in base_image_lower:
                        tech["tools"].add("Alpine Linux")
                    elif 'ubuntu' in base_image_lower:
                        tech["tools"].add("Ubuntu")
                        
        except Exception as e:
            logger.warning(f"Error parsing Dockerfile: {e}")

    def _parse_docker_compose(self, content: str, tech: Dict) -> None:
        """Parse docker-compose.yml for services and technologies"""
        try:
            import yaml
            data = yaml.safe_load(content)
            
            services = data.get('services', {})
            for service_name, service_config in services.items():
                image = service_config.get('image', '')
                if image:
                    image_lower = image.lower()
                    if 'postgres' in image_lower:
                        tech["tools"].add("PostgreSQL")
                    elif 'mysql' in image_lower:
                        tech["tools"].add("MySQL")
                    elif 'redis' in image_lower:
                        tech["tools"].add("Redis")
                    elif 'mongo' in image_lower:
                        tech["tools"].add("MongoDB")
                    elif 'nginx' in image_lower:
                        tech["tools"].add("Nginx")
                    elif 'apache' in image_lower:
                        tech["tools"].add("Apache")
                    elif 'elasticsearch' in image_lower:
                        tech["tools"].add("Elasticsearch")
                    elif 'rabbitmq' in image_lower:
                        tech["tools"].add("RabbitMQ")
                    elif 'kafka' in image_lower:
                        tech["tools"].add("Apache Kafka")
                        
                # Check for environment variables that indicate technologies
                environment = service_config.get('environment', {})
                if isinstance(environment, list):
                    env_vars = ' '.join(environment).lower()
                elif isinstance(environment, dict):
                    env_vars = ' '.join(environment.keys()).lower()
                else:
                    env_vars = ''
                    
                if 'database_url' in env_vars or 'db_' in env_vars:
                    tech["tools"].add("Database")
                if 'redis_url' in env_vars:
                    tech["tools"].add("Redis")
                    
        except Exception as e:
            logger.warning(f"Error parsing docker-compose: {e}")

    def cleanup(self) -> None:
        """Remove all temp dirs with better Windows compatibility"""
        for d in self.temp_dirs:
            try:
                import stat

                # Set write permissions on Windows before deletion
                if os.name == "nt":  # Windows
                    for root, dirs, files in os.walk(d):
                        for dir in dirs:
                            os.chmod(os.path.join(root, dir), stat.S_IWRITE)
                        for file in files:
                            os.chmod(os.path.join(root, file), stat.S_IWRITE)

                shutil.rmtree(d)
                logger.info(f"Cleaned {d}")
            except Exception as e:
                logger.warning(f"Cleanup warning for {d}: {e}")
                # Try alternative cleanup on Windows
                if os.name == "nt":
                    try:
                        import subprocess

                        subprocess.run(
                            ["rmdir", "/s", "/q", d], shell=True, check=False
                        )
                        logger.info(f"Force cleaned {d}")
                    except Exception as e2:
                        logger.error(f"Force cleanup failed {d}: {e2}")
        self.temp_dirs = []

    def __del__(self):
        self.cleanup()
