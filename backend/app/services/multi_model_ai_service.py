# app/services/multi_model_ai_service.py - FIXED & ENHANCED VERSION
import os
import json
import logging
import asyncio
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    OllamaLLM = None
from langchain_community.llms import Ollama

logger = logging.getLogger(__name__)


# New MongoDB-optimized multi-model service
# class MongoMultiModelService:
#     async def store_comparison_result(self, comparison_data):
#         """Store multi-model comparison in MongoDB"""
#         document = {
#             "comparison_id": str(uuid.uuid4()),
#             "repository_id": comparison_data["repository_id"],
#             "models_compared": comparison_data["models"],
#             "individual_results": [
#                 {
#                     "model": result.model.value,
#                     "patterns": result.patterns,
#                     "complexity_score": result.complexity_score,
#                     "confidence": result.confidence,
#                     "processing_time": result.processing_time,
#                     "suggestions": result.suggestions,
#                     "token_usage": result.token_usage,
#                 }
#                 for result in comparison_data["results"]
#             ],
#             "comparison_analysis": {
#                 "consensus_patterns": comparison_data["consensus_patterns"],
#                 "disputed_patterns": comparison_data["disputed_patterns"],
#                 "agreement_score": comparison_data["agreement_score"],
#             },
#             "created_at": datetime.utcnow(),
#             "metadata": {
#                 "code_language": comparison_data.get("language"),
#                 "analysis_type": "multi_model_comparison",
#             },
#         }

#         result = await model_comparisons_collection.insert_one(document)
#         return str(result.inserted_id)


class AIModel(str, Enum):
    """Supported AI models for code analysis"""

    CODELLAMA_7B = "codellama:7b"
    DEVSTRAL = "devstral"
    GEMMA3N = "gemma3n"
    OPENAI_GPT4 = "gpt-4"
    OPENAI_GPT35_TURBO = "gpt-3.5-turbo"
    OPENAI_GPT4_1_MINI = "gpt-4.1-mini"
    OPENAI_GPT4_1_NANO = "gpt-4.1-nano"
    OPENAI_GPT4O_MINI = "gpt-4o-mini"
    OPENAI_O4_MINI = "o4-mini"
    OPENAI_O3_MINI = "o3-mini"
    CLAUDE_SONNET = "claude-3-7-sonnet-20250219"


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
        """Initialize Ollama local models with fast startup"""
        logger.info("🔄 Initializing Ollama models...")
        
        # Quick availability check
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
            if response.status_code != 200:
                logger.warning("❌ Ollama service not available, skipping all Ollama models")
                return
            
            available_models_data = response.json().get("models", [])
            available_model_names = [m["name"].split(":")[0] for m in available_models_data]
            logger.info(f"📋 Found {len(available_model_names)} Ollama models: {available_model_names}")
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"❌ Cannot connect to Ollama: {e}, skipping all Ollama models")
            return

        ollama_models = [
            (
                AIModel.CODELLAMA_7B,
                "CodeLlama 7B",
                ["Fast inference", "Good for basic patterns", "Privacy-focused"],
            ),
            (
                AIModel.DEVSTRAL,
                "devstral",
                [
                    "Better reasoning",
                    "Complex pattern detection",
                    "Architectural insights",
                ],
            ),
            (
                AIModel.GEMMA3N,
                "gemma3n",
                ["Google's code model", "Good performance", "Open source"],
            ),
        ]

        for model_enum, display_name, strengths in ollama_models:
            try:
                # Check if this specific model is downloaded
                if model_enum.value not in available_model_names:
                    logger.info(f"⏭️ {display_name} not downloaded, skipping initialization")
                    continue

                # Initialize client without testing (lazy loading for fast startup)
                if OllamaLLM is not None:
                    client = OllamaLLM(model=model_enum.value, temperature=0.1)
                else:
                    client = Ollama(model=model_enum.value, temperature=0.1)
                
                self.model_clients[model_enum] = client
                self.available_models[model_enum] = ModelInfo(
                    name=display_name,
                    provider="Ollama (Local)",
                    context_window=16384,
                    cost_per_1k_tokens=0.0,  # Free local
                    strengths=strengths,
                    available=True,
                )
                logger.info(f"✅ {display_name} initialized (lazy loading)")
                
            except Exception as e:
                logger.warning(f"❌ {display_name} not available: {e}")

    def _init_openai_models(self):
        """Initialize OpenAI API models"""
        if not os.getenv("OPENAI_API_KEY"):
            logger.info("🔑 OpenAI API key not found, skipping OpenAI models")
            return

        try:
            # Legacy models
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

            # New 2025 models with improved capabilities
            self.available_models[AIModel.OPENAI_GPT4_1_MINI] = ModelInfo(
                name="GPT-4.1 Mini",
                provider="OpenAI",
                context_window=1000000,  # 1M token context window
                cost_per_1k_tokens=0.0004,  # $0.40 per million input tokens
                strengths=[
                    "Major gains in coding",
                    "Instruction following",
                    "83% cost reduction vs GPT-4o",
                    "2x faster than GPT-4o",
                ],
                available=True,
            )

            self.available_models[AIModel.OPENAI_GPT4_1_NANO] = ModelInfo(
                name="GPT-4.1 Nano",
                provider="OpenAI",
                context_window=1000000,  # 1M token context window
                cost_per_1k_tokens=0.0001,  # $0.10 per million input tokens
                strengths=[
                    "Fastest and cheapest",
                    "Exceptional small model performance",
                    "80.1% on MMLU",
                    "Superior coding capabilities",
                ],
                available=True,
            )

            self.available_models[AIModel.OPENAI_GPT4O_MINI] = ModelInfo(
                name="GPT-4o Mini",
                provider="OpenAI",
                context_window=128000,
                cost_per_1k_tokens=0.00015,  # Most cost-efficient
                strengths=[
                    "Cost-efficient intelligence",
                    "Vision capabilities",
                    "Good balance of speed and quality",
                ],
                available=True,
            )

            self.available_models[AIModel.OPENAI_O4_MINI] = ModelInfo(
                name="O4-Mini",
                provider="OpenAI",
                context_window=200000,
                cost_per_1k_tokens=0.0011,  # $1.10 per million input tokens
                strengths=[
                    "Optimized for reasoning",
                    "Best performance on AIME 2024/2025",
                    "Excellent in math and coding",
                    "Visual task capabilities",
                ],
                available=True,
            )

            self.available_models[AIModel.OPENAI_O3_MINI] = ModelInfo(
                name="O3-Mini",
                provider="OpenAI",
                context_window=200000,  # Assumed similar to O4-mini
                cost_per_1k_tokens=0.002,  # Estimated based on O-series pricing
                strengths=[
                    "Advanced reasoning capabilities",
                    "Latest O-series model",
                    "Trained to think longer",
                    "Smart and efficient",
                ],
                available=True,
            )

            logger.info("✅ OpenAI models configured (including new 2025 models)")
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

    def get_available_models(self) -> Dict[str, Dict]:
        """Get all available models with their info"""
        return {
            model.value: {
                "id": model.value,  # Add the model ID that frontend expects
                "name": model.value,  # Use model.value as the technical name
                "display_name": info.name,  # Use info.name as the display name
                "provider": info.provider,
                "context_window": info.context_window,
                "cost_per_1k_tokens": info.cost_per_1k_tokens,
                "strengths": info.strengths,
                "available": info.available,
                "is_available": info.available,  # Frontend expects is_available
                "cost_tier": self._get_cost_tier(info.cost_per_1k_tokens),
                "is_free": info.cost_per_1k_tokens == 0.0,
                "model_type": "code_analysis",  # Default model type
                "created_at": "2024-01-01T00:00:00.000Z",  # Default timestamp
                "usage_count": 0,  # Default usage count
            }
            for model, info in self.available_models.items()
            if info.available
        }
    
    def _get_cost_tier(self, cost_per_1k_tokens: float) -> str:
        """Categorize model by cost tier"""
        if cost_per_1k_tokens == 0.0:
            return "free"
        elif cost_per_1k_tokens <= 0.0005:
            return "ultra_low"
        elif cost_per_1k_tokens <= 0.002:
            return "low"
        elif cost_per_1k_tokens <= 0.01:
            return "medium"
        else:
            return "high"
    
    def estimate_analysis_cost(self, code: str, model: AIModel) -> Dict[str, Any]:
        """Estimate the cost of analyzing code with a specific model"""
        if model not in self.available_models:
            return {"error": f"Model {model.value} not available"}
        
        model_info = self.available_models[model]
        
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        estimated_input_tokens = len(code) // 4
        
        # Add some overhead for prompt formatting
        total_input_tokens = estimated_input_tokens + 200
        
        # Estimate output tokens (typically much smaller than input for analysis)
        estimated_output_tokens = min(500, total_input_tokens // 4)
        
        if model_info.cost_per_1k_tokens == 0.0:
            return {
                "model": model.value,
                "estimated_input_tokens": total_input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "estimated_cost": 0.0,
                "cost_breakdown": {
                    "input_cost": 0.0,
                    "output_cost": 0.0,
                },
                "is_free": True,
            }
        
        # Different pricing for input vs output tokens (output typically 4x more expensive)
        input_cost_per_1k = model_info.cost_per_1k_tokens
        output_cost_per_1k = model_info.cost_per_1k_tokens * 4  # Typical ratio
        
        input_cost = (total_input_tokens / 1000) * input_cost_per_1k
        output_cost = (estimated_output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        
        return {
            "model": model.value,
            "estimated_input_tokens": total_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_cost": round(total_cost, 6),
            "cost_breakdown": {
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
            },
            "is_free": False,
            "cost_tier": self._get_cost_tier(model_info.cost_per_1k_tokens),
        }

    async def analyze_with_model(
        self, code: str, language: str, model: AIModel, **kwargs
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
                AIModel.DEVSTRAL,
                AIModel.GEMMA3N,
            ]:
                result = await self._analyze_with_ollama(code, language, model, **kwargs)
            elif model in [
                AIModel.OPENAI_GPT4, 
                AIModel.OPENAI_GPT35_TURBO,
                AIModel.OPENAI_GPT4_1_MINI,
                AIModel.OPENAI_GPT4_1_NANO,
                AIModel.OPENAI_GPT4O_MINI,
                AIModel.OPENAI_O4_MINI,
                AIModel.OPENAI_O3_MINI,
            ]:
                result = await self._analyze_with_openai(code, language, model, **kwargs)
            elif model == AIModel.CLAUDE_SONNET:
                result = await self._analyze_with_claude(code, language, model, **kwargs)
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
        self, code: str, language: str, model: AIModel, **kwargs
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
                None, lambda: client.invoke(prompt)
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
        self, code: str, language: str, model: AIModel, **kwargs
    ) -> AnalysisResult:
        """Analyze with OpenAI models - Updated for current API"""
        try:
            # Use the newer OpenAI client approach
            import openai

            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Prepare API call parameters
            api_params = {
                "model": model.value,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert code analyzer. You MUST respond with ONLY valid JSON. No explanations, no text outside JSON. ONLY JSON."
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this {language} code. Respond with ONLY this JSON format (no additional text):

```{language}
{code[:2000]}
```

{{
    "patterns": ["list of programming patterns found"],
    "complexity_score": 5.5,
    "skill_level": "intermediate", 
    "suggestions": ["specific improvement suggestions"],
    "confidence": 0.8
}}"""
                    },
                ],
            }
            
            # Add temperature for models that support it (exclude o3/o4 models)
            if not any(x in model.value for x in ["o3-mini", "o4-mini", "o3", "o4"]):
                api_params["temperature"] = 0.1
            
            # Add token limit parameters from kwargs
            if "max_tokens" in kwargs:
                api_params["max_tokens"] = kwargs["max_tokens"]
            elif "max_completion_tokens" in kwargs:
                api_params["max_completion_tokens"] = kwargs["max_completion_tokens"]
            else:
                api_params["max_tokens"] = 1000  # Default fallback
            
            response = client.chat.completions.create(**api_params)

            content = response.choices[0].message.content
            data = self._parse_response_json(content)

            return AnalysisResult(
                model=model,
                patterns=data.get("patterns", []),
                complexity_score=float(data.get("complexity_score", 5.0)),
                skill_level=data.get("skill_level", "intermediate"),
                suggestions=data.get("suggestions", []),
                confidence=float(data.get("confidence", 0.8)),
                processing_time=0.0,  # Will be set by caller
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
                processing_time=0.0,
                error=str(e),
            )

    async def _analyze_with_claude(
        self, code: str, language: str, model: AIModel, **kwargs
    ) -> AnalysisResult:
        """Analyze with Anthropic Claude"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            message = client.messages.create(
                model="claude-3-7-sonnet-20250219",
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
                processing_time=0.0,  # Will be set by caller
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
                processing_time=0.0,
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
