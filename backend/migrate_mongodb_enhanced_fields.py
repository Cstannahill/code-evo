#!/usr/bin/env python3
"""
MongoDB Enhanced Fields Migration Script

This script ensures all existing MongoDB records have the enhanced fields populated
with appropriate default values and validates data integrity.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
import json
from pathlib import Path

# Add the app directory to the Python path
import sys
sys.path.append(str(Path(__file__).parent))

from app.core.mongodb_config import initialize_mongodb, get_mongodb_manager
from app.models.repository import (
    Repository, Commit, Pattern, PatternOccurrence, Technology, AnalysisSession
)

logger = logging.getLogger(__name__)

class MongoDBFieldMigration:
    """Migrates MongoDB records to include enhanced fields"""
    
    def __init__(self):
        self.mongodb_manager = None
        self.engine = None
        self.migration_stats = {
            "repositories_updated": 0,
            "commits_updated": 0,
            "patterns_updated": 0,
            "pattern_occurrences_updated": 0,
            "technologies_updated": 0,
            "analysis_sessions_updated": 0,
            "errors": []
        }
    
    async def initialize(self):
        """Initialize MongoDB connection"""
        try:
            self.mongodb_manager = await initialize_mongodb()
            self.engine = self.mongodb_manager.get_engine()
            
            if not self.engine:
                raise Exception("MongoDB engine not available")
                
            logger.info("✅ MongoDB connection initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB: {e}")
            raise
    
    async def migrate_all_models(self) -> Dict[str, Any]:
        """Migrate all model types"""
        logger.info("🚀 Starting MongoDB enhanced fields migration...")
        
        try:
            # Migrate each model type
            await self.migrate_repositories()
            await self.migrate_commits()
            await self.migrate_patterns()
            await self.migrate_pattern_occurrences()
            await self.migrate_technologies()
            await self.migrate_analysis_sessions()
            
            # Generate migration report
            return self.generate_migration_report()
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            self.migration_stats["errors"].append(str(e))
            raise
    
    async def migrate_repositories(self):
        """Migrate Repository model enhanced fields"""
        logger.info("📁 Migrating Repository enhanced fields...")
        
        try:
            repositories = await self.engine.find(Repository)
            
            for repo in repositories:
                updated = False
                
                # Add missing enhanced fields with defaults
                if repo.updated_at is None:
                    repo.updated_at = repo.created_at
                    updated = True
                
                if repo.is_public is None:
                    repo.is_public = True  # Default to public for backward compatibility
                    updated = True
                
                if repo.analysis_count is None:
                    repo.analysis_count = 0
                    updated = True
                
                if repo.unique_users is None:
                    repo.unique_users = 0
                    updated = True
                
                if repo.tags is None:
                    repo.tags = []
                    updated = True
                
                if repo.description is None:
                    repo.description = ""
                    updated = True
                
                if repo.primary_language is None:
                    repo.primary_language = "unknown"
                    updated = True
                
                if updated:
                    await self.engine.save(repo)
                    self.migration_stats["repositories_updated"] += 1
                    logger.debug(f"✅ Updated repository: {repo.name}")
            
            logger.info(f"✅ Repository migration completed: {self.migration_stats['repositories_updated']} updated")
            
        except Exception as e:
            error_msg = f"Repository migration failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.migration_stats["errors"].append(error_msg)
    
    async def migrate_commits(self):
        """Migrate Commit model enhanced fields"""
        logger.info("📝 Migrating Commit enhanced fields...")
        
        try:
            commits = await self.engine.find(Commit)
            
            for commit in commits:
                updated = False
                
                # Add enhanced analysis fields
                if not hasattr(commit, 'analysis') or commit.analysis is None:
                    commit.analysis = {
                        "is_feature": False,
                        "is_bugfix": False,
                        "is_refactoring": False,
                        "is_breaking_change": False,
                        "complexity_impact": "low",
                        "risk_level": "low",
                        "patterns_detected": [],
                        "quality_indicators": {}
                    }
                    updated = True
                
                if not hasattr(commit, 'short_hash') or commit.short_hash is None:
                    commit.short_hash = commit.hash[:8] if commit.hash else ""
                    updated = True
                
                if not hasattr(commit, 'quality_indicators') or commit.quality_indicators is None:
                    commit.quality_indicators = {
                        "message_quality": "fair",
                        "author_experience": "unknown",
                        "commit_size": "small",
                        "complexity_change": "none"
                    }
                    updated = True
                
                if updated:
                    await self.engine.save(commit)
                    self.migration_stats["commits_updated"] += 1
                    logger.debug(f"✅ Updated commit: {commit.short_hash}")
            
            logger.info(f"✅ Commit migration completed: {self.migration_stats['commits_updated']} updated")
            
        except Exception as e:
            error_msg = f"Commit migration failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.migration_stats["errors"].append(error_msg)
    
    async def migrate_patterns(self):
        """Migrate Pattern model enhanced fields"""
        logger.info("🔍 Migrating Pattern enhanced fields...")
        
        try:
            patterns = await self.engine.find(Pattern)
            
            for pattern in patterns:
                updated = False
                
                if not hasattr(pattern, 'usage_count') or pattern.usage_count is None:
                    pattern.usage_count = 0
                    updated = True
                
                if not hasattr(pattern, 'last_detected') or pattern.last_detected is None:
                    pattern.last_detected = pattern.created_at
                    updated = True
                
                if updated:
                    await self.engine.save(pattern)
                    self.migration_stats["patterns_updated"] += 1
                    logger.debug(f"✅ Updated pattern: {pattern.name}")
            
            logger.info(f"✅ Pattern migration completed: {self.migration_stats['patterns_updated']} updated")
            
        except Exception as e:
            error_msg = f"Pattern migration failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.migration_stats["errors"].append(error_msg)
    
    async def migrate_pattern_occurrences(self):
        """Migrate PatternOccurrence model enhanced fields"""
        logger.info("📍 Migrating PatternOccurrence enhanced fields...")
        
        try:
            occurrences = await self.engine.find(PatternOccurrence)
            
            for occurrence in occurrences:
                updated = False
                
                # Add enhanced AI analysis fields
                if not hasattr(occurrence, 'code_snippet') or occurrence.code_snippet is None:
                    occurrence.code_snippet = ""
                    updated = True
                
                if not hasattr(occurrence, 'ai_model_used') or occurrence.ai_model_used is None:
                    occurrence.ai_model_used = "unknown"
                    updated = True
                
                if not hasattr(occurrence, 'model_confidence') or occurrence.model_confidence is None:
                    occurrence.model_confidence = occurrence.confidence_score
                    updated = True
                
                if not hasattr(occurrence, 'processing_time_ms') or occurrence.processing_time_ms is None:
                    occurrence.processing_time_ms = 0
                    updated = True
                
                if not hasattr(occurrence, 'token_usage') or occurrence.token_usage is None:
                    occurrence.token_usage = {}
                    updated = True
                
                if not hasattr(occurrence, 'ai_analysis_metadata') or occurrence.ai_analysis_metadata is None:
                    occurrence.ai_analysis_metadata = {}
                    updated = True
                
                if updated:
                    await self.engine.save(occurrence)
                    self.migration_stats["pattern_occurrences_updated"] += 1
                    logger.debug(f"✅ Updated pattern occurrence: {occurrence.id}")
            
            logger.info(f"✅ PatternOccurrence migration completed: {self.migration_stats['pattern_occurrences_updated']} updated")
            
        except Exception as e:
            error_msg = f"PatternOccurrence migration failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.migration_stats["errors"].append(error_msg)
    
    async def migrate_technologies(self):
        """Migrate Technology model enhanced fields"""
        logger.info("🛠️ Migrating Technology enhanced fields...")
        
        try:
            technologies = await self.engine.find(Technology)
            
            for tech in technologies:
                updated = False
                
                if not hasattr(tech, 'files') or tech.files is None:
                    tech.files = []
                    updated = True
                
                if not hasattr(tech, 'confidence') or tech.confidence is None:
                    tech.confidence = 1.0
                    updated = True
                
                if not hasattr(tech, 'last_detected') or tech.last_detected is None:
                    tech.last_detected = datetime.utcnow()
                    updated = True
                
                if updated:
                    await self.engine.save(tech)
                    self.migration_stats["technologies_updated"] += 1
                    logger.debug(f"✅ Updated technology: {tech.name}")
            
            logger.info(f"✅ Technology migration completed: {self.migration_stats['technologies_updated']} updated")
            
        except Exception as e:
            error_msg = f"Technology migration failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.migration_stats["errors"].append(error_msg)
    
    async def migrate_analysis_sessions(self):
        """Migrate AnalysisSession model enhanced fields"""
        logger.info("📊 Migrating AnalysisSession enhanced fields...")
        
        try:
            sessions = await self.engine.find(AnalysisSession)
            
            for session in sessions:
                updated = False
                
                if not hasattr(session, 'analysis_config') or session.analysis_config is None:
                    session.analysis_config = {}
                    updated = True
                
                if not hasattr(session, 'performance_metrics') or session.performance_metrics is None:
                    session.performance_metrics = {}
                    updated = True
                
                if not hasattr(session, 'error_details') or session.error_details is None:
                    session.error_details = {}
                    updated = True
                
                if not hasattr(session, 'security_violations') or session.security_violations is None:
                    session.security_violations = []
                    updated = True
                
                if not hasattr(session, 'incremental_efficiency') or session.incremental_efficiency is None:
                    session.incremental_efficiency = 0.0
                    updated = True
                
                if updated:
                    await self.engine.save(session)
                    self.migration_stats["analysis_sessions_updated"] += 1
                    logger.debug(f"✅ Updated analysis session: {session.id}")
            
            logger.info(f"✅ AnalysisSession migration completed: {self.migration_stats['analysis_sessions_updated']} updated")
            
        except Exception as e:
            error_msg = f"AnalysisSession migration failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.migration_stats["errors"].append(error_msg)
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """Generate migration report"""
        total_updated = sum([
            self.migration_stats["repositories_updated"],
            self.migration_stats["commits_updated"],
            self.migration_stats["patterns_updated"],
            self.migration_stats["pattern_occurrences_updated"],
            self.migration_stats["technologies_updated"],
            self.migration_stats["analysis_sessions_updated"]
        ])
        
        report = {
            "migration_timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_records_updated": total_updated,
                "models_migrated": 6,
                "errors_count": len(self.migration_stats["errors"]),
                "success": len(self.migration_stats["errors"]) == 0
            },
            "detailed_stats": self.migration_stats,
            "recommendations": [
                "✅ Enhanced fields migration completed successfully",
                "🔄 Restart the application to ensure all changes are loaded",
                "📊 Monitor application performance after migration",
                "🧪 Run integration tests to verify data integrity"
            ] if len(self.migration_stats["errors"]) == 0 else [
                "⚠️ Some migrations encountered errors - review error details",
                "🔄 Re-run migration script to fix remaining issues",
                "📞 Contact support if errors persist"
            ]
        }
        
        return report
    
    async def cleanup(self):
        """Cleanup MongoDB connections"""
        if self.mongodb_manager:
            await self.mongodb_manager.disconnect()
            logger.info("✅ MongoDB connection closed")

async def main():
    """Main migration function"""
    logging.basicConfig(level=logging.INFO)
    
    migration = MongoDBFieldMigration()
    
    try:
        await migration.initialize()
        report = await migration.migrate_all_models()
        
        # Print summary
        print("🚀 MongoDB Enhanced Fields Migration Report")
        print("=" * 60)
        print(f"📊 Total records updated: {report['summary']['total_records_updated']}")
        print(f"📁 Models migrated: {report['summary']['models_migrated']}")
        print(f"❌ Errors: {report['summary']['errors_count']}")
        print(f"✅ Success: {report['summary']['success']}")
        print()
        
        print("📈 DETAILED STATS:")
        for model, count in report['detailed_stats'].items():
            if model != 'errors':
                print(f"  {model}: {count}")
        
        if report['detailed_stats']['errors']:
            print("\n❌ ERRORS:")
            for error in report['detailed_stats']['errors']:
                print(f"  - {error}")
        
        print("\n📋 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        # Save detailed report
        with open('mongodb_migration_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: mongodb_migration_report.json")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return 1
    finally:
        await migration.cleanup()
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
