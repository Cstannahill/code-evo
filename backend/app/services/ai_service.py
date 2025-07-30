import json
import logging
import re
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field

from app.core.database import get_enhanced_database_manager, get_collection

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
                        "IMPORTANT: Respond ONLY with valid JSON matching this exact format. Do not include any explanations or additional text.\n\n"
                        "{format_instructions}\n\n"
                        "Return only the JSON object with:\n"
                        "- patterns: array of pattern names\n"
                        "- complexity_score: number 1-10\n"
                        "- evolution_stage: one of 'beginner', 'intermediate', 'advanced'\n"
                        "- suggestions: array of improvement suggestions"
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
                        "IMPORTANT: Respond ONLY with valid JSON matching this exact format. Do not include any explanations or additional text.\n\n"
                        "{format_instructions}\n\n"
                        "Return only the JSON object with:\n"
                        "- quality_score: number 1-100\n"
                        "- readability: string assessment\n"
                        "- issues: array of strings describing issues\n"
                        "- improvements: array of strings with suggestions"
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
                if "properties" in result.lower() or "type" in result.lower() and "object" in result.lower():
                    logger.warning("AI returned schema definition instead of data, using fallback")
                    raise ValueError("Invalid response format - schema returned instead of data")

                try:
                    evolution_analysis = fixing_parser.parse(result)
                except Exception as parse_error:
                    logger.error(f"Failed to parse evolution analysis: {parse_error}")
                    logger.debug(f"Raw result that failed parsing: {result}")
                    # Try basic fallback parsing
                    try:
                        # Try to extract JSON if present
                        import re
                        json_match = re.search(r'\{.*\}', result, re.DOTALL)
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
                            learning_insights="Unable to analyze evolution due to AI response format"
                        )

                return {
                    "complexity_change": evolution_analysis.complexity_change,
                    "new_patterns": evolution_analysis.new_patterns,
                    "improvements": evolution_analysis.improvements,
                    "learning_insights": evolution_analysis.learning_insights,
                    "ai_powered": True,
                    "timestamp": datetime.utcnow().isoformat(),
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
            "timestamp": datetime.utcnow().isoformat(),
        }

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
        }
