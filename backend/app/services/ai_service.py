import json
import logging
import re
import asyncio
import datetime
from typing import Any, Dict, List, Optional

try:
    from langchain_ollama import OllamaLLM, OllamaEmbeddings
except Exception:
    # Optional dependency: allow the app to start even when langchain_ollama
    # is not installed (docker/dev environments may not include it).
    OllamaLLM = None
    OllamaEmbeddings = None
from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.chains import LLMChain
from pydantic import BaseModel, Field

from app.core.database import get_enhanced_database_manager, get_collection
from app.core.service_manager import (
    get_security_analyzer,
    get_architectural_analyzer,
    get_performance_analyzer,
)
from app.services.cache_service import cache_analysis_result

logger = logging.getLogger(__name__)


class PatternAnalysis(BaseModel):
    patterns: List[str] = Field(description="List of detected pattern names")
    complexity_score: float = Field(description="Complexity score from 1-10")
    evolution_stage: str = Field(
        description="Developer skill level: beginner, intermediate, advanced"
    )
    suggestions: List[str] = Field(description="Improvement suggestions")


class CodeQualityAnalysis(BaseModel):
    quality_score: float = Field(description="Overall quality score 1-100")
    readability: str = Field(description="Code readability assessment")
    issues: List[str] = Field(description="Identified issues")
    improvements: List[str] = Field(description="Suggested improvements")


class EvolutionAnalysis(BaseModel):
    complexity_change: str = Field(
        description="How complexity changed: increased, decreased, stable"
    )
    new_patterns: List[str] = Field(description="New patterns in recent code")
    improvements: List[str] = Field(description="Improvements observed")
    learning_insights: str = Field(
        description="What this evolution suggests about learning"
    )


class AIService:
    def _get_openai_token_param(self, model_name: str, value: int) -> dict:
        """
        Utility to select correct token parameter for OpenAI models.
        Uses 'max_completion_tokens' for new models, 'max_tokens' for legacy models.
        Includes robust error handling and logging.
        """
        try:
            # New models require 'max_completion_tokens', legacy use 'max_tokens'
            if any(
                s in model_name
                for s in [
                    "gpt-4-1106",
                    "gpt-4-vision",
                    "gpt-4o",
                    "gpt-3.5-turbo-1106",
                    "o3-mini",
                    "o4-mini",
                ]
            ):
                logger.debug(f"Using 'max_completion_tokens' for model {model_name}")
                return {"max_completion_tokens": value}
            else:
                logger.debug(f"Using 'max_tokens' for model {model_name}")
                return {"max_tokens": value}
        except Exception as e:
            logger.error(
                f"Error determining OpenAI token param for model {model_name}: {e}"
            )
            return {"max_tokens": value}

    """Enhanced AI service with robust pattern analysis and embeddings"""

    def __init__(self):
        # Use Any to avoid referring to optional types at import-time
        self.llm: Any = None
        self.embeddings: Any = None
        self.collection = None
        self.ollama_available: bool = False
        self.security_analyzer = get_security_analyzer()
        self.architectural_analyzer = get_architectural_analyzer()
        self.performance_analyzer = get_performance_analyzer()
        self.ensemble = None  # Initialize after services are ready

        # Model selection support
        self.preferred_model: Optional[str] = None
        self.multi_model_service = None

        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize AI services with fallback handling"""
        try:
            # Initialize Ollama LLM only if the optional package is available
            if OllamaLLM is not None:
                try:
                    self.llm = OllamaLLM(model="codellama:7b", temperature=0.1)
                    # Quick smoke test - non-fatal if it fails
                    try:
                        self.llm.invoke("test")
                        self.ollama_available = True
                        logger.info("Ollama LLM initialized successfully")
                    except Exception as invoke_err:
                        logger.warning(
                            f"Ollama LLM initialized but test invoke failed: {invoke_err}"
                        )
                        # keep llm instance but mark availability based on test
                except Exception as init_err:
                    logger.warning(
                        f"Ollama LLM not available (init failed): {init_err}"
                    )
                    self.llm = None
                    self.ollama_available = False
            else:
                logger.info(
                    "langchain_ollama not installed; skipping Ollama LLM initialization"
                )
                self.llm = None
                self.ollama_available = False

            # Initialize embeddings only if available
            if OllamaEmbeddings is not None:
                try:
                    self.embeddings = OllamaEmbeddings(
                        model="nomic-embed-text", base_url="http://localhost:11434"
                    )
                    try:
                        self.embeddings.embed_query("test")
                        logger.info("Ollama embeddings initialized successfully")
                    except Exception as embed_invoke_err:
                        logger.warning(
                            f"Ollama embeddings created but test failed: {embed_invoke_err}"
                        )
                except Exception as emb_err:
                    logger.warning(f"Embeddings not available: {emb_err}")
                    self.embeddings = None
            else:
                self.embeddings = None

            self.collection = get_collection("code_patterns")
            if self.collection:
                logger.info("ChromaDB collection initialized")

            # Initialize AI ensemble after services are ready
            from app.core.service_manager import get_ai_ensemble

            self.ensemble = get_ai_ensemble(self)
            logger.info("AI Ensemble initialized")

            # Initialize multi-model service for model selection
            from app.services.multi_model_ai_service import MultiModelAIService

            self.multi_model_service = MultiModelAIService()
            logger.info("Multi-model AI service initialized")

        except Exception as e:
            logger.error(f"Error initializing AI services: {e}")
            self.ollama_available = False

    def _get_timestamp(self) -> str:
        """Get current timestamp - utility method to avoid import issues"""
        return datetime.datetime.utcnow().isoformat()

    def set_preferred_model(self, model_id: str) -> None:
        """Set the preferred model for AI analysis"""
        self.preferred_model = model_id
        logger.info(f"🤖 Set preferred model to: {model_id}")

        # Validate model is available
        if self.multi_model_service:
            available_models = self.multi_model_service.get_available_models()
            if model_id not in available_models:
                logger.warning(
                    f"⚠️  Model {model_id} not available. Available models: {list(available_models.keys())}"
                )
            else:
                logger.info(f"✅ Model {model_id} is available and selected")

    def get_status(self) -> Dict[str, Any]:
        """Get AI service status"""
        logger.info(f"Fetching AI service status: {self}")
        status = {
            "ollama_available": self.ollama_available,
            "ollama_model": "codellama:7b" if self.ollama_available else None,
            "embeddings_available": self.embeddings is not None,
            "embeddings_model": "nomic-embed-text" if self.embeddings else None,
            "vector_db_available": self.collection is not None,
            "preferred_model": self.preferred_model,
            "multi_model_service_available": self.multi_model_service is not None,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }

        # Add available models info
        if self.multi_model_service:
            available_models = self.multi_model_service.get_available_models()
            status["available_models_count"] = len(available_models)
            status["openai_models_available"] = any(
                "gpt" in model for model in available_models.keys()
            )

        return status

    @cache_analysis_result("pattern", ttl_seconds=3600)  # 1 hour cache
    async def analyze_code_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """
        Analyze code for patterns with enhanced AI understanding
        Fix #7: Use AI for dynamic pattern complexity and skill assessment
        """
        detected_patterns = self._detect_patterns_simple(code, language)

        # Use selected model if available via multi-model service
        if self.preferred_model and self.multi_model_service:
            try:
                from app.services.multi_model_ai_service import AIModel

                model_enum = AIModel(self.preferred_model)

                logger.info(
                    f"🤖 Using selected model {self.preferred_model} for pattern analysis"
                )
                # Patch: Pass correct token param for OpenAI models
                token_param = self._get_openai_token_param(self.preferred_model, 2048)
                result = await self.multi_model_service.analyze_with_model(
                    code, language, model_enum, **token_param
                )

                return {
                    "detected_patterns": detected_patterns,
                    "ai_patterns": result.patterns,
                    "combined_patterns": list(set(detected_patterns + result.patterns)),
                    "complexity_score": result.complexity_score,
                    "skill_level": result.skill_level,
                    "suggestions": result.suggestions,
                    "ai_powered": True,
                    "model_used": self.preferred_model,
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "token_usage": result.token_usage,
                }

            except Exception as e:
                logger.error(
                    f"Selected model {self.preferred_model} analysis failed: {e}"
                )
                # Fall back to default analysis

        # Fallback to Ollama if available
        if self.ollama_available:
            try:
                parser = PydanticOutputParser(pydantic_object=PatternAnalysis)
                fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=self.llm)

                prompt = PromptTemplate(
                    input_variables=[
                        "code",
                        "language",
                        "simple_patterns",
                        "format_instructions",
                    ],
                    template=(
                        "Analyze this {language} code for patterns and complexity.\n\n"
                        "Code:\n```{language}\n{code}\n```\n"
                        "Initially detected patterns: {simple_patterns}\n\n"
                        "IMPORTANT: Respond ONLY with valid JSON matching this exact format. Do not include any explanations or additional text.\n\n"
                        "{format_instructions}\n\n"
                        "Return only the JSON object with:\n"
                        "- patterns: array of pattern names\n"
                        "- complexity_score: number 1-10\n"
                        "- evolution_stage: one of 'beginner', 'intermediate', 'advanced'\n"
                        "- suggestions: array of improvement suggestions"
                    ),
                )

                # Use RunnableSequence for prompt | llm | output_parser
                chain = prompt | self.llm | parser
                # run in executor to avoid blocking
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chain.invoke(
                        {
                            "code": code[:1500],
                            "language": language,
                            "simple_patterns": ", ".join(detected_patterns),
                            "format_instructions": parser.get_format_instructions(),
                        }
                    ),
                )

                # Try to extract JSON from the response
                ai_analysis = self._parse_llm_response(result, parser, fixing_parser)

                if ai_analysis:
                    if self.embeddings and self.collection:
                        await self.store_pattern_embedding(
                            code,
                            ai_analysis.patterns,
                            {
                                "language": language,
                                "complexity": ai_analysis.complexity_score,
                                "skill_level": ai_analysis.evolution_stage,
                            },
                        )

                    return {
                        "detected_patterns": detected_patterns,
                        "ai_patterns": ai_analysis.patterns,
                        "combined_patterns": list(
                            set(detected_patterns + ai_analysis.patterns)
                        ),
                        "complexity_score": ai_analysis.complexity_score,
                        "skill_level": ai_analysis.evolution_stage,
                        "suggestions": ai_analysis.suggestions,
                        "ai_powered": True,
                    }

            except Exception as e:
                logger.error(f"AI analysis error: {e}")

        # Enhanced fallback analysis
        return self._enhanced_simple_analysis(code, detected_patterns, language)

    def _parse_llm_response(
        self, result: str, parser, fixing_parser
    ) -> Optional[PatternAnalysis]:
        """Extract and parse JSON from LLM response"""
        try:
            # First try direct parsing
            return fixing_parser.parse(result)
        except Exception as e1:
            logger.debug(f"Direct parsing failed: {e1}")

            # Try to extract JSON from text
            import json
            import re

            try:
                # Look for JSON object in the text
                json_match = re.search(r"\{.*\}", result, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    data = json.loads(json_str)

                    # Create PatternAnalysis object from dict
                    return PatternAnalysis(
                        patterns=data.get("patterns", []),
                        complexity_score=data.get("complexity_score", 5.0),
                        evolution_stage=data.get("evolution_stage", "intermediate"),
                        suggestions=data.get("suggestions", []),
                    )
            except Exception as e2:
                logger.debug(f"JSON extraction failed: {e2}")

            # Final fallback - create from partial data
            try:
                return PatternAnalysis(
                    patterns=["basic_patterns"],
                    complexity_score=5.0,
                    evolution_stage="intermediate",
                    suggestions=["Enable proper AI analysis for detailed insights"],
                )
            except Exception as e3:
                logger.warning(f"Fallback parsing failed: {e3}")
                return None

    @cache_analysis_result("quality", ttl_seconds=3600)  # 1 hour cache
    async def analyze_code_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality with detailed insights"""

        # Use selected model if available via multi-model service
        if self.preferred_model and self.multi_model_service:
            try:
                from app.services.multi_model_ai_service import AIModel

                model_enum = AIModel(self.preferred_model)

                logger.info(
                    f"🤖 Using selected model {self.preferred_model} for quality analysis"
                )
                # Patch: Pass correct token param for OpenAI models
                token_param = self._get_openai_token_param(self.preferred_model, 2048)
                result = await self.multi_model_service.analyze_with_model(
                    code, language, model_enum, **token_param
                )

                # Convert to quality analysis format
                return {
                    "quality_score": min(
                        100, result.complexity_score * 10
                    ),  # Scale to 100
                    "readability": result.skill_level.capitalize(),
                    "issues": [f"Complexity: {result.complexity_score}/10"],
                    "improvements": result.suggestions,
                    "ai_powered": True,
                    "model_used": self.preferred_model,
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "token_usage": result.token_usage,
                }

            except Exception as e:
                logger.error(
                    f"Selected model {self.preferred_model} quality analysis failed: {e}"
                )
                # Fall back to default analysis

        # Fallback to Ollama if available
        if self.ollama_available:
            try:
                parser = PydanticOutputParser(pydantic_object=CodeQualityAnalysis)
                fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=self.llm)

                prompt = PromptTemplate(
                    input_variables=["code", "language", "format_instructions"],
                    template=(
                        "Analyze the quality of this {language} code.\n"
                        "{code}\n\n"
                        "IMPORTANT: Respond ONLY with valid JSON matching this exact format. Do not include any explanations or additional text.\n\n"
                        "{format_instructions}\n\n"
                        "Return only the JSON object with:\n"
                        "- quality_score: number 1-100\n"
                        "- readability: string assessment\n"
                        "- issues: array of strings describing issues\n"
                        "- improvements: array of strings with suggestions"
                    ),
                )

                chain = prompt | self.llm | parser
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chain.invoke(
                        {
                            "code": code[:1500],
                            "language": language,
                            "format_instructions": parser.get_format_instructions(),
                        }
                    ),
                )

                # Try to parse the response with robust error handling
                quality_analysis = self._parse_quality_response(
                    result, parser, fixing_parser
                )

                if quality_analysis:
                    return {
                        "quality_score": quality_analysis.quality_score,
                        "readability": quality_analysis.readability,
                        "issues": quality_analysis.issues,
                        "improvements": quality_analysis.improvements,
                        "ai_powered": True,
                    }

            except Exception as e:
                logger.error(f"Quality analysis error: {e}")

        return self._enhanced_quality_analysis(code, language)

    def _parse_quality_response(
        self, result: str, parser, fixing_parser
    ) -> Optional[CodeQualityAnalysis]:
        """Extract and parse quality analysis JSON from LLM response"""
        try:
            # First try direct parsing
            return fixing_parser.parse(result)
        except Exception as e1:
            logger.debug(f"Direct quality parsing failed: {e1}")

            # Try to extract JSON from text
            import json
            import re

            try:
                # Look for JSON object in the text
                json_match = re.search(r"\{.*\}", result, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    data = json.loads(json_str)

                    # Create CodeQualityAnalysis object from dict
                    return CodeQualityAnalysis(
                        quality_score=float(data.get("quality_score", 80)),
                        readability=data.get("readability", "Good"),
                        issues=data.get("issues", []),
                        improvements=data.get("improvements", []),
                    )
            except Exception as e2:
                logger.debug(f"Quality JSON extraction failed: {e2}")

            # Final fallback
            try:
                return CodeQualityAnalysis(
                    quality_score=80.0,
                    readability="Fair",
                    issues=["Enable proper AI analysis for detailed assessment"],
                    improvements=[
                        "Configure Ollama for comprehensive code quality insights"
                    ],
                )
            except Exception as e3:
                logger.warning(f"Quality fallback parsing failed: {e3}")
                return None

    async def analyze_evolution(
        self, old_code: str, new_code: str, context: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze the evolution between two code versions
        """
        if self.ollama_available:
            try:
                from langchain.output_parsers import (
                    PydanticOutputParser,
                    OutputFixingParser,
                )

                parser = PydanticOutputParser(pydantic_object=EvolutionAnalysis)
                fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=self.llm)

                prompt = PromptTemplate(
                    input_variables=[
                        "old_code",
                        "new_code",
                        "context",
                        "format_instructions",
                    ],
                    template=(
                        "Compare these two code versions and analyze the evolution:\n\n"
                        "OLD CODE:\n```\n{old_code}\n```\n\n"
                        "NEW CODE:\n```\n{new_code}\n```\n\n"
                        "Context: {context}\n\n"
                        "Analyze the evolution and provide your response in the EXACT JSON format specified below:\n"
                        "- complexity_change: Use ONLY 'increased', 'decreased', or 'stable'\n"
                        "- new_patterns: List of specific pattern names (e.g., ['Observer Pattern', 'Factory Method'])\n"
                        "- improvements: List of specific improvements observed (e.g., ['Better error handling', 'Cleaner code structure'])\n"
                        "- learning_insights: Single string describing what this suggests about developer learning\n\n"
                        "IMPORTANT: Respond with ONLY the JSON data, no explanations, no schema definitions, no markdown formatting.\n"
                        "Do NOT include field descriptions or type information in your response.\n\n"
                        "{format_instructions}\n\n"
                        "Example response:\n"
                        "{{\n"
                        '  "complexity_change": "decreased",\n'
                        '  "new_patterns": ["Error Handling Pattern", "Input Validation"],\n'
                        '  "improvements": ["Better error messages", "More robust validation"],\n'
                        '  "learning_insights": "Developer is showing improved defensive programming practices"\n'
                        "}}"
                    ),
                )

                chain = LLMChain(llm=self.llm, prompt=prompt)

                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chain.run(
                        old_code=old_code[:1000],
                        new_code=new_code[:1000],
                        context=context,
                        format_instructions=parser.get_format_instructions(),
                    ),
                )

                logger.debug(f"Raw evolution analysis result: {result}")

                # Check if result looks like a schema instead of data
                if (
                    "properties" in result.lower()
                    or "type" in result.lower()
                    and "object" in result.lower()
                ):
                    logger.warning(
                        "AI returned schema definition instead of data, using fallback"
                    )
                    raise ValueError(
                        "Invalid response format - schema returned instead of data"
                    )

                try:
                    evolution_analysis = fixing_parser.parse(result)
                except Exception as parse_error:
                    logger.error(f"Failed to parse evolution analysis: {parse_error}")
                    logger.debug(f"Raw result that failed parsing: {result}")
                    # Try basic fallback parsing
                    try:
                        # Try to extract JSON if present
                        import re

                        json_match = re.search(r"\{.*\}", result, re.DOTALL)
                        if json_match:
                            json_str = json_match.group()
                            data = json.loads(json_str)
                            evolution_analysis = EvolutionAnalysis(**data)
                        else:
                            raise parse_error
                    except Exception:
                        # Complete fallback
                        evolution_analysis = EvolutionAnalysis(
                            complexity_change="stable",
                            new_patterns=[],
                            improvements=["Analysis unavailable due to parsing error"],
                            learning_insights="Unable to analyze evolution due to AI response format",
                        )

                return {
                    "complexity_change": evolution_analysis.complexity_change,
                    "new_patterns": evolution_analysis.new_patterns,
                    "improvements": evolution_analysis.improvements,
                    "learning_insights": evolution_analysis.learning_insights,
                    "ai_powered": True,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(f"Evolution analysis error: {e}")
                logger.debug(f"Full error details: {e.__class__.__name__}: {str(e)}")

        # Enhanced fallback analysis
        return {
            "complexity_change": "stable",
            "new_patterns": [],
            "improvements": ["Code structure maintained"],
            "learning_insights": "Enable Ollama for detailed evolution analysis",
            "ai_powered": False,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }

    async def generate_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate comprehensive insights based on patterns, technologies, and AI analysis.
        """
        insights: List[Dict[str, Any]] = []

        # Extract data from analysis
        patterns = analysis_data.get("patterns", {})
        technologies = analysis_data.get("technologies", [])
        commits = analysis_data.get("commits", 0)

        # 1. Pattern Analysis Insights
        if patterns:
            pattern_insights = self._analyze_patterns(patterns)
            insights.extend(pattern_insights)

        # 2. Technology Stack Insights
        if technologies:
            tech_insights = self._analyze_technology_stack(technologies)
            insights.extend(tech_insights)

        # 3. Code Quality Insights
        quality_insights = self._analyze_code_quality(patterns, commits)
        insights.extend(quality_insights)

        # 4. Architecture Insights
        arch_insights = self._analyze_architecture(patterns, technologies)
        insights.extend(arch_insights)

        # 5. Evolution Insights
        if commits > 0:
            evolution_insights = self._analyze_evolution(patterns, commits)
            insights.extend(evolution_insights)

        # 6. AI-Powered Recommendations (if LLM available)
        if self.ollama_available and self.llm:
            try:
                ai_insights = await self._generate_ai_recommendations(analysis_data)
                insights.extend(ai_insights)
            except Exception as e:
                logger.warning(f"Failed to generate AI recommendations: {e}")

        return insights

    def _analyze_patterns(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze pattern usage and generate insights."""
        insights = []

        # Pattern complexity analysis
        complex_patterns = []
        simple_patterns = []
        antipatterns = []

        for pattern_name, pattern_data in patterns.items():
            if isinstance(pattern_data, dict):
                complexity = pattern_data.get("complexity_level", "intermediate")
                is_antipattern = pattern_data.get("is_antipattern", False)
                occurrences = pattern_data.get("occurrences", 0)

                if is_antipattern:
                    antipatterns.append((pattern_name, occurrences))
                elif complexity == "advanced":
                    complex_patterns.append((pattern_name, occurrences))
                elif complexity == "simple":
                    simple_patterns.append((pattern_name, occurrences))

        # Generate pattern-based insights
        if complex_patterns:
            insights.append(
                {
                    "type": "achievement",
                    "title": "Advanced Pattern Mastery",
                    "description": f"Your codebase demonstrates mastery of {len(complex_patterns)} advanced patterns, showing sophisticated architectural thinking.",
                    "data": {
                        "patterns": dict(complex_patterns),
                        "complexity": "advanced",
                    },
                }
            )

        if antipatterns:
            total_antipattern_occurrences = sum(count for _, count in antipatterns)
            insights.append(
                {
                    "type": "warning",
                    "title": "Code Quality Concerns",
                    "description": f"Detected {len(antipatterns)} anti-patterns with {total_antipattern_occurrences} total occurrences. Consider refactoring these areas.",
                    "data": {"antipatterns": dict(antipatterns), "priority": "high"},
                }
            )

        if len(patterns) > 15:
            insights.append(
                {
                    "type": "trend",
                    "title": "Rich Pattern Ecosystem",
                    "description": f"Your project uses {len(patterns)} different patterns, indicating a mature and well-structured codebase.",
                    "data": {
                        "pattern_count": len(patterns),
                        "diversity_score": min(100, len(patterns) * 5),
                    },
                }
            )

        return insights

    def _analyze_technology_stack(
        self, technologies: List[str]
    ) -> List[Dict[str, Any]]:
        """Analyze technology choices and generate insights."""
        insights = []

        tech_count = len(technologies)

        if tech_count > 10:
            insights.append(
                {
                    "type": "trend",
                    "title": "Diverse Technology Portfolio",
                    "description": f"Your project leverages {tech_count} technologies, demonstrating a modern, polyglot approach to development.",
                    "data": {
                        "technologies": technologies,
                        "diversity_score": min(100, tech_count * 8),
                    },
                }
            )
        elif tech_count > 5:
            insights.append(
                {
                    "type": "recommendation",
                    "title": "Balanced Technology Stack",
                    "description": f"Good balance with {tech_count} core technologies. Consider whether all are necessary for maintenance overhead.",
                    "data": {"technologies": technologies, "balance_score": 75},
                }
            )
        else:
            insights.append(
                {
                    "type": "recommendation",
                    "title": "Focused Technology Approach",
                    "description": f"Minimal tech stack with {tech_count} technologies. This can improve maintainability but may limit capabilities.",
                    "data": {"technologies": technologies, "focus_score": 85},
                }
            )

        return insights

    def _analyze_code_quality(
        self, patterns: Dict[str, Any], commits: int
    ) -> List[Dict[str, Any]]:
        """Generate code quality insights."""
        insights = []

        # Calculate quality metrics
        total_patterns = len(patterns)
        antipattern_count = sum(
            1
            for p in patterns.values()
            if isinstance(p, dict) and p.get("is_antipattern", False)
        )

        quality_score = max(0, 100 - (antipattern_count * 15))

        if quality_score >= 80:
            insights.append(
                {
                    "type": "achievement",
                    "title": "High Code Quality",
                    "description": f"Excellent code quality score of {quality_score}% with minimal anti-patterns detected.",
                    "data": {"score": quality_score, "antipatterns": antipattern_count},
                }
            )
        elif quality_score >= 60:
            insights.append(
                {
                    "type": "recommendation",
                    "title": "Good Code Quality",
                    "description": f"Solid code quality score of {quality_score}%. Focus on reducing the {antipattern_count} anti-patterns for improvement.",
                    "data": {"score": quality_score, "antipatterns": antipattern_count},
                }
            )
        else:
            insights.append(
                {
                    "type": "warning",
                    "title": "Code Quality Needs Attention",
                    "description": f"Code quality score of {quality_score}% indicates {antipattern_count} anti-patterns requiring immediate attention.",
                    "data": {
                        "score": quality_score,
                        "antipatterns": antipattern_count,
                        "priority": "high",
                    },
                }
            )

        return insights

    def _analyze_architecture(
        self, patterns: Dict[str, Any], technologies: List[str]
    ) -> List[Dict[str, Any]]:
        """Analyze architectural patterns and structure."""
        insights = []

        # Look for architectural indicators
        arch_patterns = []
        for pattern_name in patterns.keys():
            pattern_lower = pattern_name.lower()
            if any(
                arch in pattern_lower
                for arch in ["mvc", "mvp", "mvvm", "facade", "adapter", "strategy"]
            ):
                arch_patterns.append(pattern_name)

        if arch_patterns:
            insights.append(
                {
                    "type": "achievement",
                    "title": "Strong Architectural Foundation",
                    "description": f"Detected {len(arch_patterns)} architectural patterns: {', '.join(arch_patterns[:3])}{'...' if len(arch_patterns) > 3 else ''}",
                    "data": {"architectural_patterns": arch_patterns},
                }
            )

        # Analyze technology coherence
        if len(technologies) > 8:
            insights.append(
                {
                    "type": "recommendation",
                    "title": "Architecture Complexity Review",
                    "description": "Consider reviewing architecture complexity as the diverse tech stack may impact maintainability.",
                    "data": {
                        "tech_count": len(technologies),
                        "suggestion": "consolidation_review",
                    },
                }
            )

        return insights

    def _analyze_evolution(
        self, patterns: Dict[str, Any], commits: int
    ) -> List[Dict[str, Any]]:
        """Analyze code evolution insights."""
        insights = []

        patterns_per_commit = len(patterns) / max(commits, 1)

        if patterns_per_commit > 0.5:
            insights.append(
                {
                    "type": "trend",
                    "title": "Rapid Pattern Evolution",
                    "description": f"High pattern density with {len(patterns)} patterns across {commits} commits, indicating active architectural development.",
                    "data": {
                        "pattern_density": patterns_per_commit,
                        "evolution_rate": "high",
                    },
                }
            )
        elif patterns_per_commit > 0.2:
            insights.append(
                {
                    "type": "trend",
                    "title": "Steady Architectural Growth",
                    "description": f"Consistent pattern introduction with {len(patterns)} patterns over {commits} commits shows steady evolution.",
                    "data": {
                        "pattern_density": patterns_per_commit,
                        "evolution_rate": "steady",
                    },
                }
            )

        return insights

    async def _generate_ai_recommendations(
        self, analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered recommendations using LLM."""
        if not self.llm:
            return []

        try:
            # Prepare context for AI analysis
            patterns = analysis_data.get("patterns", {})
            technologies = analysis_data.get("technologies", [])
            commits = analysis_data.get("commits", 0)

            context = f"""
            Code Analysis Summary:
            - Total Patterns: {len(patterns)}
            - Technologies: {', '.join(technologies[:10])}
            - Commits Analyzed: {commits}
            - Top Patterns: {', '.join(list(patterns.keys())[:5])}
            
            Please provide 2-3 specific, actionable recommendations for improving this codebase.
            Focus on architecture, maintainability, and best practices.
            """

            # Generate AI recommendations
            response = await self.llm.ainvoke(context)

            if response and hasattr(response, "content"):
                recommendation_text = response.content

                return [
                    {
                        "type": "ai_analysis",
                        "title": "AI-Powered Code Recommendations",
                        "description": (
                            recommendation_text[:200] + "..."
                            if len(recommendation_text) > 200
                            else recommendation_text
                        ),
                        "data": {
                            "full_analysis": recommendation_text,
                            "source": "ai_llm",
                            "confidence": 0.8,
                        },
                    }
                ]

        except Exception as e:
            logger.error(f"Failed to generate AI recommendations: {e}")

        return []

    async def store_pattern_embedding(
        self, code: str, patterns: List[str], metadata: Dict[str, Any]
    ) -> None:
        """
        Fix #6: Actually store embeddings for similarity search
        """
        if not self.embeddings or not self.collection:
            logger.warning("Embeddings or collection not available")
            return

        try:
            embedding = self.embeddings.embed_query(code[:1000])
            metadata.update(
                {
                    "patterns": json.dumps(patterns),
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "code_preview": code[:200],
                }
            )

            self.collection.add(
                embeddings=[embedding],
                documents=[code[:1000]],
                metadatas=[metadata],
                ids=[f"code_{datetime.datetime.utcnow().timestamp()}_{hash(code)}"],
            )

            logger.info(f"✅ Stored embedding for {len(patterns)} patterns")

        except Exception as e:
            logger.error(f"Error storing embedding: {e}")

    async def find_similar_patterns(
        self, code: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fix #6: Implement actual similarity search
        """
        if not self.embeddings or not self.collection:
            return []

        try:
            query_embedding = self.embeddings.embed_query(code[:1000])
            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=limit
            )

            similar_patterns: List[Dict[str, Any]] = []
            metadatas = results.get("metadatas", [])
            distances = results.get("distances", [])
            if metadatas and distances:
                for metadata, distance in zip(metadatas[0], distances[0]):
                    similar_patterns.append(
                        {
                            "patterns": json.loads(metadata.get("patterns", "[]")),
                            "similarity_score": 1 - distance,
                            "language": metadata.get("language", "unknown"),
                            "complexity": metadata.get("complexity", 0),
                            "code_preview": metadata.get("code_preview", ""),
                        }
                    )
            return similar_patterns

        except Exception as e:
            logger.error(f"Similarity search error: {e}")
            return []

    def _detect_patterns_simple(self, code: str, language: str) -> List[str]:
        """Enhanced pattern detection with comprehensive rule-based analysis"""
        patterns: List[str] = []
        logger.debug(f"Analyzing {len(code)} chars of {language} code")
        css_patterns_to_exclude = {
            "justify-center",
            "whitespace-nowrap",
            "font-medium",
            "rounded-md",
            "focus-visible:outline-none",
            "inline-flex",
            "text-sm",
            "items-center",
            "transition-colors",
            "disabled:opacity-50",
            "gap-2",
            "focus-visible:ring-1",
            "[&_svg]:size-4",
            "[&_svg]:shrink-0",
            "[&_svg]:pointer-events-none",
            "focus-visible:ring-ring",
            "disabled:pointer-events-none",
            "text-xs",
            "focus-visible",
            "outline-none",
            "ring-2",
            "ring-ring",
            "ring-offset-2",
            "pointer-events-none",
            "opacity-50",
            "size-4",
            "shrink-0",
        }

        code_lower = code.lower()

        # JavaScript/TypeScript patterns
        if language.lower() in ["javascript", "typescript"]:
            if "async" in code_lower and "await" in code_lower:
                patterns.append("async_await_pattern")
            if "promise" in code_lower:
                patterns.append("promise_pattern")
            if ".then(" in code_lower:
                patterns.append("promise_chaining")
            if "usestate" in code_lower:
                patterns.append("react_hooks")
            if "useeffect" in code_lower:
                patterns.append("react_effects")
            if "function*" in code_lower:
                patterns.append("generator_pattern")
            if "class " in code_lower:
                patterns.append("class_pattern")
            if "=>" in code:
                patterns.append("arrow_functions")
            if "try" in code_lower and "catch" in code_lower:
                patterns.append("error_handling")
            if "fetch(" in code_lower or "axios" in code_lower:
                patterns.append("api_integration")
            if "map(" in code_lower or "filter(" in code_lower:
                patterns.append("functional_programming")

        # Python patterns
        elif language.lower() == "python":
            if "def " in code_lower:
                patterns.append("function_definition")
            if "class " in code_lower:
                patterns.append("class_definition")
            if "async def" in code_lower:
                patterns.append("async_functions")
            if "with " in code_lower:
                patterns.append("context_manager")
            if "try:" in code_lower and "except" in code_lower:
                patterns.append("exception_handling")
            if "[" in code and "for" in code_lower and "in" in code_lower:
                patterns.append("list_comprehension")
            if "@" in code:
                patterns.append("decorators")
            if "yield" in code_lower:
                patterns.append("generator_pattern")
            if "__init__" in code_lower:
                patterns.append("constructor_pattern")
            if "import " in code_lower:
                patterns.append("module_imports")

        # Rust patterns
        elif language.lower() == "rust":
            if "fn " in code_lower:
                patterns.append("function_definition")
            if "struct " in code_lower:
                patterns.append("struct_definition")
            if "enum " in code_lower:
                patterns.append("enum_definition")
            if "impl " in code_lower:
                patterns.append("implementation_block")
            if "trait " in code_lower:
                patterns.append("trait_definition")
            if "match " in code_lower:
                patterns.append("pattern_matching")
            if "if let" in code_lower:
                patterns.append("conditional_binding")
            if "unwrap()" in code_lower:
                patterns.append("unwrap_pattern")
            if "?" in code and "result" in code_lower:
                patterns.append("error_propagation")
            if "async fn" in code_lower:
                patterns.append("async_functions")
            if ".await" in code_lower:
                patterns.append("await_pattern")
            if "use " in code_lower:
                patterns.append("module_imports")
            if "mut " in code_lower:
                patterns.append("mutable_binding")
            if "&" in code and ("ref" in code_lower or "borrow" in code_lower):
                patterns.append("borrowing_pattern")
            if "clone()" in code_lower:
                patterns.append("clone_pattern")
            if "box<" in code_lower or "rc<" in code_lower or "arc<" in code_lower:
                patterns.append("smart_pointers")
            if "lifetime" in code_lower or "'" in code:
                patterns.append("lifetime_annotations")
            if "unsafe" in code_lower:
                patterns.append("unsafe_code")
            if "macro_rules!" in code_lower:
                patterns.append("macro_definition")
            if "vec![" in code_lower:
                patterns.append("vector_initialization")
            if (
                ".iter()" in code_lower
                or ".map(" in code_lower
                or ".filter(" in code_lower
            ):
                patterns.append("iterator_pattern")
            if "thread::" in code_lower or "spawn(" in code_lower:
                patterns.append("concurrency_pattern")

        # General patterns (all languages)
        if "if " in code_lower:
            patterns.append("conditional_logic")
        if "for " in code_lower or "while " in code_lower:
            patterns.append("iteration_pattern")
        if "return " in code_lower:
            patterns.append("return_pattern")

        # Design patterns (based on naming and structure)
        if "factory" in code_lower:
            patterns.append("factory_pattern")
        if "singleton" in code_lower:
            patterns.append("singleton_pattern")
        if "observer" in code_lower:
            patterns.append("observer_pattern")
        if "strategy" in code_lower:
            patterns.append("strategy_pattern")

        # Code quality patterns
        if len(code.split("\n")) > 50:
            patterns.append("large_code_block")
        if code.count("function") > 5 or code.count("def ") > 5:
            patterns.append("multi_function_module")
        filtered_patterns = [p for p in patterns if p not in css_patterns_to_exclude]
        logger.info(f"Detected {len(patterns)} patterns: {patterns}")
        return list(set(filtered_patterns))  # Remove duplicates

    def _enhanced_simple_analysis(
        self, code: str, patterns: List[str], language: str
    ) -> Dict[str, Any]:
        """Enhanced fallback analysis when AI is not available"""

        # Calculate complexity based on code characteristics
        complexity_indicators = [
            len(patterns),  # Number of patterns
            code.count("if"),  # Conditional complexity
            code.count("for") + code.count("while"),  # Loop complexity
            code.count("function") + code.count("def"),  # Function count
            code.count("class"),  # Class usage
            len(code.split("\n")),  # Code length
        ]

        complexity_score = min(10.0, max(1.0, sum(complexity_indicators) / 10))

        # Determine skill level based on patterns and complexity
        advanced_patterns = [
            "async_await_pattern",
            "generator_pattern",
            "decorators",
            "context_manager",
        ]
        intermediate_patterns = ["class_pattern", "error_handling", "promise_pattern"]

        if any(p in patterns for p in advanced_patterns) or complexity_score > 7:
            skill_level = "advanced"
        elif any(p in patterns for p in intermediate_patterns) or complexity_score > 4:
            skill_level = "intermediate"
        else:
            skill_level = "beginner"

        # Generate suggestions based on analysis
        suggestions = []
        if complexity_score > 8:
            suggestions.append(
                "Consider breaking down complex functions into smaller, more manageable pieces"
            )
        if "error_handling" not in patterns:
            suggestions.append("Add error handling to improve code robustness")
        if (
            language.lower() in ["javascript", "typescript"]
            and "async_await_pattern" not in patterns
        ):
            suggestions.append(
                "Consider using async/await for better asynchronous code handling"
            )
        if len(patterns) < 3:
            suggestions.append(
                "Explore more programming patterns to improve code structure"
            )

        suggestions.append(
            "Enable Ollama for AI-powered detailed analysis and suggestions"
        )

        return {
            "detected_patterns": patterns,
            "ai_patterns": [],
            "combined_patterns": patterns,
            "complexity_score": complexity_score,
            "skill_level": skill_level,
            "suggestions": suggestions,
            "ai_powered": False,
            "model_used": "rule_based_fallback",
        }

    def _enhanced_quality_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Enhanced quality analysis fallback when AI is not available"""

        lines = code.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        # Calculate various quality metrics
        avg_line_length = sum(len(line) for line in non_empty_lines) / max(
            len(non_empty_lines), 1
        )
        long_lines = sum(1 for line in non_empty_lines if len(line) > 120)
        comment_lines = sum(
            1 for line in lines if line.strip().startswith(("#", "//", "/*", "*"))
        )
        comment_ratio = comment_lines / max(len(lines), 1)

        # Basic quality score calculation
        quality_score = 85  # Start with good base score

        # Deduct points for quality issues
        if avg_line_length > 100:
            quality_score -= 10
        if long_lines > len(non_empty_lines) * 0.3:
            quality_score -= 15
        if comment_ratio < 0.1:
            quality_score -= 10
        if len(non_empty_lines) > 200:
            quality_score -= 5  # Penalty for very long files

        quality_score = max(0, min(100, quality_score))

        # Determine readability
        if quality_score >= 85:
            readability = "Excellent"
        elif quality_score >= 70:
            readability = "Good"
        elif quality_score >= 55:
            readability = "Fair"
        else:
            readability = "Needs Improvement"

        # Generate issues based on analysis
        issues = []
        if avg_line_length > 100:
            issues.append("Lines are too long on average, consider shorter lines")
        if long_lines > 0:
            issues.append(f"{long_lines} lines exceed 120 characters")
        if comment_ratio < 0.1:
            issues.append("Low comment density, consider adding more documentation")
        if len(non_empty_lines) > 200:
            issues.append("Large file size, consider breaking into smaller modules")

        if not issues:
            issues.append("No major quality issues detected in basic analysis")

        # Generate improvements
        improvements = []
        if avg_line_length > 80:
            improvements.append("Break long lines for better readability")
        if comment_ratio < 0.2:
            improvements.append("Add more comments to explain complex logic")
        improvements.append("Use consistent formatting and naming conventions")
        improvements.append(
            "Enable Ollama for comprehensive AI-powered quality analysis"
        )

        return {
            "quality_score": quality_score,
            "readability": readability,
            "issues": issues,
            "improvements": improvements,
            "ai_powered": False,
            "model_used": "rule_based_fallback",
        }

    @cache_analysis_result(
        "security", ttl_seconds=1800
    )  # 30 minute cache (security is time-sensitive)
    async def analyze_security(
        self, code: str, file_path: str = "unknown", language: str = None
    ) -> Dict[str, Any]:
        """
        Analyze code for security vulnerabilities using comprehensive security patterns

        Args:
            code: Source code to analyze
            file_path: Path to the file being analyzed
            language: Programming language (auto-detected if None)

        Returns:
            Dict containing security analysis results
        """
        try:
            # Run security analysis
            # Handle both sync and async security analyzers
            if hasattr(self.security_analyzer, "analyze_code"):
                if asyncio.iscoroutinefunction(self.security_analyzer.analyze_code):
                    vulnerabilities = await self.security_analyzer.analyze_code(
                        code, file_path, language
                    )
                else:
                    vulnerabilities = self.security_analyzer.analyze_code(
                        code, file_path, language
                    )
            else:
                vulnerabilities = []

            # Generate comprehensive report
            security_report = self.security_analyzer.generate_security_report(
                vulnerabilities
            )

            # Add metadata
            security_report["analysis_metadata"] = {
                "analyzer_version": "1.0.0",
                "patterns_checked": len(self.security_analyzer.patterns),
                "file_path": file_path,
                "language": language
                or self.security_analyzer._detect_language(file_path),
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Security analysis completed: {len(vulnerabilities)} vulnerabilities found"
            )
            return security_report

        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return {
                "overall_score": 50,
                "risk_level": "unknown",
                "total_vulnerabilities": 0,
                "error": str(e),
                "recommendations": [
                    "Security analysis failed - manual review recommended"
                ],
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

    async def analyze_architecture(
        self, repository_path: str, file_list: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze repository architecture using comprehensive pattern detection

        Args:
            repository_path: Path to repository root
            file_list: Optional list of files to analyze

        Returns:
            Dict containing architectural analysis results
        """
        try:
            # Run architectural analysis
            analysis = self.architectural_analyzer.analyze_architecture(
                repository_path, file_list
            )

            # Generate comprehensive report
            architecture_report = (
                self.architectural_analyzer.generate_architecture_report(analysis)
            )

            # Add metadata
            architecture_report["analysis_metadata"] = {
                "analyzer_version": "1.0.0",
                "repository_path": repository_path,
                "files_analyzed": len(file_list) if file_list else 0,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Architecture analysis completed: {analysis.primary_style.value} style detected"
            )
            return architecture_report

        except Exception as e:
            logger.error(f"Architecture analysis failed: {e}")
            return {
                "architectural_style": {
                    "primary": "unknown",
                    "confidence": 0.0,
                    "description": "Architecture analysis failed",
                },
                "design_patterns": [],
                "quality_metrics": {
                    "overall_score": 50,
                    "modularity": 0.5,
                    "coupling": 0.5,
                    "cohesion": 0.5,
                    "complexity": 0.5,
                    "grade": "F",
                },
                "error": str(e),
                "recommendations": [
                    "Architecture analysis failed - manual review recommended"
                ],
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

    @cache_analysis_result("performance", ttl_seconds=1800)  # 30 minute cache
    async def analyze_performance(
        self, code: str, file_path: str = "unknown", language: str = None
    ) -> Dict[str, Any]:
        """
        Analyze code for performance issues and bottlenecks

        Args:
            code: Source code to analyze
            file_path: Path to the file being analyzed
            language: Programming language (auto-detected if None)

        Returns:
            Dict containing performance analysis results
        """
        try:
            # Run performance analysis
            # Handle both sync and async performance analyzers
            if hasattr(self.performance_analyzer, "analyze_performance"):
                if asyncio.iscoroutinefunction(
                    self.performance_analyzer.analyze_performance
                ):
                    issues = await self.performance_analyzer.analyze_performance(
                        code, file_path, language
                    )
                else:
                    issues = self.performance_analyzer.analyze_performance(
                        code, file_path, language
                    )
            else:
                issues = []

            # Calculate performance metrics
            metrics = self.performance_analyzer.calculate_performance_metrics(issues)

            # Generate comprehensive report
            performance_report = self.performance_analyzer.generate_performance_report(
                issues, metrics
            )

            # Add metadata
            performance_report["analysis_metadata"] = {
                "analyzer_version": "1.0.0",
                "patterns_checked": len(self.performance_analyzer.patterns),
                "file_path": file_path,
                "language": language
                or self.performance_analyzer._detect_language(file_path),
                "timestamp": self._get_timestamp(),
            }

            logger.info(f"Performance analysis completed: {len(issues)} issues found")
            return performance_report

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {
                "overall_score": 50,
                "performance_grade": "unknown",
                "total_issues": 0,
                "error": str(e),
                "optimizations": [
                    "Performance analysis failed - manual review recommended"
                ],
                "timestamp": self._get_timestamp(),
            }

    async def analyze_with_ensemble(
        self,
        analysis_type: str,
        code: str,
        language: str,
        file_path: str = "unknown",
        use_ensemble: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform analysis using AI ensemble for improved quality

        Args:
            analysis_type: Type of analysis ('pattern', 'quality', 'security', 'performance')
            code: Source code to analyze
            language: Programming language
            file_path: File path for context
            use_ensemble: Whether to use ensemble (fallback to single model if False)

        Returns:
            Analysis results with ensemble metadata
        """
        try:
            if use_ensemble and self.ensemble and len(self.ensemble.models) > 1:
                # Use ensemble analysis
                from app.services.ai_ensemble import ConsensusMethod

                ensemble_result = await self.ensemble.analyze_with_ensemble(
                    analysis_type=analysis_type,
                    code=code,
                    language=language,
                    file_path=file_path,
                    consensus_method=ConsensusMethod.CONFIDENCE_BASED,
                )

                # Enhance result with ensemble metadata
                result = ensemble_result.consensus_result.copy()
                result["ensemble_metadata"] = {
                    "models_used": ensemble_result.models_used,
                    "consensus_confidence": ensemble_result.consensus_confidence,
                    "consensus_method": ensemble_result.consensus_method.value,
                    "total_execution_time": ensemble_result.total_execution_time,
                    "individual_confidences": [
                        r.confidence
                        for r in ensemble_result.individual_results
                        if r.success
                    ],
                }

                logger.info(
                    f"Ensemble analysis completed with {len(ensemble_result.models_used)} models"
                )
                return result

            else:
                # Fallback to single model analysis
                if analysis_type == "pattern":
                    return await self.analyze_code_pattern(code, language)
                elif analysis_type == "quality":
                    return await self.analyze_code_quality(code, language)
                elif analysis_type == "security":
                    return await self.analyze_security(code, file_path, language)
                elif analysis_type == "performance":
                    return await self.analyze_performance(code, file_path, language)
                else:
                    raise ValueError(f"Unknown analysis type: {analysis_type}")

        except Exception as e:
            logger.error(f"Ensemble analysis failed: {e}")
            # Final fallback to basic single model
            if analysis_type == "pattern":
                return await self.analyze_code_pattern(code, language)
            elif analysis_type == "quality":
                return await self.analyze_code_quality(code, language)
            elif analysis_type == "security":
                return await self.analyze_security(code, file_path, language)
            elif analysis_type == "performance":
                return await self.analyze_performance(code, file_path, language)
            else:
                return {
                    "error": f"Analysis failed: {e}",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }

    def get_ensemble_status(self) -> Dict[str, Any]:
        """Get AI ensemble status"""
        if self.ensemble:
            return self.ensemble.get_ensemble_status()
        else:
            return {"ensemble_available": False, "reason": "Ensemble not initialized"}
