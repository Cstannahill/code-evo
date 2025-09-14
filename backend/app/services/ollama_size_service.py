import asyncio
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaModelSizeService:
    """Service to fetch, cache, and serve Ollama model sizes via backend."""

    def __init__(self):
        self.ollama_base_url = "http://127.0.0.1:11434"
        self.cache_ttl = 300  # 5 minutes cache
        self.last_check = None
        self._cached_models = {}

        # Try to initialize Redis cache
        try:
            from app.core.database import get_enhanced_database_manager

            db_manager = get_enhanced_database_manager()
            self.cache = db_manager.cache if db_manager else None
        except Exception as e:
            logger.warning(f"Redis cache not available for Ollama size service: {e}")
            self.cache = None

    async def _fetch_ollama_tags(self) -> Optional[Dict[str, Any]]:
        """Fetch /api/tags from local Ollama instance."""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Ollama tags fetch failed: HTTP {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            logger.debug("Ollama not running on localhost:11434")
            return None
        except Exception as e:
            logger.warning(f"Error fetching Ollama tags: {e}")
            return None

    def _parse_model_sizes(
        self, tags_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Parse /api/tags response and extract model size info."""
        models = {}

        for model in tags_data.get("models", []):
            name = model.get("name", "")
            size = model.get("size", 0)

            if name and size > 0:
                models[name] = {
                    "name": name,
                    "size_bytes": size,
                    "size_gb": round(size / (1024**3), 1),
                    "modified_at": model.get("modified_at", ""),
                    "digest": model.get("digest", ""),
                    "details": model.get("details", {}),
                }

        return models

    async def update_model_sizes(self) -> Dict[str, Dict[str, Any]]:
        """Fetch and cache latest model sizes from Ollama."""
        try:
            # Check if we need to refresh
            now = datetime.utcnow()
            if (
                self.last_check
                and (now - self.last_check).total_seconds() < self.cache_ttl
            ):
                return self._cached_models

            # Fetch fresh data
            tags_data = await self._fetch_ollama_tags()
            if not tags_data:
                return self._cached_models

            # Parse sizes
            models = self._parse_model_sizes(tags_data)

            # Update cache
            self._cached_models = models
            self.last_check = now

            # Store in Redis if available
            if self.cache:
                try:
                    cache_key = "ollama:model_sizes"
                    await self.cache.set(
                        cache_key, json.dumps(models), ttl=self.cache_ttl
                    )
                except Exception as e:
                    logger.warning(f"Failed to cache Ollama sizes in Redis: {e}")

            logger.info(f"Updated Ollama model sizes: {len(models)} models found")
            return models

        except Exception as e:
            logger.error(f"Failed to update Ollama model sizes: {e}")
            return self._cached_models

    async def get_model_sizes(self) -> Dict[str, Dict[str, Any]]:
        """Get cached model sizes, refreshing if needed."""
        # Try Redis first if available
        if self.cache:
            try:
                cache_key = "ollama:model_sizes"
                cached = await self.cache.get(cache_key)
                if cached and isinstance(cached, str):
                    return json.loads(cached)
            except Exception as e:
                logger.debug(f"Redis cache miss for Ollama sizes: {e}")

        # Fall back to updating from Ollama
        return await self.update_model_sizes()

    async def get_model_size_gb(self, model_name: str) -> Optional[float]:
        """Get size in GB for a specific model."""
        try:
            models = await self.get_model_sizes()
            model_info = models.get(model_name)
            if model_info:
                return model_info.get("size_gb")
            return None
        except Exception as e:
            logger.warning(f"Failed to get size for model {model_name}: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        return {
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "cached_models_count": len(self._cached_models),
            "cache_available": self.cache is not None,
            "ollama_url": self.ollama_base_url,
        }


# Global service instance
_ollama_size_service: Optional[OllamaModelSizeService] = None


def get_ollama_size_service() -> OllamaModelSizeService:
    """Get the global Ollama size service instance."""
    global _ollama_size_service
    if _ollama_size_service is None:
        _ollama_size_service = OllamaModelSizeService()
    return _ollama_size_service
