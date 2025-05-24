# app/services/git_service.py
from git import Repo, GitCommandError
import tempfile
import os
import shutil
from typing import List, Dict, Optional, Generator
from datetime import datetime
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class GitService:
    """Service for Git repository operations and analysis"""

    def __init__(self):
        self.temp_dirs = []  # Track temp directories for cleanup

        # Language detection mapping
        self.language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "React",
            ".ts": "TypeScript",
            ".tsx": "React TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".c": "C",
            ".cpp": "C++",
            ".cs": "C#",
            ".php": "PHP",
            ".rb": "Ruby",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".sql": "SQL",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".vue": "Vue",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".md": "Markdown",
            ".dockerfile": "Docker",
        }

    def clone_repository(self, repo_url: str, branch: str = "main") -> Repo:
        """Clone a repository to temporary directory"""
        try:
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)

            logger.info(f"Cloning {repo_url} to {temp_dir}")

            # Handle authentication if needed
            if "github.com" in repo_url and not repo_url.startswith("https://"):
                repo_url = f"https://github.com/{repo_url}"

            repo = Repo.clone_from(
                repo_url, temp_dir, branch=branch, depth=1000
            )  # Limit depth for performance
            return repo

        except GitCommandError as e:
            logger.error(f"Failed to clone repository {repo_url}: {e}")
            raise ValueError(f"Failed to clone repository: {e}")

    def get_repository_info(self, repo: Repo) -> Dict:
        """Get basic repository information"""
        try:
            commits = list(repo.iter_commits(max_count=1))
            if not commits:
                return {
                    "total_commits": 0,
                    "first_commit_date": None,
                    "last_commit_date": None,
                    "authors": [],
                    "branches": [],
                }

            # Get all commits for stats
            all_commits = list(repo.iter_commits())

            authors = set()
            for commit in all_commits:
                authors.add(commit.author.email)

            return {
                "total_commits": len(all_commits),
                "first_commit_date": (
                    all_commits[-1].committed_datetime if all_commits else None
                ),
                "last_commit_date": (
                    all_commits[0].committed_datetime if all_commits else None
                ),
                "authors": list(authors),
                "branches": [branch.name for branch in repo.branches],
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

    def get_commit_history(self, repo: Repo, limit: int = 1000) -> List[Dict]:
        """Extract detailed commit history"""
        commits = []

        try:
            for commit in repo.iter_commits(max_count=limit):
                commit_data = {
                    "hash": commit.hexsha,
                    "author_name": commit.author.name,
                    "author_email": commit.author.email,
                    "committed_date": commit.committed_datetime,
                    "message": commit.message.strip(),
                    "files_changed": [],
                    "stats": {
                        "total_files": commit.stats.total["files"],
                        "total_insertions": commit.stats.total["insertions"],
                        "total_deletions": commit.stats.total["deletions"],
                    },
                }

                # Get file changes
                try:
                    parent = commit.parents[0] if commit.parents else None
                    for diff in commit.diff(parent):
                        file_change = self._analyze_file_change(diff)
                        if file_change:
                            commit_data["files_changed"].append(file_change)
                except Exception as e:
                    logger.warning(
                        f"Error analyzing diff for commit {commit.hexsha}: {e}"
                    )

                commits.append(commit_data)

        except Exception as e:
            logger.error(f"Error getting commit history: {e}")

        return commits

    def _analyze_file_change(self, diff) -> Optional[Dict]:
        """Analyze a single file change"""
        try:
            file_path = diff.a_path or diff.b_path
            if not file_path:
                return None

            # Get file extension and language
            extension = Path(file_path).suffix.lower()
            language = self.language_map.get(extension, "Other")

            # Skip binary files and common non-code files
            if self._should_skip_file(file_path):
                return None

            change_data = {
                "file_path": file_path,
                "old_path": diff.a_path,
                "change_type": self._get_change_type(diff),
                "language": language,
                "extension": extension,
                "additions": 0,
                "deletions": 0,
                "content": None,
            }

            # Get content and diff stats
            if diff.b_blob:  # File exists in new version
                try:
                    content = diff.b_blob.data_stream.read().decode(
                        "utf-8", errors="ignore"
                    )
                    change_data["content"] = content[:5000]  # Limit content size
                except Exception as e:
                    logger.warning(f"Could not read content for {file_path}: {e}")

            # Calculate line changes
            try:
                diff_text = diff.diff.decode("utf-8", errors="ignore")
                change_data["additions"] = diff_text.count("\n+")
                change_data["deletions"] = diff_text.count("\n-")
            except:
                pass

            return change_data

        except Exception as e:
            logger.warning(f"Error analyzing file change: {e}")
            return None

    def _get_change_type(self, diff) -> str:
        """Determine the type of change"""
        if diff.new_file:
            return "added"
        elif diff.deleted_file:
            return "deleted"
        elif diff.renamed_file:
            return "renamed"
        else:
            return "modified"

    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped in analysis"""
        skip_patterns = [
            r"\.git/",
            r"node_modules/",
            r"__pycache__/",
            r"\.pyc$",
            r"\.jpg$",
            r"\.jpeg$",
            r"\.png$",
            r"\.gif$",
            r"\.pdf$",
            r"\.doc$",
            r"\.docx$",
            r"\.zip$",
            r"\.tar$",
            r"\.gz$",
            r"package-lock\.json$",
            r"yarn\.lock$",
            r"\.DS_Store$",
            r"\.env$",
            r"\.env\..*$",
        ]

        for pattern in skip_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True

        return False

    def extract_technologies(self, repo: Repo) -> Dict:
        """Extract technologies used in the repository"""
        technologies = {
            "languages": {},
            "frameworks": set(),
            "libraries": set(),
            "tools": set(),
        }

        try:
            # Get latest commit
            latest_commit = next(repo.iter_commits())

            # Analyze files in the latest commit
            for item in latest_commit.tree.traverse():
                if item.type == "blob":  # It's a file
                    file_path = item.path
                    extension = Path(file_path).suffix.lower()

                    # Count languages
                    language = self.language_map.get(extension, "Other")
                    if language != "Other":
                        technologies["languages"][language] = (
                            technologies["languages"].get(language, 0) + 1
                        )

                    # Analyze specific files for technologies
                    self._analyze_tech_file(file_path, item, technologies)

        except Exception as e:
            logger.error(f"Error extracting technologies: {e}")

        # Convert sets to lists for JSON serialization
        technologies["frameworks"] = list(technologies["frameworks"])
        technologies["libraries"] = list(technologies["libraries"])
        technologies["tools"] = list(technologies["tools"])

        return technologies

    def _analyze_tech_file(self, file_path: str, blob, technologies: Dict):
        """Analyze specific files for technology indicators"""
        filename = Path(file_path).name.lower()

        try:
            # Package files
            if filename == "package.json":
                content = blob.data_stream.read().decode("utf-8", errors="ignore")
                self._parse_package_json(content, technologies)
            elif filename == "requirements.txt":
                content = blob.data_stream.read().decode("utf-8", errors="ignore")
                self._parse_requirements_txt(content, technologies)
            elif filename == "gemfile":
                technologies["languages"]["Ruby"] = (
                    technologies["languages"].get("Ruby", 0) + 1
                )
                technologies["tools"].add("Bundler")
            elif filename == "pom.xml":
                technologies["languages"]["Java"] = (
                    technologies["languages"].get("Java", 0) + 1
                )
                technologies["tools"].add("Maven")
            elif filename == "build.gradle":
                technologies["languages"]["Java"] = (
                    technologies["languages"].get("Java", 0) + 1
                )
                technologies["tools"].add("Gradle")
            elif filename == "dockerfile":
                technologies["tools"].add("Docker")
            elif filename in [".travis.yml", ".github/workflows/ci.yml"]:
                technologies["tools"].add("CI/CD")

        except Exception as e:
            logger.warning(f"Error analyzing tech file {file_path}: {e}")

    def _parse_package_json(self, content: str, technologies: Dict):
        """Parse package.json for JavaScript technologies"""
        import json

        try:
            data = json.loads(content)

            # Dependencies
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            # Framework detection
            if "react" in deps:
                technologies["frameworks"].add("React")
            if "vue" in deps:
                technologies["frameworks"].add("Vue.js")
            if "@angular/core" in deps:
                technologies["frameworks"].add("Angular")
            if "express" in deps:
                technologies["frameworks"].add("Express.js")
            if "next" in deps:
                technologies["frameworks"].add("Next.js")

            # Tools
            if "webpack" in deps:
                technologies["tools"].add("Webpack")
            if "typescript" in deps:
                technologies["languages"]["TypeScript"] = (
                    technologies["languages"].get("TypeScript", 0) + 1
                )
            if "jest" in deps:
                technologies["tools"].add("Jest")

        except Exception as e:
            logger.warning(f"Error parsing package.json: {e}")

    def _parse_requirements_txt(self, content: str, technologies: Dict):
        """Parse requirements.txt for Python technologies"""
        lines = content.split("\n")

        for line in lines:
            line = line.strip().lower()
            if not line or line.startswith("#"):
                continue

            # Extract package name
            package = line.split("==")[0].split(">=")[0].split("~=")[0].strip()

            # Framework detection
            if package in ["django", "flask", "fastapi", "tornado"]:
                technologies["frameworks"].add(package.capitalize())
            elif package in [
                "numpy",
                "pandas",
                "scikit-learn",
                "tensorflow",
                "pytorch",
            ]:
                technologies["libraries"].add(package)

    def get_pattern_candidates(self, commits: List[Dict]) -> List[Dict]:
        """Extract code snippets that could be patterns"""
        candidates = []

        for commit in commits:
            for file_change in commit["files_changed"]:
                if file_change["content"] and file_change["language"] != "Other":
                    # Extract meaningful code snippets
                    snippets = self._extract_code_snippets(
                        file_change["content"], file_change["language"]
                    )

                    for snippet in snippets:
                        candidates.append(
                            {
                                "code": snippet,
                                "language": file_change["language"],
                                "file_path": file_change["file_path"],
                                "commit_hash": commit["hash"],
                                "commit_date": commit["committed_date"],
                                "author": commit["author_email"],
                            }
                        )

        return candidates

    def _extract_code_snippets(self, content: str, language: str) -> List[str]:
        """Extract meaningful code snippets from file content"""
        snippets = []
        lines = content.split("\n")

        # Different strategies for different languages
        if language in ["JavaScript", "TypeScript", "React", "React TypeScript"]:
            snippets.extend(self._extract_js_snippets(lines))
        elif language == "Python":
            snippets.extend(self._extract_python_snippets(lines))

        return [s for s in snippets if len(s.strip()) > 20]  # Filter out tiny snippets

    def _extract_js_snippets(self, lines: List[str]) -> List[str]:
        """Extract JavaScript/React code snippets"""
        snippets = []
        current_snippet = []
        in_function = False
        brace_count = 0

        for line in lines:
            stripped_line = line.strip()

            # Skip empty lines and comments
            if (
                not stripped_line
                or stripped_line.startswith("//")
                or stripped_line.startswith("/*")
            ):
                continue

            # Look for function declarations, React components, hooks
            if any(
                pattern in stripped_line
                for pattern in [
                    "function ",
                    "const ",
                    "let ",
                    "var ",
                    "useState",
                    "useEffect",
                    "class ",
                    "export ",
                ]
            ):
                if current_snippet and len("\n".join(current_snippet)) > 50:
                    snippets.append("\n".join(current_snippet))
                current_snippet = [line]
                in_function = True
                brace_count = stripped_line.count("{") - stripped_line.count("}")
            elif in_function:
                current_snippet.append(line)
                brace_count += stripped_line.count("{") - stripped_line.count("}")

                if brace_count <= 0:
                    in_function = False
                    if len("\n".join(current_snippet)) > 50:
                        snippets.append("\n".join(current_snippet))
                    current_snippet = []

        return snippets

    def _extract_python_snippets(self, lines: List[str]) -> List[str]:
        """Extract Python code snippets"""
        snippets = []
        current_snippet = []
        in_function = False
        current_indent = 0

        for line in lines:
            stripped_line = line.strip()

            if not stripped_line or stripped_line.startswith("#"):
                continue

            line_indent = len(line) - len(line.lstrip())

            # Look for function/class definitions
            if stripped_line.startswith(("def ", "class ", "async def ")):
                if current_snippet and len("\n".join(current_snippet)) > 50:
                    snippets.append("\n".join(current_snippet))
                current_snippet = [line]
                in_function = True
                current_indent = line_indent
            elif in_function:
                if line_indent > current_indent or stripped_line == "":
                    current_snippet.append(line)
                else:
                    # Function ended
                    in_function = False
                    if len("\n".join(current_snippet)) > 50:
                        snippets.append("\n".join(current_snippet))
                    current_snippet = []

                    # Start new snippet if this is also a definition
                    if stripped_line.startswith(("def ", "class ", "async def ")):
                        current_snippet = [line]
                        in_function = True
                        current_indent = line_indent

        return snippets

    def cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                import stat

                def handle_remove_readonly(func, path, exc):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)

                shutil.rmtree(temp_dir, onerror=handle_remove_readonly)
            except Exception as e:
                logger.error(f"Error cleaning up temp directories: {e}")
        self.temp_dirs = []

    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()
