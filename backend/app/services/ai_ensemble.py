"""
AI Model Ensemble Framework

Provides multi-model AI analysis with consensus building, confidence scoring,
and fallback mechanisms to improve analysis quality and reliability.
"""

import asyncio
import logging
import statistics
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of AI models in the ensemble"""
    LOCAL_LLM = "local_llm"          # Ollama local models
    OPENAI_API = "openai_api"        # OpenAI API models
    ANTHROPIC_API = "anthropic_api"  # Claude API models
    # Note: FALLBACK removed as it's not a real AI model for user selection


class ConsensusMethod(Enum):
    """Methods for building consensus from multiple model outputs"""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    CONFIDENCE_BASED = "confidence_based"
    BEST_SCORE = "best_score"


@dataclass
class ModelResult:
    """Result from a single AI model"""
    model_id: str
    model_type: ModelType
    result: Dict[str, Any]
    confidence: float
    execution_time: float
    success: bool
    error: Optional[str] = None


@dataclass
class EnsembleResult:
    """Consolidated result from model ensemble"""
    consensus_result: Dict[str, Any]
    individual_results: List[ModelResult]
    consensus_confidence: float
    consensus_method: ConsensusMethod
    models_used: List[str]
    total_execution_time: float


class AIModelInterface(ABC):
    """Abstract interface for AI models in the ensemble"""
    
    @abstractmethod
    async def analyze_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code pattern"""
        pass
        
    @abstractmethod
    async def analyze_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality"""
        pass
        
    @abstractmethod
    async def analyze_security(self, code: str, file_path: str, language: str) -> Dict[str, Any]:
        """Analyze security vulnerabilities"""
        pass
        
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass
        
    @abstractmethod
    def is_available(self) -> bool:
        """Check if model is available"""
        pass


class LocalLLMModel(AIModelInterface):
    """Wrapper for local LLM models (Ollama)"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.model_id = "ollama_codellama"
        self.model_type = ModelType.LOCAL_LLM
        
    async def analyze_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code pattern using local LLM"""
        return await self.ai_service.analyze_code_pattern(code, language)
        
    async def analyze_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality using local LLM"""
        return await self.ai_service.analyze_code_quality(code, language)
        
    async def analyze_security(self, code: str, file_path: str, language: str) -> Dict[str, Any]:
        """Analyze security using local LLM"""
        return await self.ai_service.analyze_security(code, file_path, language)
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get local LLM model info"""
        return {
            "model_id": self.model_id,
            "model_type": self.model_type.value,
            "provider": "ollama",
            "local": True,
            "cost": 0.0
        }
        
    def is_available(self) -> bool:
        """Check if local LLM is available"""
        return self.ai_service.ollama_available


class FallbackModel(AIModelInterface):
    """Rule-based fallback model when AI models are unavailable"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.model_id = "rule_based_fallback"
        self.model_type = ModelType.FALLBACK
        
    async def analyze_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze pattern using rule-based approach"""
        detected_patterns = self.ai_service._detect_patterns_simple(code, language)
        return self.ai_service._enhanced_simple_analysis(code, detected_patterns, language)
        
    async def analyze_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze quality using rule-based approach"""
        return self.ai_service._enhanced_quality_analysis(code, language)
        
    async def analyze_security(self, code: str, file_path: str, language: str) -> Dict[str, Any]:
        """Analyze security using rule-based patterns"""
        # Use security analyzer directly
        return await self.ai_service.analyze_security(code, file_path, language)
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get fallback model info"""
        return {
            "model_id": self.model_id,
            "model_type": self.model_type.value,
            "provider": "rule_based",
            "local": True,
            "cost": 0.0
        }
        
    def is_available(self) -> bool:
        """Fallback is always available"""
        return True


class AIEnsemble:
    """
    AI Model Ensemble for improved analysis quality
    
    Manages multiple AI models, builds consensus, and provides
    confidence scoring for analysis results.
    """
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.models: List[AIModelInterface] = []
        self.model_weights: Dict[str, float] = {}
        self.default_consensus = ConsensusMethod.CONFIDENCE_BASED
        self.min_models_for_consensus = 2
        self.timeout_seconds = 30
        
        # Initialize available models
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize available AI models"""
        try:
            # Add local LLM if available
            local_model = LocalLLMModel(self.ai_service)
            if local_model.is_available():
                self.models.append(local_model)
                self.model_weights[local_model.model_id] = 0.8
                logger.info("✅ Added local LLM to ensemble")
                
            # Note: Fallback model removed from user selection as it's not a real AI model
            # Fallback functionality is handled internally by the analysis service
            
            # TODO: Add OpenAI/Anthropic models when API keys are configured
            
            logger.info(f"🤖 AI Ensemble initialized with {len(self.models)} models")
            
        except Exception as e:
            logger.error(f"Error initializing AI ensemble: {e}")
            
    async def analyze_with_ensemble(
        self,
        analysis_type: str,
        code: str,
        language: str,
        file_path: str = "unknown",
        consensus_method: Optional[ConsensusMethod] = None
    ) -> EnsembleResult:
        """
        Perform analysis using ensemble of AI models
        
        Args:
            analysis_type: Type of analysis ('pattern', 'quality', 'security')
            code: Source code to analyze
            language: Programming language  
            file_path: File path for context
            consensus_method: Method for building consensus
            
        Returns:
            EnsembleResult with consensus and individual results
        """
        if not self.models:
            raise RuntimeError("No AI models available in ensemble")
            
        consensus_method = consensus_method or self.default_consensus
        start_time = asyncio.get_event_loop().time()
        
        # Execute analysis on all available models
        tasks = []
        for model in self.models:
            if model.is_available():
                task = self._execute_model_analysis(
                    model, analysis_type, code, language, file_path
                )
                tasks.append(task)
                
        if not tasks:
            raise RuntimeError("No available models for analysis")
            
        # Wait for all models with timeout
        try:
            individual_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning(f"Ensemble analysis timed out after {self.timeout_seconds}s")
            individual_results = [
                ModelResult(
                    model_id="timeout",
                    model_type=ModelType.FALLBACK,
                    result={},
                    confidence=0.0,
                    execution_time=self.timeout_seconds,
                    success=False,
                    error="Analysis timed out"
                )
            ]
            
        # Filter successful results
        successful_results = [
            r for r in individual_results 
            if isinstance(r, ModelResult) and r.success
        ]
        
        if not successful_results:
            # Use fallback if no models succeeded
            fallback_model = next(
                (m for m in self.models if m.model_type == ModelType.FALLBACK), 
                None
            )
            if fallback_model:
                fallback_result = await self._execute_model_analysis(
                    fallback_model, analysis_type, code, language, file_path
                )
                successful_results = [fallback_result]
                
        # Build consensus from successful results
        consensus_result, consensus_confidence = self._build_consensus(
            successful_results, consensus_method
        )
        
        total_time = asyncio.get_event_loop().time() - start_time
        
        return EnsembleResult(
            consensus_result=consensus_result,
            individual_results=individual_results,
            consensus_confidence=consensus_confidence,
            consensus_method=consensus_method,
            models_used=[r.model_id for r in successful_results],
            total_execution_time=total_time
        )
        
    async def _execute_model_analysis(
        self,
        model: AIModelInterface,
        analysis_type: str,
        code: str,
        language: str,
        file_path: str
    ) -> ModelResult:
        """Execute analysis on a single model"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Route to appropriate analysis method
            if analysis_type == "pattern":
                result = await model.analyze_pattern(code, language)
            elif analysis_type == "quality":
                result = await model.analyze_quality(code, language)
            elif analysis_type == "security":
                result = await model.analyze_security(code, file_path, language)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
                
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Extract confidence score
            confidence = result.get("confidence", 0.8)
            if isinstance(confidence, (list, tuple)):
                confidence = statistics.mean(confidence) if confidence else 0.8
                
            return ModelResult(
                model_id=model.model_id,
                model_type=model.model_type,
                result=result,
                confidence=float(confidence),
                execution_time=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Model {model.model_id} failed: {e}")
            
            return ModelResult(
                model_id=model.model_id,
                model_type=model.model_type,
                result={},
                confidence=0.0,
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
            
    def _build_consensus(
        self,
        results: List[ModelResult],
        method: ConsensusMethod
    ) -> Tuple[Dict[str, Any], float]:
        """Build consensus from multiple model results"""
        if not results:
            return {}, 0.0
            
        if len(results) == 1:
            return results[0].result, results[0].confidence
            
        try:
            if method == ConsensusMethod.CONFIDENCE_BASED:
                return self._confidence_based_consensus(results)
            elif method == ConsensusMethod.WEIGHTED_AVERAGE:
                return self._weighted_average_consensus(results)
            elif method == ConsensusMethod.MAJORITY_VOTE:
                return self._majority_vote_consensus(results)
            elif method == ConsensusMethod.BEST_SCORE:
                return self._best_score_consensus(results)
            else:
                # Default to highest confidence
                best_result = max(results, key=lambda r: r.confidence)
                return best_result.result, best_result.confidence
                
        except Exception as e:
            logger.error(f"Error building consensus: {e}")
            # Fallback to highest confidence result
            best_result = max(results, key=lambda r: r.confidence)
            return best_result.result, best_result.confidence
            
    def _confidence_based_consensus(
        self, 
        results: List[ModelResult]
    ) -> Tuple[Dict[str, Any], float]:
        """Build consensus based on model confidence scores"""
        # Weight results by confidence
        total_weight = sum(r.confidence for r in results)
        if total_weight == 0:
            return results[0].result, 0.0
            
        consensus_result = {}
        
        # For each key in results, compute weighted average
        all_keys = set()
        for result in results:
            if isinstance(result.result, dict):
                all_keys.update(result.result.keys())
                
        for key in all_keys:
            values = []
            weights = []
            
            for result in results:
                if key in result.result:
                    value = result.result[key]
                    weight = result.confidence
                    
                    if isinstance(value, (int, float)):
                        values.append(value * weight)
                        weights.append(weight)
                    elif isinstance(value, list):
                        # For lists, take union with weight-based frequency
                        for item in value:
                            values.append(item)
                            weights.append(weight)
                            
            if values and weights:
                if all(isinstance(v, (int, float)) for v in values):
                    # Weighted average for numeric values
                    consensus_result[key] = sum(values) / sum(weights)
                else:
                    # Most frequent for non-numeric values
                    consensus_result[key] = max(set(values), key=values.count)
                    
        # Average confidence
        avg_confidence = statistics.mean([r.confidence for r in results])
        
        return consensus_result, avg_confidence
        
    def _weighted_average_consensus(
        self, 
        results: List[ModelResult]
    ) -> Tuple[Dict[str, Any], float]:
        """Build consensus using model weights"""
        total_weight = 0
        weighted_results = {}
        
        for result in results:
            model_weight = self.model_weights.get(result.model_id, 1.0)
            total_weight += model_weight
            
            for key, value in result.result.items():
                if key not in weighted_results:
                    weighted_results[key] = []
                weighted_results[key].append((value, model_weight))
                
        consensus_result = {}
        for key, value_weight_pairs in weighted_results.items():
            if all(isinstance(v, (int, float)) for v, w in value_weight_pairs):
                # Weighted average for numeric values
                weighted_sum = sum(v * w for v, w in value_weight_pairs)
                consensus_result[key] = weighted_sum / total_weight
            else:
                # Most weighted for non-numeric values
                best_value = max(value_weight_pairs, key=lambda x: x[1])[0]
                consensus_result[key] = best_value
                
        # Weighted average confidence
        weighted_confidence = sum(
            r.confidence * self.model_weights.get(r.model_id, 1.0)
            for r in results
        ) / total_weight
        
        return consensus_result, weighted_confidence
        
    def _majority_vote_consensus(
        self, 
        results: List[ModelResult]
    ) -> Tuple[Dict[str, Any], float]:
        """Build consensus using majority vote"""
        consensus_result = {}
        
        # Collect all keys
        all_keys = set()
        for result in results:
            if isinstance(result.result, dict):
                all_keys.update(result.result.keys())
                
        for key in all_keys:
            values = []
            for result in results:
                if key in result.result:
                    values.append(result.result[key])
                    
            if values:
                if all(isinstance(v, (int, float)) for v in values):
                    # Average for numeric values
                    consensus_result[key] = statistics.mean(values)
                else:
                    # Most common for non-numeric values
                    consensus_result[key] = max(set(values), key=values.count)
                    
        # Average confidence
        avg_confidence = statistics.mean([r.confidence for r in results])
        
        return consensus_result, avg_confidence
        
    def _best_score_consensus(
        self, 
        results: List[ModelResult]
    ) -> Tuple[Dict[str, Any], float]:
        """Use result from model with best score"""
        # Find result with highest confidence
        best_result = max(results, key=lambda r: r.confidence)
        return best_result.result, best_result.confidence
        
    def get_ensemble_status(self) -> Dict[str, Any]:
        """Get status of ensemble models"""
        return {
            "total_models": len(self.models),
            "available_models": sum(1 for m in self.models if m.is_available()),
            "model_info": [m.get_model_info() for m in self.models],
            "consensus_methods": [method.value for method in ConsensusMethod],
            "default_consensus": self.default_consensus.value
        }


# Singleton instance
_ai_ensemble = None

def get_ai_ensemble(ai_service) -> AIEnsemble:
    """Get singleton AIEnsemble instance"""
    global _ai_ensemble
    if _ai_ensemble is None:
        _ai_ensemble = AIEnsemble(ai_service)
        logger.info("🤖 Initialized AI Ensemble (singleton)")
    return _ai_ensemble