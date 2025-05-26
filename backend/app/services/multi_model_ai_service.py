# app/services/multi_model_ai_service.py - FIXED & ENHANCED VERSION
import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from langchain.llms import Ollama

logger = logging.getLogger(__name__)


class AIModel(str, Enum):
    """Supported AI models for code analysis"""

    CODELLAMA_7B = "codellama:7b"
    CODELLAMA_13B = "codellama:13b"
    CODEGEMMA_7B = "codegemma:7b"
    OPENAI_GPT4 = "gpt-4"
    OPENAI_GPT35_TURBO = "gpt-3.5-turbo"
    CLAUDE_SONNET = "claude-3-sonnet"


@dataclass
class ModelInfo:
    """Information about an AI model"""

    name: str
    provider: str
    context_window: int
    cost_per_1k_tokens: float
    strengths: List[str]
    available: bool = False


@dataclass
class AnalysisResult:
    """Result from AI model analysis"""

    model: AIModel
    patterns: List[str]
    complexity_score: float
    skill_level: str
    suggestions: List[str]
    confidence: float
    processing_time: float
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class MultiModelAIService:
    """Enhanced AI service supporting multiple models for comparison"""

    def __init__(self):
        self.available_models: Dict[AIModel, ModelInfo] = {}
        self.model_clients = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initialize all available AI model clients"""
        logger.info("🔄 Initializing multi-model AI service...")

        # Ollama Models (Local)
        self._init_ollama_models()

        # OpenAI Models (API)
        self._init_openai_models()

        # Anthropic Models (API)
        self._init_anthropic_models()

        logger.info(f"✅ Initialized {len(self.available_models)} AI models")

    def _init_ollama_models(self):
        """Initialize Ollama local models"""
        ollama_models = [
            (
                AIModel.CODELLAMA_7B,
                "CodeLlama 7B",
                ["Fast inference", "Good for basic patterns", "Privacy-focused"],
            ),
            (
                AIModel.CODELLAMA_13B,
                "CodeLlama 13B",
                [
                    "Better reasoning",
                    "Complex pattern detection",
                    "Architectural insights",
                ],
            ),
            (
                AIModel.CODEGEMMA_7B,
                "CodeGemma 7B",
                ["Google's code model", "Good performance", "Open source"],
            ),
        ]

        for model_enum, display_name, strengths in ollama_models:
            try:
                client = Ollama(model=model_enum.value, temperature=0.1)
                # Test connection with a simple prompt
                test_response = client("Hello")
                if test_response:
                    self.model_clients[model_enum] = client
                    self.available_models[model_enum] = ModelInfo(
                        name=display_name,
                        provider="Ollama (Local)",
                        context_window=16384,
                        cost_per_1k_tokens=0.0,  # Free local
                        strengths=strengths,
                        available=True,
                    )
                    logger.info(f"✅ {display_name} initialized")
            except Exception as e:
                logger.warning(f"❌ {display_name} not available: {e}")

    def _init_openai_models(self):
        """Initialize OpenAI API models"""
        if not os.getenv("OPENAI_API_KEY"):
            logger.info("🔑 OpenAI API key not found, skipping OpenAI models")
            return

        try:
            # We'll use a simple approach that works with current OpenAI library
            self.available_models[AIModel.OPENAI_GPT4] = ModelInfo(
                name="GPT-4",
                provider="OpenAI",
                context_window=128000,
                cost_per_1k_tokens=0.03,
                strengths=[
                    "Exceptional reasoning",
                    "Detailed explanations",
                    "Latest patterns",
                ],
                available=True,
            )

            self.available_models[AIModel.OPENAI_GPT35_TURBO] = ModelInfo(
                name="GPT-3.5 Turbo",
                provider="OpenAI",
                context_window=16384,
                cost_per_1k_tokens=0.002,
                strengths=["Fast", "Cost-effective", "Good general analysis"],
                available=True,
            )
            logger.info("✅ OpenAI models configured")
        except Exception as e:
            logger.warning(f"❌ OpenAI models initialization failed: {e}")

    def _init_anthropic_models(self):
        """Initialize Anthropic Claude models"""
        if not os.getenv("ANTHROPIC_API_KEY"):
            logger.info("🔑 Anthropic API key not found, skipping Claude models")
            return

        try:
            self.available_models[AIModel.CLAUDE_SONNET] = ModelInfo(
                name="Claude 3 Sonnet",
                provider="Anthropic",
                context_window=200000,
                cost_per_1k_tokens=0.015,
                strengths=["Code quality focus", "Security analysis", "Best practices"],
                available=True,
            )
            logger.info("✅ Anthropic Claude configured")
        except Exception as e:
            logger.warning(f"❌ Anthropic models initialization failed: {e}")

    def get_available_models(self) -> Dict[str, ModelInfo]:
        """Get all available models with their info"""
        return {
            model.value: info.__dict__
            for model, info in self.available_models.items()
            if info.available
        }

    async def analyze_with_model(
        self, code: str, language: str, model: AIModel
    ) -> AnalysisResult:
        """Analyze code with a specific model"""
        start_time = asyncio.get_event_loop().time()

        try:
            if (
                model not in self.available_models
                or not self.available_models[model].available
            ):
                return AnalysisResult(
                    model=model,
                    patterns=[],
                    complexity_score=0.0,
                    skill_level="unknown",
                    suggestions=[],
                    confidence=0.0,
                    processing_time=0.0,
                    error=f"Model {model.value} not available",
                )

            # Route to appropriate analysis method
            if model in [
                AIModel.CODELLAMA_7B,
                AIModel.CODELLAMA_13B,
                AIModel.CODEGEMMA_7B,
            ]:
                result = await self._analyze_with_ollama(code, language, model)
            elif model in [AIModel.OPENAI_GPT4, AIModel.OPENAI_GPT35_TURBO]:
                result = await self._analyze_with_openai(code, language, model)
            elif model == AIModel.CLAUDE_SONNET:
                result = await self._analyze_with_claude(code, language, model)
            else:
                raise ValueError(f"Unsupported model: {model}")

            processing_time = asyncio.get_event_loop().time() - start_time
            result.processing_time = processing_time

            logger.info(
                f"✅ Analysis completed with {model.value} in {processing_time:.2f}s"
            )
            return result

        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ Analysis failed with {model.value}: {e}")
            return AnalysisResult(
                model=model,
                patterns=[],
                complexity_score=0.0,
                skill_level="error",
                suggestions=[],
                confidence=0.0,
                processing_time=processing_time,
                error=str(e),
            )

    async def compare_models(
        self, code: str, language: str, models: List[AIModel]
    ) -> List[AnalysisResult]:
        """Analyze code with multiple models for comparison"""
        tasks = [
            self.analyze_with_model(code, language, model)
            for model in models
            if model in self.available_models
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if isinstance(result, AnalysisResult):
                valid_results.append(result)
            else:
                logger.error(f"Model comparison error: {result}")

        return valid_results

    async def analyze_repository_parallel(
        self, repository_id: str, models: List[AIModel]
    ) -> Dict[str, Any]:
        """Analyze repository with multiple models in parallel"""
        logger.info(f"🔄 Starting multi-model repository analysis for {repository_id}")

        try:
            # For now, we'll use a sample code snippet to demonstrate
            # In a full implementation, you'd get actual code from the repository
            sample_code = """
            async function fetchUserData(userId) {
                try {
                    const response = await fetch(`/api/users/${userId}`);
                    const userData = await response.json();
                    return userData;
                } catch (error) {
                    console.error('Failed to fetch user:', error);
                    throw error;
                }
            }
            """

            # Analyze with all models
            results = await self.compare_models(sample_code, "javascript", models)

            # Calculate comparison metrics
            all_patterns = set()
            model_patterns = {}

            for result in results:
                model_patterns[result.model.value] = set(result.patterns)
                all_patterns.update(result.patterns)

            # Calculate consensus and disputes
            consensus_patterns = (
                set.intersection(*model_patterns.values()) if model_patterns else set()
            )

            disputed_patterns = []
            for pattern in all_patterns:
                models_detecting = [
                    model
                    for model, patterns in model_patterns.items()
                    if pattern in patterns
                ]
                if len(models_detecting) < len(results):
                    disputed_patterns.append(
                        {
                            "pattern": pattern,
                            "detected_by": models_detecting,
                            "agreement_ratio": len(models_detecting) / len(results),
                        }
                    )

            # Calculate agreement score
            total_possible_agreements = len(all_patterns) * len(results)
            actual_agreements = sum(
                sum(
                    1
                    for model_patterns_set in model_patterns.values()
                    if pattern in model_patterns_set
                )
                for pattern in all_patterns
            )
            agreement_score = (
                actual_agreements / total_possible_agreements
                if total_possible_agreements > 0
                else 0
            )

            return {
                "consensus_patterns": list(consensus_patterns),
                "disputed_patterns": disputed_patterns,
                "agreement_score": round(agreement_score, 3),
                "individual_results": [
                    {
                        "model": r.model.value,
                        "patterns": r.patterns,
                        "complexity_score": r.complexity_score,
                        "confidence": r.confidence,
                        "processing_time": r.processing_time,
                        "error": r.error,
                    }
                    for r in results
                ],
                "performance": {
                    "processing_times": {
                        r.model.value: r.processing_time for r in results
                    },
                    "fastest_model": (
                        min(results, key=lambda x: x.processing_time).model.value
                        if results
                        else None
                    ),
                },
            }

        except Exception as e:
            logger.error(f"❌ Repository analysis failed: {e}")
            return {
                "error": str(e),
                "consensus_patterns": [],
                "disputed_patterns": [],
                "agreement_score": 0.0,
                "individual_results": [],
                "performance": {},
            }

    async def _analyze_with_ollama(
        self, code: str, language: str, model: AIModel
    ) -> AnalysisResult:
        """Analyze with Ollama models"""
        client = self.model_clients[model]

        prompt = f"""
        Analyze this {language} code for programming patterns and provide a JSON response:
        
        ```{language}
        {code[:1500]}
        ```
        
        Return only valid JSON with these exact fields:
        {{
            "patterns": ["list of detected programming patterns"],
            "complexity_score": 7.5,
            "skill_level": "intermediate",
            "suggestions": ["list of improvement suggestions"],
            "confidence": 0.85
        }}
        
        Important: Return ONLY the JSON object, no additional text.
        """

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: client(prompt)
            )

            # Parse JSON response (with robust fallback)
            data = self._parse_response_json(response)

            return AnalysisResult(
                model=model,
                patterns=data.get("patterns", []),
                complexity_score=float(data.get("complexity_score", 5.0)),
                skill_level=data.get("skill_level", "intermediate"),
                suggestions=data.get("suggestions", []),
                confidence=float(data.get("confidence", 0.7)),
                processing_time=0.0,  # Will be set by caller
            )
        except Exception as e:
            logger.error(f"Ollama analysis error for {model.value}: {e}")
            return AnalysisResult(
                model=model,
                patterns=["basic_patterns"],
                complexity_score=5.0,
                skill_level="intermediate",
                suggestions=[f"Error in {model.value} analysis: {str(e)}"],
                confidence=0.3,
                processing_time=0.0,
                error=str(e),
            )

    async def _analyze_with_openai(
        self, code: str, language: str, model: AIModel
    ) -> AnalysisResult:
        """Analyze with OpenAI models - Updated for current API"""
        try:
            # Use the newer OpenAI client approach
            import openai

            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            response = client.chat.completions.create(
                model=model.value,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code analyzer. Respond only with valid JSON.",
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Analyze this {language} code and return JSON:
                        
                        ```{language}
                        {code[:2000]}
                        ```
                        
                        Return only this JSON format:
                        {{
                            "patterns": ["list of programming patterns"],
                            "complexity_score": 1-10,
                            "skill_level": "beginner|intermediate|advanced", 
                            "suggestions": ["improvement suggestions"],
                            "confidence": 0-1
                        }}
                        """,
                    },
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            content = response.choices[0].message.content
            data = self._parse_response_json(content)

            return AnalysisResult(
                model=model,
                patterns=data.get("patterns", []),
                complexity_score=float(data.get("complexity_score", 5.0)),
                skill_level=data.get("skill_level", "intermediate"),
                suggestions=data.get("suggestions", []),
                confidence=float(data.get("confidence", 0.8)),
                token_usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            )
        except Exception as e:
            logger.error(f"OpenAI analysis error for {model.value}: {e}")
            return AnalysisResult(
                model=model,
                patterns=["api_error"],
                complexity_score=5.0,
                skill_level="intermediate",
                suggestions=[f"OpenAI API error: {str(e)}"],
                confidence=0.3,
                error=str(e),
            )

    async def _analyze_with_claude(
        self, code: str, language: str, model: AIModel
    ) -> AnalysisResult:
        """Analyze with Anthropic Claude"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            message = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Analyze this {language} code for patterns and quality. Return valid JSON only:
                        
                        ```{language}
                        {code[:3000]}
                        ```
                        
                        Return only this JSON format:
                        {{
                            "patterns": ["detected patterns"],
                            "complexity_score": 1-10,
                            "skill_level": "beginner|intermediate|advanced",
                            "suggestions": ["specific improvements"],
                            "confidence": 0-1
                        }}
                        """,
                    }
                ],
            )

            content = message.content[0].text
            data = self._parse_response_json(content)

            return AnalysisResult(
                model=model,
                patterns=data.get("patterns", []),
                complexity_score=float(data.get("complexity_score", 6.0)),
                skill_level=data.get("skill_level", "intermediate"),
                suggestions=data.get("suggestions", []),
                confidence=float(data.get("confidence", 0.85)),
                token_usage={
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens,
                    "total_tokens": message.usage.input_tokens
                    + message.usage.output_tokens,
                },
            )
        except Exception as e:
            logger.error(f"Claude analysis error: {e}")
            return AnalysisResult(
                model=model,
                patterns=["api_error"],
                complexity_score=6.0,
                skill_level="intermediate",
                suggestions=[f"Claude API error: {str(e)}"],
                confidence=0.3,
                error=str(e),
            )

    def _parse_response_json(self, response: str) -> Dict:
        """Robust JSON parsing with fallbacks"""
        try:
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Fallback: parse response manually
            return self._parse_fallback_response(response)

    def _parse_fallback_response(self, response: str) -> Dict:
        """Fallback parser for non-JSON responses"""
        patterns = []
        response_lower = response.lower()

        # Extract patterns based on keywords
        if "async" in response_lower and "await" in response_lower:
            patterns.append("async_await")
        if "function" in response_lower:
            patterns.append("functions")
        if "class" in response_lower:
            patterns.append("classes")
        if "error" in response_lower:
            patterns.append("error_handling")
        if "react" in response_lower:
            patterns.append("react_patterns")

        return {
            "patterns": patterns or ["basic_patterns"],
            "complexity_score": 5.0,
            "skill_level": "intermediate",
            "suggestions": ["Enable JSON output for better analysis"],
            "confidence": 0.5,
        }
