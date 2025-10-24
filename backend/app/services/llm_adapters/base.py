"""Utility classes for working with interchangeable LLM providers.

The backend historically relied on locally hosted Ollama models that were
wired directly into LangChain primitives.  As we expand support for hosted
LLM APIs we need a thin abstraction layer that can:

* Normalise the request/response flow across providers.
* Provide structured (JSON) responses suitable for Pydantic parsing.
* Offer async friendly helpers even when the underlying SDKs are sync.

The adapter layer keeps the rest of the codebase agnostic of provider
specific details and makes it trivial to swap implementations via
configuration.
"""
from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMProviderNotAvailable(RuntimeError):
    """Raised when a provider cannot handle a request."""


class LLMProvider(ABC):
    """Base contract all concrete providers must satisfy."""

    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """Return ``True`` when the provider is ready for use."""

    @abstractmethod
    async def acompletion(self, prompt: str, *, instructions: Optional[str] = None, **kwargs: Any) -> str:
        """Execute a completion request and return the textual response."""

    async def astructured_completion(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        *,
        instructions: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[BaseModel]:
        """Return a structured response parsed into ``response_model``.

        Providers are encouraged to return strict JSON, however in practice
        the responses can contain surrounding prose.  We attempt to recover
        the JSON payload in a defensive manner before handing it to
        Pydantic.
        """

        raw = await self.acompletion(prompt, instructions=instructions, **kwargs)
        parsed = _extract_json(raw)
        if parsed is None:
            logger.debug("Provider %s returned non JSON output", getattr(self, "name", "unknown"))
            return None

        try:
            return response_model.model_validate(parsed)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Failed to coerce provider %s response into %s: %s",
                getattr(self, "name", "unknown"),
                response_model.__name__,
                exc,
            )
            return None


TModel = TypeVar("TModel", bound=BaseModel)


@dataclass
class ProviderMetadata:
    """Metadata describing an instantiated provider."""

    name: str
    priority: int
    provider: LLMProvider


class LLMAdapterManager:
    """Holds a list of providers and handles fail-over between them."""

    def __init__(self, providers: Sequence[Tuple[int, LLMProvider]]):
        ordered: List[ProviderMetadata] = []
        for priority, provider in providers:
            if not provider.is_available():
                logger.debug("Skipping unavailable LLM provider %s", getattr(provider, "name", "unknown"))
                continue
            ordered.append(ProviderMetadata(name=getattr(provider, "name", "unknown"), priority=priority, provider=provider))

        # Order by priority (lower value == higher priority)
        self._providers: List[ProviderMetadata] = sorted(ordered, key=lambda item: item.priority)

    @property
    def has_providers(self) -> bool:
        return bool(self._providers)

    @property
    def provider_names(self) -> List[str]:
        return [meta.name for meta in self._providers]

    async def astructured_completion(
        self,
        prompt: str,
        response_model: Type[TModel],
        *,
        instructions: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[TModel]:
        """Return a structured completion using the first working provider."""

        last_error: Optional[Exception] = None
        for meta in self._providers:
            try:
                logger.debug("Attempting completion using provider %s", meta.name)
                response = await meta.provider.astructured_completion(
                    prompt,
                    response_model,
                    instructions=instructions,
                    **kwargs,
                )
                if response is not None:
                    logger.info("LLM provider %s handled the request", meta.name)
                    return response
            except Exception as exc:  # pragma: no cover - defensive
                last_error = exc
                logger.warning("Provider %s failed to produce output: %s", meta.name, exc)

        if last_error:
            logger.error("All configured LLM providers failed, last error: %s", last_error)
        return None

    async def acompletion(
        self,
        prompt: str,
        *,
        instructions: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """Return a raw completion string using the first working provider."""

        for meta in self._providers:
            try:
                logger.debug("Attempting raw completion using provider %s", meta.name)
                return await meta.provider.acompletion(prompt, instructions=instructions, **kwargs)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Provider %s failed to produce raw output: %s", meta.name, exc)
        return None


def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from a raw LLM string response."""

    try:
        return json.loads(raw)
    except Exception:
        pass

    import re

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    snippet = match.group(0)
    try:
        return json.loads(snippet)
    except Exception:  # pragma: no cover - defensive parsing
        logger.debug("Failed to parse JSON snippet from provider output")
        return None


def build_adapter_manager(providers: Iterable[Tuple[int, LLMProvider]]) -> Optional[LLMAdapterManager]:
    """Helper used by the service manager to instantiate adapters."""

    manager = LLMAdapterManager(list(providers))
    if not manager.has_providers:
        return None
    return manager
