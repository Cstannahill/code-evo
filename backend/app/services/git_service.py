from git import Repo, GitCommandError
import tempfile
import os
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
                # parse known files
                if name == "package.json":
                    self._parse_package_json(item.data_stream.read().decode(), tech)
                if name == "requirements.txt":
                    self._parse_requirements_txt(item.data_stream.read().decode(), tech)
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
            if "react" in deps:
                tech["frameworks"].add("React")
            if "express" in deps:
                tech["frameworks"].add("Express.js")
            if "next" in deps:
                tech["frameworks"].add("Next.js")
            if "webpack" in deps:
                tech["tools"].add("Webpack")
        except Exception as e:
            logger.warning(f"Error parsing package.json: {e}")

    def _parse_requirements_txt(self, content: str, tech: Dict) -> None:
        for line in content.split("\n"):
            pkg = line.strip().split("==")[0].lower()
            if pkg in ("django", "flask", "fastapi"):
                tech["frameworks"].add(pkg.capitalize())
            if pkg in ("numpy", "pandas"):
                tech["libraries"].add(pkg)

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
        return candidates

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

    def cleanup(self) -> None:
        """Remove all temp dirs"""
        for d in self.temp_dirs:
            try:
                shutil.rmtree(d)
                logger.info(f"Cleaned {d}")
            except Exception as e:
                logger.error(f"Cleanup error {d}: {e}")
        self.temp_dirs = []

    def __del__(self):
        self.cleanup()
