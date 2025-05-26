# app/services/multi_model_ai_service.py
import json
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from langchain.llms import Ollama
from langchain.embeddings import OllamaEmbeddings
import openai
import anthropic

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

        # Ollama Models
        try:
            # CodeLlama 7B
            codellama_7b = Ollama(model="codellama:7b", temperature=0.1)
            codellama_7b("test")  # Test connection
            self.model_clients[AIModel.CODELLAMA_7B] = codellama_7b
            self.available_models[AIModel.CODELLAMA_7B] = ModelInfo(
                name="CodeLlama 7B",
                provider="Meta/Ollama",
                context_window=16384,
                cost_per_1k_tokens=0.0,  # Free local
                strengths=[
                    "Fast inference",
                    "Good for basic patterns",
                    "Privacy-focused",
                ],
                available=True,
            )
            logger.info("✅ CodeLlama 7B initialized")
        except Exception as e:
            logger.warning(f"❌ CodeLlama 7B not available: {e}")

        try:
            # CodeLlama 13B
            codellama_13b = Ollama(model="codellama:13b", temperature=0.1)
            codellama_13b("test")
            self.model_clients[AIModel.CODELLAMA_13B] = codellama_13b
            self.available_models[AIModel.CODELLAMA_13B] = ModelInfo(
                name="CodeLlama 13B",
                provider="Meta/Ollama",
                context_window=16384,
                cost_per_1k_tokens=0.0,
                strengths=[
                    "Better reasoning",
                    "Complex pattern detection",
                    "Architectural insights",
                ],
                available=True,
            )
            logger.info("✅ CodeLlama 13B initialized")
        except Exception as e:
            logger.warning(f"❌ CodeLlama 13B not available: {e}")

        # OpenAI Models
        if openai_key := os.getenv("OPENAI_API_KEY"):
            openai.api_key = openai_key
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
            logger.info("✅ OpenAI models initialized")

        # Anthropic Claude
        if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            self.available_models[AIModel.CLAUDE_SONNET] = ModelInfo(
                name="Claude 3 Sonnet",
                provider="Anthropic",
                context_window=200000,
                cost_per_1k_tokens=0.015,
                strengths=["Code quality focus", "Security analysis", "Best practices"],
                available=True,
            )
            logger.info("✅ Anthropic Claude initialized")

    def get_available_models(self) -> Dict[str, ModelInfo]:
        """Get all available models with their info"""
        return {
            model.value: info
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
            if model in [AIModel.CODELLAMA_7B, AIModel.CODELLAMA_13B]:
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
        
        Return JSON with:
        - patterns: List of detected programming patterns
        - complexity_score: Float from 1-10 
        - skill_level: "beginner", "intermediate", or "advanced"
        - suggestions: List of improvement suggestions
        - confidence: Float from 0-1 indicating analysis confidence
        """

        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: client(prompt)
        )

        # Parse JSON response (with fallback)
        try:
            data = json.loads(response)
        except:
            # Fallback parsing if JSON is malformed
            data = self._parse_fallback_response(response)

        return AnalysisResult(
            model=model,
            patterns=data.get("patterns", []),
            complexity_score=float(data.get("complexity_score", 5.0)),
            skill_level=data.get("skill_level", "intermediate"),
            suggestions=data.get("suggestions", []),
            confidence=float(data.get("confidence", 0.7)),
        )

    async def _analyze_with_openai(
        self, code: str, language: str, model: AIModel
    ) -> AnalysisResult:
        """Analyze with OpenAI models"""
        client = openai.ChatCompletion()

        response = await client.acreate(
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
                {code[:2000]}  # GPT-4 can handle more
                ```
                
                JSON format:
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
        )

        content = response.choices[0].message.content
        data = json.loads(content)

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

    async def _analyze_with_claude(
        self, code: str, language: str, model: AIModel
    ) -> AnalysisResult:
        """Analyze with Anthropic Claude"""
        message = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                Analyze this {language} code for patterns and quality. Return valid JSON only:
                
                ```{language}
                {code[:3000]}  # Claude has large context
                ```
                
                JSON format:
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
        data = json.loads(content)

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

    def _parse_fallback_response(self, response: str) -> Dict:
        """Fallback parser for non-JSON responses"""
        # Simple regex-based parsing as fallback
        patterns = []
        if "react" in response.lower():
            patterns.append("react_patterns")
        if "function" in response.lower():
            patterns.append("functional_programming")

        return {
            "patterns": patterns,
            "complexity_score": 5.0,
            "skill_level": "intermediate",
            "suggestions": ["Enable JSON output for better analysis"],
            "confidence": 0.5,
        }
