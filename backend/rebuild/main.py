from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import re

app = FastAPI(title="Rebuilt Backend")


class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"


class CompareRequest(CodeAnalysisRequest):
    models: List[str]


# Simple heuristics for pattern detection
PATTERN_MAP = {
    "class_pattern": r"class \w+",
    "function_definition": r"def \w+|function \w+",
    "async_function": r"async def|async ",
    "promise_pattern": r"\.then\(|Promise",
    "error_handling": r"try:|catch \(",
}

TECH_KEYWORDS = {
    "react": ["React", "useState"],
    "vue": ["Vue", "vuex"],
    "django": ["django"],
    "flask": ["flask"],
}


def detect_patterns(code: str) -> List[str]:
    found = []
    for name, pattern in PATTERN_MAP.items():
        if re.search(pattern, code, re.IGNORECASE):
            found.append(name)
    return found


def detect_technologies(code: str) -> List[str]:
    techs = []
    for tech, keywords in TECH_KEYWORDS.items():
        for k in keywords:
            if k.lower() in code.lower():
                techs.append(tech)
                break
    return techs


def simple_complexity(code: str) -> float:
    indicators = [
        code.count(tok) for tok in ["if", "for", "while", "class", "def", "function"]
    ]
    length_factor = len(code.splitlines()) / 10
    return min(10.0, sum(indicators) + length_factor)


def determine_skill_level(score: float, patterns: List[str]) -> str:
    if score > 8 or "async_function" in patterns:
        return "advanced"
    if score > 4 or "class_pattern" in patterns:
        return "intermediate"
    return "beginner"


def build_analysis(code: str, language: str) -> Dict[str, Any]:
    patterns = detect_patterns(code)
    techs = detect_technologies(code)
    complexity = simple_complexity(code)
    skill = determine_skill_level(complexity, patterns)
    quality = max(0, 100 - complexity * 10)
    return {
        "code": code,
        "language": language,
        "pattern_analysis": {
            "detected_patterns": patterns,
            "ai_patterns": [],
            "combined_patterns": patterns,
            "complexity_score": complexity,
            "skill_level": skill,
            "suggestions": [],
        },
        "quality_analysis": {
            "quality_score": quality,
            "readability": "Good" if quality > 70 else "Fair",
            "issues": [],
            "improvements": [],
        },
        "similar_patterns": [],
        "technologies": techs,
        "ai_powered": False,
        "analysis_timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/analyze/code")
async def analyze_code(req: CodeAnalysisRequest):
    return build_analysis(req.code, req.language)


@app.post("/analyze/compare")
async def compare_models(req: CompareRequest):
    if len(req.models) != 2:
        raise HTTPException(status_code=400, detail="Provide exactly two models")
    results = []
    for model in req.models:
        result = build_analysis(req.code, req.language)
        result["model"] = model
        results.append(result)
    return {
        "models": req.models,
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
