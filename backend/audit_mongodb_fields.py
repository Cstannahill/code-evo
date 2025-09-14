#!/usr/bin/env python3
"""
MongoDB Field Audit and Migration Script

This script audits MongoDB models to identify missing fields compared to SQL models
and provides a migration plan to restore missing fields.
"""

import logging
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class FieldComparison:
    """Represents a field comparison between SQL and MongoDB models"""
    model_name: str
    field_name: str
    sql_type: str
    mongodb_exists: bool
    mongodb_type: str = None
    is_required: bool = False
    default_value: Any = None
    notes: str = ""

class MongoDBFieldAuditor:
    """Audits MongoDB models for missing fields compared to SQL models"""
    
    def __init__(self):
        self.comparisons: List[FieldComparison] = []
        self.missing_fields: Dict[str, List[str]] = {}
        self.extra_fields: Dict[str, List[str]] = {}
    
    def audit_models(self) -> Dict[str, Any]:
        """Perform comprehensive audit of all models"""
        logger.info("🔍 Starting MongoDB field audit...")
        
        # Define field mappings for each model
        model_mappings = {
            "Repository": {
                "sql_fields": {
                    "id": "String (UUID)",
                    "url": "String (unique)",
                    "name": "String",
                    "default_branch": "String",
                    "status": "String",
                    "total_commits": "Integer",
                    "created_at": "DateTime",
                    "last_analyzed": "DateTime",
                    "error_message": "Text"
                },
                "mongodb_fields": {
                    "id": "ObjectId",
                    "url": "String (unique)",
                    "name": "String",
                    "default_branch": "String",
                    "status": "String",
                    "total_commits": "Integer",
                    "created_at": "DateTime",
                    "updated_at": "DateTime",
                    "last_analyzed": "DateTime",
                    "error_message": "String",
                    "is_public": "Boolean (optional)",
                    "created_by_user": "ObjectId (optional)",
                    "analysis_count": "Integer (optional)",
                    "unique_users": "Integer (optional)",
                    "tags": "List[String] (optional)",
                    "description": "String (optional)",
                    "primary_language": "String (optional)"
                }
            },
            "Commit": {
                "sql_fields": {
                    "id": "String (UUID)",
                    "repository_id": "String (FK)",
                    "hash": "String (index)",
                    "author_name": "String",
                    "author_email": "String",
                    "committed_date": "DateTime",
                    "message": "Text",
                    "files_changed_count": "Integer",
                    "additions": "Integer",
                    "deletions": "Integer",
                    "stats": "JSON"
                },
                "mongodb_fields": {
                    "id": "ObjectId",
                    "repository_id": "ObjectId",
                    "hash": "String (index)",
                    "author_name": "String",
                    "author_email": "String",
                    "committed_date": "DateTime",
                    "message": "String",
                    "files_changed_count": "Integer",
                    "additions": "Integer",
                    "deletions": "Integer",
                    "stats": "Dict",
                    "analysis": "Dict (enhanced)",
                    "short_hash": "String",
                    "quality_indicators": "Dict"
                }
            },
            "Pattern": {
                "sql_fields": {
                    "id": "String (UUID)",
                    "name": "String (unique)",
                    "category": "String",
                    "description": "Text",
                    "complexity_level": "String",
                    "is_antipattern": "Boolean",
                    "created_at": "DateTime"
                },
                "mongodb_fields": {
                    "id": "ObjectId",
                    "name": "String (unique)",
                    "category": "String",
                    "description": "String",
                    "complexity_level": "String",
                    "is_antipattern": "Boolean",
                    "created_at": "DateTime",
                    "usage_count": "Integer",
                    "last_detected": "DateTime"
                }
            },
            "PatternOccurrence": {
                "sql_fields": {
                    "id": "String (UUID)",
                    "repository_id": "String (FK)",
                    "pattern_id": "String (FK)",
                    "file_path": "String",
                    "line_number": "Integer",
                    "confidence_score": "Float",
                    "detected_at": "DateTime",
                    "commit_id": "String (FK)"
                },
                "mongodb_fields": {
                    "id": "ObjectId",
                    "repository_id": "ObjectId",
                    "pattern_id": "ObjectId",
                    "file_path": "String",
                    "line_number": "Integer",
                    "confidence_score": "Float",
                    "detected_at": "DateTime",
                    "commit_id": "ObjectId",
                    "code_snippet": "String",
                    "ai_model_used": "String",
                    "model_confidence": "Float",
                    "processing_time_ms": "Integer",
                    "token_usage": "Dict",
                    "ai_analysis_metadata": "Dict"
                }
            },
            "Technology": {
                "sql_fields": {
                    "id": "String (UUID)",
                    "repository_id": "String (FK)",
                    "name": "String",
                    "category": "String",
                    "version": "String",
                    "file_count": "Integer",
                    "percentage": "Float"
                },
                "mongodb_fields": {
                    "id": "ObjectId",
                    "repository_id": "ObjectId",
                    "name": "String",
                    "category": "String",
                    "version": "String",
                    "file_count": "Integer",
                    "percentage": "Float",
                    "files": "List[String]",
                    "confidence": "Float",
                    "last_detected": "DateTime"
                }
            },
            "AnalysisSession": {
                "sql_fields": {
                    "id": "String (UUID)",
                    "repository_id": "String (FK)",
                    "started_at": "DateTime",
                    "completed_at": "DateTime",
                    "status": "String",
                    "analysis_type": "String",
                    "models_used": "JSON",
                    "total_files_analyzed": "Integer",
                    "total_commits_analyzed": "Integer"
                },
                "mongodb_fields": {
                    "id": "ObjectId",
                    "repository_id": "ObjectId",
                    "started_at": "DateTime",
                    "completed_at": "DateTime",
                    "status": "String",
                    "analysis_type": "String",
                    "models_used": "List[String]",
                    "total_files_analyzed": "Integer",
                    "total_commits_analyzed": "Integer",
                    "analysis_config": "Dict",
                    "performance_metrics": "Dict",
                    "error_details": "Dict",
                    "security_violations": "List[Dict]",
                    "incremental_efficiency": "Float"
                }
            }
        }
        
        # Perform comparisons
        for model_name, mappings in model_mappings.items():
            self._compare_model_fields(model_name, mappings)
        
        # Generate audit report
        return self._generate_audit_report()
    
    def _compare_model_fields(self, model_name: str, mappings: Dict[str, Dict[str, str]]):
        """Compare fields between SQL and MongoDB models"""
        sql_fields = mappings["sql_fields"]
        mongodb_fields = mappings["mongodb_fields"]
        
        # Check for missing fields in MongoDB
        missing_in_mongodb = []
        for field_name, sql_type in sql_fields.items():
            if field_name not in mongodb_fields:
                missing_in_mongodb.append(field_name)
                self.comparisons.append(FieldComparison(
                    model_name=model_name,
                    field_name=field_name,
                    sql_type=sql_type,
                    mongodb_exists=False,
                    notes=f"Missing from MongoDB model"
                ))
        
        # Check for extra fields in MongoDB
        extra_in_mongodb = []
        for field_name, mongodb_type in mongodb_fields.items():
            if field_name not in sql_fields:
                extra_in_mongodb.append(field_name)
                self.comparisons.append(FieldComparison(
                    model_name=model_name,
                    field_name=field_name,
                    sql_type="N/A",
                    mongodb_exists=True,
                    mongodb_type=mongodb_type,
                    notes=f"Enhanced field in MongoDB model"
                ))
        
        if missing_in_mongodb:
            self.missing_fields[model_name] = missing_in_mongodb
        if extra_in_mongodb:
            self.extra_fields[model_name] = extra_in_mongodb
    
    def _generate_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        total_missing = sum(len(fields) for fields in self.missing_fields.values())
        total_extra = sum(len(fields) for fields in self.extra_fields.values())
        
        report = {
            "audit_timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_models_audited": len(self.missing_fields) + len(self.extra_fields),
                "total_missing_fields": total_missing,
                "total_extra_fields": total_extra,
                "models_with_missing_fields": len(self.missing_fields),
                "models_with_extra_fields": len(self.extra_fields)
            },
            "missing_fields": self.missing_fields,
            "extra_fields": self.extra_fields,
            "detailed_comparisons": [
                {
                    "model": comp.model_name,
                    "field": comp.field_name,
                    "sql_type": comp.sql_type,
                    "mongodb_exists": comp.mongodb_exists,
                    "mongodb_type": comp.mongodb_type,
                    "notes": comp.notes
                }
                for comp in self.comparisons
            ],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for fixing missing fields"""
        recommendations = []
        
        if self.missing_fields:
            recommendations.append("🚨 CRITICAL: Add missing fields to MongoDB models")
            recommendations.append("📝 Update model definitions in app/models/repository.py")
            recommendations.append("🔄 Create data migration script to populate existing records")
            recommendations.append("✅ Add validation and default values for new fields")
        
        if self.extra_fields:
            recommendations.append("✨ MongoDB models have enhanced fields not in SQL")
            recommendations.append("🔍 Review enhanced fields for backward compatibility")
            recommendations.append("📊 Consider migrating enhanced fields to SQL models")
        
        recommendations.extend([
            "🛡️ Add field validation using Pydantic validators",
            "📈 Add database indexes for new queryable fields",
            "🧪 Create unit tests for model field validation",
            "📚 Update API documentation to reflect new fields"
        ])
        
        return recommendations

def main():
    """Main function to run the audit"""
    logging.basicConfig(level=logging.INFO)
    
    auditor = MongoDBFieldAuditor()
    report = auditor.audit_models()
    
    # Print summary
    print("🔍 MongoDB Field Audit Report")
    print("=" * 50)
    print(f"📊 Models audited: {report['summary']['total_models_audited']}")
    print(f"❌ Missing fields: {report['summary']['total_missing_fields']}")
    print(f"✨ Extra fields: {report['summary']['total_extra_fields']}")
    print()
    
    if report['missing_fields']:
        print("🚨 MISSING FIELDS:")
        for model, fields in report['missing_fields'].items():
            print(f"  {model}: {', '.join(fields)}")
        print()
    
    if report['extra_fields']:
        print("✨ ENHANCED FIELDS IN MONGODB:")
        for model, fields in report['extra_fields'].items():
            print(f"  {model}: {', '.join(fields)}")
        print()
    
    print("📋 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # Save detailed report
    import json
    with open('mongodb_field_audit_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: mongodb_field_audit_report.json")

if __name__ == "__main__":
    main()
