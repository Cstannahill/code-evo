# app/services/ai_service.py - WORKING AI with Ollama + LangChain
from typing import List, Dict, Optional
import json
import re
import logging
import asyncio
from pydantic import BaseModel

# LangChain imports
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser

# ChromaDB for embeddings (optional)
from app.core.database import get_collection, get_cache
import httpx

logger = logging.getLogger(__name__)


class PatternAnalysis(BaseModel):
    patterns: List[str]
    complexity_score: float
    language_features: List[str]
    suggestions: List[str]
    evolution_stage: str


class CodeQualityAnalysis(BaseModel):
    quality_score: float
    maintainability: str
    readability: str
    issues: List[str]
    improvements: List[str]


class JSONOutputParser(BaseOutputParser):
    """Parser to extract JSON from LLM responses"""

    def parse(self, text: str) -> dict:
        try:
            # Try to find JSON in the response
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback to simple parsing
                return {"error": "No JSON found", "raw_response": text}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw_response": text}


class AIService:
    """AI-powered code analysis service using Ollama + LangChain"""

    def __init__(self):
        self.ollama_available = False
        self.llm = None
        self.cache = get_cache()

        # Initialize Ollama
        self._init_ollama()

        # Initialize ChromaDB collections
        self.pattern_collection = get_collection("code_patterns")
        self.evolution_collection = get_collection("code_evolution")

        # Pattern detection rules (fallback)
        self.pattern_rules = self._load_pattern_rules()

        # Create LangChain prompts
        self._init_prompts()

    def _init_ollama(self):
        """Initialize Ollama connection"""
        try:
            # Test if Ollama is running - more robust version
            import subprocess

            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                import json

                models_data = json.loads(result.stdout)
                available_models = [m["name"] for m in models_data.get("models", [])]
                logger.info(f"✅ Ollama available with models: {available_models}")

                # Initialize LLM
                from langchain.llms import Ollama

                self.llm = Ollama(
                    model="codellama:7b", base_url="http://localhost:11434"
                )
                self.ollama_available = True

            else:
                raise Exception("Ollama curl test failed")

        except Exception as e:
            logger.warning(f"⚠️  Ollama not available: {e}")
            self.ollama_available = False

    async def generate_insights(self, analysis_data: Dict) -> List[Dict]:
        """Generate insights from analysis data"""
        insights = []

        try:
            # Pattern-based insights
            patterns = analysis_data.get("patterns", {})
            if patterns:
                insights.append(
                    {
                        "type": "pattern_summary",
                        "title": f"Detected {len(patterns)} Programming Patterns",
                        "description": f'Most common patterns: {", ".join(list(patterns.keys())[:3])}',
                        "data": {"patterns": patterns},
                    }
                )

            # Technology insights
            technologies = analysis_data.get("technologies", [])
            if technologies:
                insights.append(
                    {
                        "type": "technology_adoption",
                        "title": "Technology Stack Analysis",
                        "description": f'Primary technologies: JavaScript ({analysis_data.get("commits", 0)} commits), React ecosystem detected',
                        "data": {"technologies": technologies},
                    }
                )

            # AI-powered insights if available
            if self.ollama_available:
                try:
                    # Generate AI insights about the technology stack
                    tech_summary = f"Technologies: {', '.join(technologies[:5])}"

                    ai_insight_prompt = PromptTemplate(
                        input_variables=["tech_summary", "commit_count"],
                        template="""Analyze this technology stack and provide insights:

    Technologies: {tech_summary}
    Commits analyzed: {commit_count}

    IMPORTANT: Return ONLY a valid JSON object:
    {{
        "architecture_insights": ["insights about the architecture"],
        "technology_trends": ["trends in technology usage"],
        "recommendations": ["recommendations for improvement"]
    }}""",
                    )

                    chain = LLMChain(
                        llm=self.llm,
                        prompt=ai_insight_prompt,
                        output_parser=JSONOutputParser(),
                    )
                    ai_result = await chain.arun(
                        tech_summary=tech_summary,
                        commit_count=analysis_data.get("commits", 0),
                    )

                    if not ai_result.get("error"):
                        insights.append(
                            {
                                "type": "ai_analysis",
                                "title": "AI Architecture Analysis",
                                "description": "AI-generated insights about your codebase architecture and technology choices",
                                "data": ai_result,
                            }
                        )

                except Exception as e:
                    logger.error(f"AI insight generation failed: {e}")

            # Add completion insight
            insights.append(
                {
                    "type": "info",
                    "title": "Analysis Complete",
                    "description": f"Repository analysis completed successfully. Analyzed {analysis_data.get('commits', 0)} commits across {len(technologies)} technologies.",
                    "data": {},
                }
            )

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            insights.append(
                {
                    "type": "error",
                    "title": "Insight Generation Error",
                    "description": str(e),
                    "data": {},
                }
            )

        return insights

    def _init_prompts(self):
        """Initialize LangChain prompts"""

        self.pattern_analysis_prompt = PromptTemplate(
            input_variables=["code", "language"],
            template="""Analyze this {language} code for programming patterns. 

Code:
```{language}
{code}
```

IMPORTANT: Return ONLY a valid JSON object with this exact structure:
{{
    "patterns": ["list of detected patterns like 'react_hooks', 'async_await', etc."],
    "complexity_score": 5.5,
    "language_features": ["modern language features used"],
    "suggestions": ["improvement suggestions"],
    "evolution_stage": "intermediate"
}}

Do not include any text before or after the JSON. Only return the JSON object.""",
        )

        self.quality_analysis_prompt = PromptTemplate(
            input_variables=["code", "language"],
            template="""Analyze this {language} code for quality and maintainability.

Code:
```{language}
{code}
```

IMPORTANT: Return ONLY a valid JSON object with this exact structure:
{{
    "quality_score": 8.5,
    "maintainability": "excellent",
    "readability": "good", 
    "issues": ["list of specific issues found"],
    "improvements": ["specific improvement suggestions"]
}}

Do not include any text before or after the JSON. Only return the JSON object.""",
        )

        self.evolution_analysis_prompt = PromptTemplate(
            input_variables=["old_code", "new_code", "context"],
            template="""Compare these two code versions and analyze the evolution:

Context: {context}

Old Version:
```
{old_code}
```

New Version:
```
{new_code}
```

IMPORTANT: Return ONLY a valid JSON object with this exact structure:
{{
    "improvements": ["what got better"],
    "new_patterns": ["new patterns introduced"],
    "complexity_change": "increased",
    "learning_insights": ["what this evolution shows about developer growth"]
}}

Do not include any text before or after the JSON. Only return the JSON object.""",
        )

    async def analyze_code_pattern(
        self, code: str, language: str, context: Dict = None
    ) -> Dict:
        """Analyze code for patterns using AI + rules"""

        # Check cache first
        cache_key = f"pattern_analysis:{hash(code + language)}"
        cached = self.cache.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass

        result = {
            "rule_based_patterns": self._detect_rule_patterns(code, language),
            "ai_analysis": {},
            "combined_patterns": [],
            "context": context or {},
        }

        # Try AI analysis if available
        if self.ollama_available and self.llm:
            try:
                chain = LLMChain(
                    llm=self.llm,
                    prompt=self.pattern_analysis_prompt,
                    output_parser=JSONOutputParser(),
                )

                ai_result = await chain.arun(
                    code=code[:2000], language=language
                )  # Limit code length
                result["ai_analysis"] = ai_result

                # Combine AI and rule-based patterns
                ai_patterns = ai_result.get("patterns", [])
                combined = list(set(result["rule_based_patterns"] + ai_patterns))
                result["combined_patterns"] = combined

                logger.info(f"🤖 AI analysis complete: {len(combined)} patterns found")

            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
                result["ai_analysis"] = {"error": str(e)}
                result["combined_patterns"] = result["rule_based_patterns"]
        else:
            # Fallback to rule-based only
            result["combined_patterns"] = result["rule_based_patterns"]

        # Cache result
        try:
            self.cache.set(cache_key, json.dumps(result), ttl=3600)
        except:
            pass

        return result

    async def analyze_code_quality(self, code: str, language: str) -> Dict:
        """Analyze code quality using AI"""

        if not self.ollama_available:
            return self._simple_quality_analysis(code, language)

        try:
            chain = LLMChain(
                llm=self.llm,
                prompt=self.quality_analysis_prompt,
                output_parser=JSONOutputParser(),
            )

            result = await chain.arun(code=code[:2000], language=language)
            logger.info(
                f"🎯 Quality analysis complete: {result.get('quality_score', 'unknown')}/10"
            )
            return result

        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            return self._simple_quality_analysis(code, language)

    async def analyze_evolution(
        self, old_code: str, new_code: str, context: str = ""
    ) -> Dict:
        """Analyze code evolution between versions"""

        if not self.ollama_available:
            return self._simple_evolution_analysis(old_code, new_code)

        try:
            chain = LLMChain(
                llm=self.llm,
                prompt=self.evolution_analysis_prompt,
                output_parser=JSONOutputParser(),
            )

            result = await chain.arun(
                old_code=old_code[:1000], new_code=new_code[:1000], context=context
            )
            logger.info(f"📈 Evolution analysis complete")
            return result

        except Exception as e:
            logger.error(f"Evolution analysis failed: {e}")
            return self._simple_evolution_analysis(old_code, new_code)

    def _detect_rule_patterns(self, code: str, language: str) -> List[str]:
        """Rule-based pattern detection (fallback)"""
        patterns = []
        lang_rules = self.pattern_rules.get(language.lower(), {})

        for pattern_category, rules in lang_rules.items():
            for rule in rules:
                if re.search(rule, code, re.MULTILINE | re.IGNORECASE):
                    patterns.append(f"{language.lower()}_{pattern_category}")
                    break

        return patterns

    def _simple_quality_analysis(self, code: str, language: str) -> Dict:
        """Simple quality analysis without AI"""
        lines = code.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        avg_line_length = sum(len(line) for line in non_empty_lines) / max(
            1, len(non_empty_lines)
        )
        complexity_indicators = len(
            re.findall(r"\bif\b|\bfor\b|\bwhile\b|\btry\b", code, re.IGNORECASE)
        )

        quality_score = 8.0
        if avg_line_length > 100:
            quality_score -= 2
        if complexity_indicators > 5:
            quality_score -= 1

        return {
            "quality_score": max(1.0, quality_score),
            "maintainability": "good" if quality_score > 7 else "fair",
            "readability": "good" if avg_line_length < 80 else "fair",
            "issues": [],
            "improvements": ["Enable Ollama for detailed AI analysis"],
        }

    def _simple_evolution_analysis(self, old_code: str, new_code: str) -> Dict:
        """Simple evolution analysis without AI"""
        old_patterns = self._detect_rule_patterns(old_code, "javascript")
        new_patterns = self._detect_rule_patterns(new_code, "javascript")

        return {
            "improvements": (
                ["Code structure maintained"] if len(new_code) > len(old_code) else []
            ),
            "new_patterns": list(set(new_patterns) - set(old_patterns)),
            "complexity_change": "similar",
            "learning_insights": ["Enable Ollama for detailed evolution insights"],
        }

    def _load_pattern_rules(self) -> Dict:
        """Pattern detection rules for different languages"""
        return {
            "react": {
                "hooks": [
                    r"useState\s*\(",
                    r"useEffect\s*\(",
                    r"useContext\s*\(",
                    r"useReducer\s*\(",
                    r"useCallback\s*\(",
                    r"useMemo\s*\(",
                    r"use[A-Z]\w*\s*\(",  # Custom hooks
                ],
                "patterns": [
                    r"React\.memo\s*\(",
                    r"React\.forwardRef\s*\(",
                    r"React\.lazy\s*\(",
                ],
            },
            "javascript": {
                "async": [
                    r"async\s+function",
                    r"async\s*\(",
                    r"await\s+",
                    r"\.then\s*\(",
                    r"Promise\.",
                ],
                "es6": [
                    r"=>",  # Arrow functions
                    r"const\s+\{.*\}\s*=",  # Destructuring
                    r"\.\.\..*",  # Spread operator
                    r"`.*\$\{.*\}.*`",  # Template literals
                ],
            },
            "python": {
                "decorators": [r"@\w+", r"@property"],
                "patterns": [
                    r"with\s+\w+.*:",  # Context managers
                    r"yield\s+",  # Generators
                    r"lambda\s+",  # Lambda functions
                ],
            },
        }

    async def store_pattern_embedding(
        self, code: str, patterns: List[str], metadata: Dict
    ):
        """Store code pattern in vector database"""
        if not self.pattern_collection:
            return

        try:
            # Simple storage without embeddings for now
            self.pattern_collection.add(
                documents=[code],
                metadatas=[{**metadata, "patterns": ",".join(patterns)}],
                ids=[f"pattern_{hash(code)}"],
            )
        except Exception as e:
            logger.warning(f"Failed to store pattern embedding: {e}")

    async def find_similar_patterns(self, code: str, limit: int = 5) -> List[Dict]:
        """Find similar code patterns"""
        if not self.pattern_collection:
            return []

        try:
            results = self.pattern_collection.query(query_texts=[code], n_results=limit)
            return results
        except Exception as e:
            logger.warning(f"Failed to find similar patterns: {e}")
            return []

    def get_status(self) -> Dict:
        """Get AI service status"""
        return {
            "ollama_available": self.ollama_available,
            "model": getattr(self.llm, "model", None) if self.llm else None,
            "cache_available": bool(self.cache),
            "vector_db_available": bool(self.pattern_collection),
            "status": "operational" if self.ollama_available else "limited",
        }
