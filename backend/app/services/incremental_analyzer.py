"""
Incremental Analysis Service

Provides efficient re-analysis of repositories by detecting changes
and only analyzing modified parts, improving performance and reducing costs.
"""

import os
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of changes detected in files"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class FileChange:
    """Represents a change to a file"""
    file_path: str
    change_type: ChangeType
    old_path: Optional[str] = None  # For renamed files
    content_hash: Optional[str] = None
    size: Optional[int] = None
    modified_time: Optional[datetime] = None


@dataclass
class AnalysisSnapshot:
    """Snapshot of analysis state for comparison"""
    timestamp: datetime
    commit_hash: str
    file_hashes: Dict[str, str]  # file_path -> content_hash
    analysis_results: Dict[str, Any]  # cached analysis results
    total_files: int
    total_lines: int


class IncrementalAnalyzer:
    """
    Handles incremental analysis by tracking changes and selectively re-analyzing
    """
    
    def __init__(self):
        self.snapshots_cache: Dict[str, AnalysisSnapshot] = {}
        self.change_threshold = 0.1  # Re-analyze if >10% of files changed
        self.max_cache_age = timedelta(days=7)  # Cache snapshots for 7 days
        
    def create_snapshot(
        self, 
        repository_path: str, 
        commit_hash: str,
        analysis_results: Dict[str, Any]
    ) -> AnalysisSnapshot:
        """
        Create a snapshot of the current repository state
        
        Args:
            repository_path: Path to repository
            commit_hash: Current commit hash
            analysis_results: Analysis results to cache
            
        Returns:
            AnalysisSnapshot object
        """
        file_hashes = {}
        total_files = 0
        total_lines = 0
        
        try:
            # Walk through repository and hash all relevant files
            for root, dirs, files in os.walk(repository_path):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                    'node_modules', '__pycache__', 'target', 'build', 'dist'
                }]
                
                for file in files:
                    if self._should_analyze_file(file):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, repository_path)
                        
                        try:
                            content_hash = self._hash_file(file_path)
                            file_hashes[rel_path] = content_hash
                            total_files += 1
                            
                            # Count lines for metrics
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                total_lines += sum(1 for _ in f)
                                
                        except Exception as e:
                            logger.warning(f"Could not hash file {file_path}: {e}")
                            
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            
        snapshot = AnalysisSnapshot(
            timestamp=datetime.utcnow(),
            commit_hash=commit_hash,
            file_hashes=file_hashes,
            analysis_results=analysis_results,
            total_files=total_files,
            total_lines=total_lines
        )
        
        # Cache the snapshot
        self.snapshots_cache[repository_path] = snapshot
        logger.info(f"Created snapshot with {total_files} files, {total_lines} lines")
        
        return snapshot
        
    def detect_changes(
        self, 
        repository_path: str, 
        current_commit: str
    ) -> Tuple[List[FileChange], bool]:
        """
        Detect changes since last analysis
        
        Args:
            repository_path: Path to repository
            current_commit: Current commit hash
            
        Returns:
            Tuple of (changes_list, should_full_reanalyze)
        """
        changes = []
        should_full_reanalyze = False
        
        # Get previous snapshot
        previous_snapshot = self.snapshots_cache.get(repository_path)
        
        if not previous_snapshot:
            logger.info("No previous snapshot found, full analysis required")
            return [], True
            
        # Check if snapshot is too old
        if datetime.utcnow() - previous_snapshot.timestamp > self.max_cache_age:
            logger.info("Previous snapshot too old, full analysis required")
            return [], True
            
        # Check if commit changed significantly (could indicate major changes)
        if previous_snapshot.commit_hash != current_commit:
            logger.info(f"Commit changed: {previous_snapshot.commit_hash} -> {current_commit}")
            
        try:
            # Get current file state
            current_files = {}
            for root, dirs, files in os.walk(repository_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                    'node_modules', '__pycache__', 'target', 'build', 'dist'
                }]
                
                for file in files:
                    if self._should_analyze_file(file):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, repository_path)
                        
                        try:
                            content_hash = self._hash_file(file_path)
                            current_files[rel_path] = content_hash
                        except Exception as e:
                            logger.warning(f"Could not hash file {file_path}: {e}")
                            
            # Compare with previous snapshot
            previous_files = previous_snapshot.file_hashes
            
            # Find added files
            for file_path in current_files:
                if file_path not in previous_files:
                    changes.append(FileChange(
                        file_path=file_path,
                        change_type=ChangeType.ADDED,
                        content_hash=current_files[file_path]
                    ))
                    
            # Find modified files
            for file_path in current_files:
                if file_path in previous_files:
                    if current_files[file_path] != previous_files[file_path]:
                        changes.append(FileChange(
                            file_path=file_path,
                            change_type=ChangeType.MODIFIED,
                            content_hash=current_files[file_path]
                        ))
                        
            # Find deleted files
            for file_path in previous_files:
                if file_path not in current_files:
                    changes.append(FileChange(
                        file_path=file_path,
                        change_type=ChangeType.DELETED
                    ))
                    
            # Determine if full re-analysis is needed
            total_files = len(current_files)
            changed_files = len([c for c in changes if c.change_type in [ChangeType.ADDED, ChangeType.MODIFIED]])
            
            if total_files > 0:
                change_ratio = changed_files / total_files
                if change_ratio > self.change_threshold:
                    should_full_reanalyze = True
                    logger.info(f"Change ratio {change_ratio:.2%} exceeds threshold {self.change_threshold:.2%}")
                    
        except Exception as e:
            logger.error(f"Error detecting changes: {e}")
            should_full_reanalyze = True
            
        logger.info(f"Detected {len(changes)} changes, full reanalysis: {should_full_reanalyze}")
        return changes, should_full_reanalyze
        
    def get_incremental_candidates(
        self, 
        changes: List[FileChange], 
        repository_path: str
    ) -> List[Dict[str, Any]]:
        """
        Get pattern candidates for only changed files
        
        Args:
            changes: List of file changes
            repository_path: Path to repository
            
        Returns:
            List of pattern candidates for analysis
        """
        candidates = []
        
        for change in changes:
            if change.change_type in [ChangeType.ADDED, ChangeType.MODIFIED]:
                file_path = os.path.join(repository_path, change.file_path)
                
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        # Extract language from file extension
                        language = self._get_language_from_path(change.file_path)
                        
                        # Create candidate similar to GitService.get_pattern_candidates
                        candidates.append({
                            "file_path": change.file_path,
                            "code": content[:2000],  # Limit code size
                            "language": language,
                            "line_number": 1,
                            "change_type": change.change_type.value,
                            "content_hash": change.content_hash
                        })
                        
                    except Exception as e:
                        logger.warning(f"Could not read changed file {file_path}: {e}")
                        
        logger.info(f"Generated {len(candidates)} incremental candidates")
        return candidates
        
    def merge_analysis_results(
        self, 
        previous_results: Dict[str, Any], 
        incremental_results: Dict[str, Any],
        changes: List[FileChange]
    ) -> Dict[str, Any]:
        """
        Merge previous analysis results with incremental analysis
        
        Args:
            previous_results: Previous full analysis results
            incremental_results: Results from incremental analysis
            changes: List of file changes
            
        Returns:
            Merged analysis results
        """
        merged_results = previous_results.copy()
        
        try:
            # Update pattern analyses
            if "pattern_analyses" in incremental_results:
                if "pattern_analyses" not in merged_results:
                    merged_results["pattern_analyses"] = []
                merged_results["pattern_analyses"].extend(incremental_results["pattern_analyses"])
                
            # Update quality analyses
            if "quality_analyses" in incremental_results:
                if "quality_analyses" not in merged_results:
                    merged_results["quality_analyses"] = []
                merged_results["quality_analyses"].extend(incremental_results["quality_analyses"])
                
            # Update security analyses
            if "security_analyses" in incremental_results:
                if "security_analyses" not in merged_results:
                    merged_results["security_analyses"] = []
                merged_results["security_analyses"].extend(incremental_results["security_analyses"])
                
            # Update performance analyses
            if "performance_analyses" in incremental_results:
                if "performance_analyses" not in merged_results:
                    merged_results["performance_analyses"] = []
                merged_results["performance_analyses"].extend(incremental_results["performance_analyses"])
                
            # Update metadata
            merged_results["incremental_analysis"] = {
                "changes_analyzed": len(changes),
                "change_types": [c.change_type.value for c in changes],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Successfully merged incremental analysis results")
            
        except Exception as e:
            logger.error(f"Error merging analysis results: {e}")
            
        return merged_results
        
    def _should_analyze_file(self, filename: str) -> bool:
        """Check if file should be included in analysis"""
        # Source code extensions
        source_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.scala',
            '.clj', '.hs', '.ml', '.fs', '.r', '.m', '.sh', '.ps1', '.pl',
            '.lua', '.dart', '.elm', '.ex', '.exs', '.jl', '.nim', '.zig'
        }
        
        # Config and markup extensions
        config_extensions = {
            '.json', '.yaml', '.yml', '.toml', '.xml', '.html', '.css',
            '.scss', '.sass', '.less', '.md', '.dockerfile', '.makefile'
        }
        
        filename_lower = filename.lower()
        ext = os.path.splitext(filename_lower)[1]
        
        # Check extensions
        if ext in source_extensions or ext in config_extensions:
            return True
            
        # Check special filenames
        special_files = {
            'dockerfile', 'makefile', 'rakefile', 'gemfile', 'procfile',
            'package.json', 'requirements.txt', 'setup.py', 'cargo.toml'
        }
        
        return filename_lower in special_files
        
    def _hash_file(self, file_path: str) -> str:
        """Generate SHA-256 hash of file content"""
        hasher = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        except Exception as e:
            logger.warning(f"Could not hash file {file_path}: {e}")
            return ""
            
        return hasher.hexdigest()
        
    def _get_language_from_path(self, file_path: str) -> str:
        """Get programming language from file path"""
        ext = os.path.splitext(file_path.lower())[1]
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.scala': 'scala',
            '.clj': 'clojure',
            '.hs': 'haskell',
            '.ml': 'ocaml',
            '.fs': 'fsharp',
            '.r': 'r',
            '.m': 'objectivec',
            '.sh': 'bash',
            '.ps1': 'powershell',
            '.pl': 'perl',
            '.lua': 'lua',
            '.dart': 'dart',
            '.elm': 'elm',
            '.ex': 'elixir',
            '.exs': 'elixir',
            '.jl': 'julia',
            '.nim': 'nim',
            '.zig': 'zig'
        }
        
        return language_map.get(ext, 'unknown')


# Singleton instance
_incremental_analyzer = None

def get_incremental_analyzer() -> IncrementalAnalyzer:
    """Get singleton IncrementalAnalyzer instance"""
    global _incremental_analyzer
    if _incremental_analyzer is None:
        _incremental_analyzer = IncrementalAnalyzer()
        logger.info("🔧 Initialized IncrementalAnalyzer (singleton)")
    return _incremental_analyzer