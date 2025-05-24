# app/api/analysis.py - Updated with working AI integration
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
import asyncio

from app.core.database import get_db
from app.models.repository import Repository, Pattern, PatternOccurrence
from app.services.ai_service import AIService  # Now working!

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize AI service
ai_service = AIService()


@router.get("/analysis/status")
async def get_ai_status():
    logger.info(f"Status Hit")
    """Get AI service status - NEW ENDPOINT"""
    status = ai_service.get_status()
    return {
        "ai_service": status,
        "recommendations": {
            "ollama_missing": (
                "Run 'ollama serve' and 'ollama pull codellama:7b'"
                if not status["ollama_available"]
                else None
            ),
            "ready_for_analysis": status["ollama_available"],
        },
    }


@router.post("/analysis/code")
async def analyze_code_snippet(request: Dict[str, str], db: Session = Depends(get_db)):
    """Analyze a code snippet for patterns - NOW WITH REAL AI!"""
    try:
        code = request.get("code", "")
        language = request.get("language", "javascript")

        if not code:
            raise HTTPException(status_code=400, detail="Code is required")
        print(f"Status Hit")
        logger.info(f"🤖 Analyzing {len(code)} chars of {language} code")

        # Use AI service for pattern analysis
        pattern_result = await ai_service.analyze_code_pattern(code, language)

        # Use AI service for quality analysis
        quality_result = await ai_service.analyze_code_quality(code, language)

        # Find similar patterns
        similar_patterns = await ai_service.find_similar_patterns(code, limit=3)

        response = {
            "code": code,
            "language": language,
            "pattern_analysis": pattern_result,
            "quality_analysis": quality_result,
            "similar_patterns": similar_patterns,
            "ai_powered": ai_service.ollama_available,  # Let frontend know if AI is working
            "analysis_timestamp": "2024-01-01T00:00:00Z",
        }

        logger.info(
            f"✅ Analysis complete: {len(pattern_result.get('combined_patterns', []))} patterns found"
        )
        return response

    except Exception as e:
        logger.error(f"Error analyzing code snippet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/patterns")
async def get_all_patterns(db: Session = Depends(get_db)):
    """Get all detected patterns across repositories"""
    try:
        patterns = (
            db.query(PatternOccurrence)
            .join(Pattern)
            .order_by(PatternOccurrence.detected_at.desc())
            .limit(100)
            .all()
        )

        return [
            {
                "pattern_name": p.pattern.name,
                "file_path": p.file_path,
                "code_snippet": p.code_snippet,
                "confidence_score": p.confidence_score,
                "detected_at": p.detected_at.isoformat(),
            }
            for p in patterns
        ]

    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        return []


@router.get("/analysis/patterns/{pattern_name}")
async def get_pattern_details(pattern_name: str, db: Session = Depends(get_db)):
    """Get details for a specific pattern"""
    try:
        pattern = db.query(Pattern).filter(Pattern.name == pattern_name).first()
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")

        occurrences = (
            db.query(PatternOccurrence)
            .filter(PatternOccurrence.pattern_id == pattern.id)
            .order_by(PatternOccurrence.detected_at.desc())
            .limit(50)
            .all()
        )

        return {
            "pattern": {
                "name": pattern.name,
                "category": pattern.category,
                "description": pattern.description,
                "complexity_level": pattern.complexity_level,
                "is_antipattern": pattern.is_antipattern,
            },
            "occurrences": [
                {
                    "file_path": occ.file_path,
                    "code_snippet": occ.code_snippet,
                    "confidence_score": occ.confidence_score,
                    "detected_at": occ.detected_at.isoformat(),
                    "repository_id": str(occ.repository_id),
                }
                for occ in occurrences
            ],
            "statistics": {
                "total_occurrences": len(occurrences),
                "repositories_using": len(
                    set(occ.repository_id for occ in occurrences)
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pattern details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/insights/{repo_id}")
async def get_repository_insights(repo_id: str, db: Session = Depends(get_db)):
    """Get AI-generated insights for a repository - NOW WITH REAL AI!"""
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

        # Get pattern statistics
        patterns = (
            db.query(Pattern)
            .join(PatternOccurrence)
            .filter(PatternOccurrence.repository_id == repo_id)
            .distinct()
            .all()
        )

        pattern_stats = {}
        for pattern in patterns:
            occurrences = (
                db.query(PatternOccurrence)
                .filter(
                    PatternOccurrence.pattern_id == pattern.id,
                    PatternOccurrence.repository_id == repo_id,
                )
                .all()
            )

            pattern_stats[pattern.name] = {
                "category": pattern.category,
                "occurrences": len(occurrences),
                "complexity_level": pattern.complexity_level,
                "is_antipattern": pattern.is_antipattern,
            }

        # Generate AI insights if available
        ai_insights = []
        if ai_service.ollama_available:
            try:
                # Analyze repository evolution
                analysis_data = {
                    "patterns": pattern_stats,
                    "technologies": [tech.name for tech in repo.technologies],
                    "commits": repo.total_commits,
                }

                ai_insights = await ai_service.generate_insights(analysis_data)
                logger.info(f"🤖 Generated {len(ai_insights)} AI insights")

            except Exception as e:
                logger.error(f"AI insight generation failed: {e}")
                ai_insights = [
                    {
                        "type": "error",
                        "title": "AI Analysis Error",
                        "description": str(e),
                    }
                ]

        # Combine basic and AI insights
        insights = [
            {
                "type": "info",
                "title": "Repository Overview",
                "description": f"Analyzed {repo.total_commits} commits with {len(patterns)} patterns detected.",
                "data": {
                    "repository_id": repo_id,
                    "patterns": pattern_stats,
                    "total_commits": repo.total_commits,
                    "technologies": [tech.name for tech in repo.technologies],
                },
            }
        ] + ai_insights

        return {
            "repository_id": repo_id,
            "pattern_timeline": {"timeline": [], "summary": {}},
            "pattern_statistics": pattern_stats,
            "insights": insights,
            "ai_powered": ai_service.ollama_available,
            "summary": {
                "total_patterns": len(patterns),
                "antipatterns_detected": sum(1 for p in patterns if p.is_antipattern),
                "complexity_distribution": _get_complexity_distribution(patterns),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting repository insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/evolution")
async def analyze_code_evolution(request: Dict, db: Session = Depends(get_db)):
    """Analyze evolution between two code versions - NEW ENDPOINT"""
    try:
        old_code = request.get("old_code", "")
        new_code = request.get("new_code", "")
        context = request.get("context", "")

        if not old_code or not new_code:
            raise HTTPException(
                status_code=400, detail="Both old_code and new_code are required"
            )

        # Use AI service for evolution analysis
        evolution_result = await ai_service.analyze_evolution(
            old_code, new_code, context
        )

        return {
            "evolution_analysis": evolution_result,
            "ai_powered": ai_service.ollama_available,
            "timestamp": "2024-01-01T00:00:00Z",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing code evolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/compare/{repo_id1}/{repo_id2}")
async def compare_repositories(
    repo_id1: str, repo_id2: str, db: Session = Depends(get_db)
):
    """Compare two repositories - ENHANCED WITH AI"""
    try:
        repo1 = db.query(Repository).filter(Repository.id == repo_id1).first()
        repo2 = db.query(Repository).filter(Repository.id == repo_id2).first()

        if not repo1 or not repo2:
            raise HTTPException(
                status_code=404, detail="One or both repositories not found"
            )

        # Get patterns for both repositories
        patterns1 = set(
            p.pattern.name
            for p in db.query(PatternOccurrence)
            .filter(PatternOccurrence.repository_id == repo_id1)
            .all()
        )

        patterns2 = set(
            p.pattern.name
            for p in db.query(PatternOccurrence)
            .filter(PatternOccurrence.repository_id == repo_id2)
            .all()
        )

        # Get technologies for both repositories
        tech1 = set(tech.name for tech in repo1.technologies)
        tech2 = set(tech.name for tech in repo2.technologies)

        # Calculate similarity
        similarity_score = _calculate_similarity_score(
            patterns1, patterns2, tech1, tech2
        )

        comparison = {
            "repository_1": {
                "id": repo_id1,
                "name": repo1.name,
                "total_commits": repo1.total_commits,
                "patterns": list(patterns1),
                "technologies": list(tech1),
            },
            "repository_2": {
                "id": repo_id2,
                "name": repo2.name,
                "total_commits": repo2.total_commits,
                "patterns": list(patterns2),
                "technologies": list(tech2),
            },
            "comparison": {
                "common_patterns": list(patterns1.intersection(patterns2)),
                "unique_to_repo1": list(patterns1.difference(patterns2)),
                "unique_to_repo2": list(patterns2.difference(patterns1)),
                "common_technologies": list(tech1.intersection(tech2)),
                "unique_tech_repo1": list(tech1.difference(tech2)),
                "unique_tech_repo2": list(tech2.difference(tech1)),
                "similarity_score": similarity_score,
            },
            "ai_powered": ai_service.ollama_available,
        }

        return comparison

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_complexity_distribution(patterns: List[Pattern]) -> Dict[str, int]:
    """Get distribution of pattern complexity levels"""
    distribution = {"simple": 0, "intermediate": 0, "advanced": 0}

    for pattern in patterns:
        level = pattern.complexity_level or "intermediate"
        if level in distribution:
            distribution[level] += 1

    return distribution


def _calculate_similarity_score(
    patterns1: set, patterns2: set, tech1: set, tech2: set
) -> float:
    """Calculate similarity score between two repositories"""
    if not patterns1 and not patterns2 and not tech1 and not tech2:
        return 1.0

    # Jaccard similarity for patterns
    pattern_union = patterns1.union(patterns2)
    pattern_intersection = patterns1.intersection(patterns2)
    pattern_similarity = (
        len(pattern_intersection) / len(pattern_union) if pattern_union else 0
    )

    # Jaccard similarity for technologies
    tech_union = tech1.union(tech2)
    tech_intersection = tech1.intersection(tech2)
    tech_similarity = len(tech_intersection) / len(tech_union) if tech_union else 0

    # Weighted average (patterns matter more)
    return (pattern_similarity * 0.7) + (tech_similarity * 0.3)
