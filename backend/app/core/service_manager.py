"""
Centralized Service Manager
Handles singleton pattern for all services to prevent re-initialization
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global service instances
_service_instances = {}

def get_service_instance(service_class, service_name: str):
    """Get or create a singleton service instance"""
    if service_name not in _service_instances:
        logger.info(f"🔧 Initializing {service_name} (singleton)")
        _service_instances[service_name] = service_class()
    return _service_instances[service_name]

def get_repository_service():
    """Get singleton RepositoryService instance"""
    from app.services.repository_service import RepositoryService
    return get_service_instance(RepositoryService, "RepositoryService")

def get_pattern_service():
    """Get singleton PatternService instance"""
    from app.services.pattern_service import PatternService
    return get_service_instance(PatternService, "PatternService")

def get_ai_analysis_service():
    """Get singleton AIAnalysisService instance"""
    from app.services.ai_analysis_service import AIAnalysisService
    return get_service_instance(AIAnalysisService, "AIAnalysisService")

def get_analysis_service():
    """Get singleton AnalysisService instance"""
    from app.services.analysis_service import AnalysisService
    return get_service_instance(AnalysisService, "AnalysisService")

def get_ai_service():
    """Get singleton AIService instance"""
    from app.services.ai_service import AIService
    return get_service_instance(AIService, "AIService")

def get_git_service():
    """Get singleton GitService instance"""
    from app.services.git_service import GitService
    return get_service_instance(GitService, "GitService")

def clear_service_instances():
    """Clear all service instances (for testing or restart)"""
    global _service_instances
    _service_instances.clear()
    logger.info("🧹 All service instances cleared")