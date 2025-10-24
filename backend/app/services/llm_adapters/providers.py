"""Concrete LLM provider implementations."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

from .base import LLMAdapterManager, LLMProvider, LLMProviderNotAvailable, build_adapter_manager

logger = logging.getLogger(__name__)


class _BaseHTTPProvider(LLMProvider):
    """Utility class that performs blocking HTTP requests in a thread."""

    timeout: int = 60

    async def _post_json(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        def _call() -> Dict[str, Any]:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _call)


class OllamaProvider(_BaseHTTPProvider):
    name = "ollama"

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None) -> None:
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return any(tag.get("name") == self.model for tag in response.json().get("models", [])) or True
        except Exception:
            logger.debug("Ollama provider not available", exc_info=True)
            return False

    async def acompletion(self, prompt: str, *, instructions: Optional[str] = None, **kwargs: Any) -> str:
        payload = {
            "model": self.model,
            "prompt": self._build_prompt(prompt, instructions),
            "stream": False,
        }
        data = await self._post_json(f"{self.base_url}/api/generate", headers={}, payload=payload)
        text = data.get("response") or data.get("text")
        if not text:
            raise LLMProviderNotAvailable("Ollama response did not contain text")
        return text

    def _build_prompt(self, prompt: str, instructions: Optional[str]) -> str:
        if not instructions:
            return prompt
        return f"{instructions}\n\n{prompt}"


class OpenAIProvider(_BaseHTTPProvider):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = base_url or settings.OPENAI_API_BASE or "https://api.openai.com/v1/chat/completions"

    def is_available(self) -> bool:
        return bool(self.api_key and self.model)

    async def acompletion(self, prompt: str, *, instructions: Optional[str] = None, **kwargs: Any) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        system_prompt = instructions or (
            "You are an expert software analysis system. Always respond with valid JSON."
        )
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
        }
        # Request JSON mode when supported by the target model
        payload["response_format"] = {"type": "json_object"}
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        data = await self._post_json(self.base_url, headers=headers, payload=payload)
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # pragma: no cover - defensive
            raise LLMProviderNotAvailable(f"Unexpected OpenAI response format: {exc}") from exc


class AnthropicProvider(_BaseHTTPProvider):
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self._base_url = "https://api.anthropic.com/v1/messages"

    def is_available(self) -> bool:
        return bool(self.api_key and self.model)

    async def acompletion(self, prompt: str, *, instructions: Optional[str] = None, **kwargs: Any) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        system_prompt = instructions or (
            "You are an expert software analysis system. Always respond with valid JSON."
        )
        payload = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.2),
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = await self._post_json(self._base_url, headers=headers, payload=payload)
        content = data.get("content") or []
        if not content:
            raise LLMProviderNotAvailable("Anthropic response missing content")
        # Anthropic returns a list of content blocks
        text_blocks = [block.get("text", "") for block in content if block.get("type") == "text"]
        result = "\n".join(filter(None, text_blocks)).strip()
        if not result:
            raise LLMProviderNotAvailable("Anthropic response empty")
        return result


class BedrockProvider(LLMProvider):
    name = "bedrock"

    def __init__(self) -> None:
        try:
            import boto3  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            self._client = None
            logger.debug("boto3 is not installed; Bedrock provider disabled")
        else:
            region = settings.BEDROCK_REGION
            if region:
                self._client = boto3.client("bedrock-runtime", region_name=region)
            else:
                self._client = boto3.client("bedrock-runtime")
        self._model_id = settings.BEDROCK_MODEL_ID

    def is_available(self) -> bool:
        return bool(self._client and self._model_id)

    async def acompletion(self, prompt: str, *, instructions: Optional[str] = None, **kwargs: Any) -> str:
        if not self.is_available():
            raise LLMProviderNotAvailable("Bedrock provider not configured")

        body = {
            "inputText": self._build_prompt(prompt, instructions),
            "textGenerationConfig": {
                "temperature": kwargs.get("temperature", 0.2),
                "maxTokenCount": kwargs.get("max_tokens", 1024),
            },
        }

        loop = asyncio.get_event_loop()
        client = self._client
        assert client is not None

        def _call() -> str:
            response = client.invoke_model(modelId=self._model_id, body=json.dumps(body))
            payload = json.loads(response.get("body", "{}"))
            results = payload.get("results") or []
            if not results:
                raise LLMProviderNotAvailable("Bedrock response missing results")
            return results[0].get("outputText", "")

        return await loop.run_in_executor(None, _call)

    def _build_prompt(self, prompt: str, instructions: Optional[str]) -> str:
        if not instructions:
            return prompt
        return f"{instructions}\n\n{prompt}"


class VertexAIProvider(LLMProvider):
    name = "vertex"

    def __init__(self) -> None:
        try:
            from vertexai.preview.generative_models import GenerativeModel  # type: ignore
            from google.oauth2 import service_account  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            self._model = None
            logger.debug("Google Cloud dependencies missing; Vertex provider disabled")
            return

        credentials_info = settings.VERTEX_SERVICE_ACCOUNT_JSON
        if credentials_info:
            try:
                credentials = service_account.Credentials.from_service_account_info(json.loads(credentials_info))
            except Exception as exc:
                logger.error("Failed to load Vertex credentials: %s", exc)
                credentials = None
        else:
            credentials = None

        model_name = settings.VERTEX_MODEL
        if not model_name:
            self._model = None
            return

        try:
            self._model = GenerativeModel(model_name, credentials=credentials)
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.error("Failed to initialise VertexAI model: %s", exc)
            self._model = None

    def is_available(self) -> bool:
        return self._model is not None

    async def acompletion(self, prompt: str, *, instructions: Optional[str] = None, **kwargs: Any) -> str:
        if not self._model:
            raise LLMProviderNotAvailable("Vertex AI model unavailable")

        loop = asyncio.get_event_loop()
        system_prompt = instructions or "You are an expert software analysis system."
        model = self._model

        def _call() -> str:
            response = model.generate_content([
                {"role": "user", "parts": [system_prompt]},
                {"role": "user", "parts": [prompt]},
            ])
            text = "".join([part.text for part in response.candidates[0].content.parts])
            if not text:
                raise LLMProviderNotAvailable("Vertex response empty")
            return text

        return await loop.run_in_executor(None, _call)


def build_default_manager() -> Optional[LLMAdapterManager]:
    """Construct a manager based on environment configuration."""

    priority_list = [item.strip() for item in settings.AI_PROVIDER_PRIORITY.split(",") if item.strip()]
    providers = []
    for index, provider_name in enumerate(priority_list):
        priority = index  # lower index == higher priority
        provider_name_lower = provider_name.lower()
        if provider_name_lower == "ollama":
            providers.append((priority, OllamaProvider()))
        elif provider_name_lower == "openai":
            providers.append((priority, OpenAIProvider()))
        elif provider_name_lower == "anthropic":
            providers.append((priority, AnthropicProvider()))
        elif provider_name_lower == "bedrock":
            providers.append((priority, BedrockProvider()))
        elif provider_name_lower == "vertex":
            providers.append((priority, VertexAIProvider()))
        else:
            logger.warning("Unknown LLM provider '%s' in AI_PROVIDER_PRIORITY", provider_name)

    return build_adapter_manager(providers)
