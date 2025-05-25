import json
import logging
import re
import asyncio
from datetime import datetime
from typing import Any, Dict, List

from langchain.llms import Ollama
from langchain.embeddings import OllamaEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field

from app.core.database import get_collection

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
    """Enhanced AI service with robust pattern analysis and embeddings"""

    def __init__(self):
        self.llm: Ollama = None
        self.embeddings: OllamaEmbeddings = None
        self.collection = None
        self.ollama_available: bool = False
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize AI services with fallback handling"""
        try:
            # Initialize Ollama LLM
            self.llm = Ollama(model="codellama:7b", temperature=0.1)
            # Test the connection
            self.llm("test")
            self.ollama_available = True
            logger.info("Ollama LLM initialized successfully")

            try:
                self.embeddings = OllamaEmbeddings(
                    model="nomic-embed-text", base_url="http://localhost:11434"
                )
                self.embeddings.embed_query("test")
                logger.info("Ollama embeddings initialized successfully")
            except Exception as e:
                logger.warning(f"Embeddings not available: {e}")
                self.embeddings = None

            self.collection = get_collection("code_patterns")
            if self.collection:
                logger.info("ChromaDB collection initialized")

        except Exception as e:
            logger.error(f"Error initializing AI services: {e}")
            self.ollama_available = False

    def get_status(self) -> Dict[str, Any]:
        """Get AI service status"""
        logger.info(f"Fetching AI service status: {self}")
        return {
            "ollama_available": self.ollama_available,
            "ollama_model": "codellama:7b" if self.ollama_available else None,
            "embeddings_available": self.embeddings is not None,
            "embeddings_model": "nomic-embed-text" if self.embeddings else None,
            "vector_db_available": self.collection is not None,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def analyze_code_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """
        Analyze code for patterns with enhanced AI understanding
        Fix #7: Use AI for dynamic pattern complexity and skill assessment
        """
        detected_patterns = self._detect_patterns_simple(code, language)

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
                        "Provide a comprehensive analysis including:\n"
                        " - All programming patterns used (be specific and thorough)\n"
                        " - Complexity score (1-10 based on pattern sophistication)\n"
                        " - Developer skill level based on pattern usage\n"
                        " - Specific suggestions for improvement\n\n"
                        "{format_instructions}"
                    ),
                )

                chain = LLMChain(llm=self.llm, prompt=prompt)

                # run in executor to avoid blocking
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chain.run(
                        code=code[:1500],
                        language=language,
                        simple_patterns=", ".join(detected_patterns),
                        format_instructions=parser.get_format_instructions(),
                    ),
                )

                ai_analysis = fixing_parser.parse(result)

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

    async def analyze_code_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality with detailed insights"""
        if self.ollama_available:
            try:
                parser = PydanticOutputParser(pydantic_object=CodeQualityAnalysis)
                fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=self.llm)

                prompt = PromptTemplate(
                    input_variables=["code", "language", "format_instructions"],
                    template=(
                        "Analyze the quality of this {language} code.\n"
                        "{code}\n\n"
                        "Evaluate:\n"
                        " - Overall quality score (1-100)\n"
                        " - Readability assessment\n"
                        " - Specific issues found\n"
                        " - Concrete improvements\n\n"
                        "{format_instructions}"
                    ),
                )

                chain = LLMChain(llm=self.llm, prompt=prompt)

                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chain.run(
                        code=code[:1500],
                        language=language,
                        format_instructions=parser.get_format_instructions(),
                    ),
                )

                quality_analysis = fixing_parser.parse(result)

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

    async def generate_insights(
        self, analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate high-level insights based on patterns, technologies, and optionally AI.
        """
        insights: List[Dict[str, Any]] = []

        # Pattern summary
        patterns = analysis_data.get("patterns", {})
        if patterns:
            insights.append(
                {
                    "type": "pattern_summary",
                    "title": f"Detected {len(patterns)} Programming Patterns",
                    "description": f"Most common patterns: {', '.join(list(patterns.keys())[:3])}",
                    "data": {"patterns": patterns},
                }
            )

        # Technology stack overview
        technologies = analysis_data.get("technologies", [])
        if technologies:
            insights.append(
                {
                    "type": "technology_adoption",
                    "title": "Technology Stack Analysis",
                    "description": f"Primary technologies: {', '.join(technologies[:3])}",
                    "data": {"technologies": technologies},
                }
            )

        # You can add an LLM-powered insight here if desired...

        return insights

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
                    "timestamp": datetime.utcnow().isoformat(),
                    "code_preview": code[:200],
                }
            )

            self.collection.add(
                embeddings=[embedding],
                documents=[code[:1000]],
                metadatas=[metadata],
                ids=[f"code_{datetime.utcnow().timestamp()}_{hash(code)}"],
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
        # … (unchanged pattern‐detection rules) …
        patterns: List[str] = []
        # … your existing regex‐based detectors …
        return list(set(patterns))

    def _enhanced_simple_analysis(
        self, code: str, patterns: List[str], language: str
    ) -> Dict[str, Any]:
        # … (unchanged fallback analysis) …
        return {
            "detected_patterns": patterns,
            "ai_patterns": [],
            "combined_patterns": patterns,
            "complexity_score": 3.0,
            "skill_level": "intermediate",
            "suggestions": ["Enable Ollama for detailed AI-powered suggestions"],
            "ai_powered": False,
        }

    def _enhanced_quality_analysis(self, code: str, language: str) -> Dict[str, Any]:
        # … (unchanged quality fallback) …
        return {
            "quality_score": 80,
            "readability": "Fair",
            "issues": ["No major issues detected"],
            "improvements": ["Maintain current standards"],
            "ai_powered": False,
        }
