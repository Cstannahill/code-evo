# app/services/cache_service.py - Advanced Caching Service
"""
Advanced Caching Service for Code Evolution Tracker

This service provides multi-layer caching with TTL management, cache warming,
and intelligent invalidation strategies for analysis results.

🔄 FRONTEND UPDATE NEEDED: No frontend changes required - this is backend optimization
"""

import json
import hashlib
import logging
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum
import pickle
import gzip
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache storage levels"""
    MEMORY = "memory"
    REDIS = "redis"
    DISK = "disk"


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"  # Time-based expiration
    LRU = "lru"  # Least Recently Used
    MANUAL = "manual"  # Manual invalidation only


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int]
    size_bytes: int
    tags: List[str]


class AnalysisCacheService:
    """
    Advanced caching service optimized for analysis results with 
    multi-layer storage and intelligent invalidation.
    """

    def __init__(self, redis_client=None, max_memory_size: int = 100 * 1024 * 1024):  # 100MB
        """
        Initialize cache service with multiple storage layers
        
        Args:
            redis_client: Redis client instance (optional)
            max_memory_size: Maximum memory cache size in bytes
        """
        self.redis_client = redis_client
        self.max_memory_size = max_memory_size
        
        # In-memory cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.memory_size = 0
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "redis_hits": 0,
            "disk_hits": 0,
            "evictions": 0,
            "total_requests": 0
        }
        
        # Cache prefixes for different analysis types
        self.prefixes = {
            "repository": "repo:",
            "pattern": "pattern:",
            "security": "security:",
            "quality": "quality:",
            "evolution": "evolution:",
            "technology": "tech:",
            "similarity": "sim:"
        }
        
        logger.info("AnalysisCacheService initialized")

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate deterministic cache key from arguments"""
        # Create a deterministic string from all arguments
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        
        return f"{prefix}{key_hash}"

    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of cached value"""
        try:
            if isinstance(value, (dict, list)):
                return len(json.dumps(value, default=str).encode())
            elif isinstance(value, str):
                return len(value.encode())
            else:
                return len(pickle.dumps(value))
        except Exception:
            return 1024  # Default estimate

    def _should_evict_memory(self, new_size: int) -> bool:
        """Check if memory eviction is needed"""
        return (self.memory_size + new_size) > self.max_memory_size

    def _evict_lru_memory(self, target_size: int) -> None:
        """Evict least recently used items from memory cache"""
        # Sort by last accessed time
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        freed_size = 0
        for key, entry in sorted_entries:
            if freed_size >= target_size:
                break
                
            self.memory_size -= entry.size_bytes
            freed_size += entry.size_bytes
            del self.memory_cache[key]
            self.stats["evictions"] += 1

    async def get(self, cache_type: str, *args, **kwargs) -> Optional[Any]:
        """
        Get value from cache with multi-layer lookup
        
        Args:
            cache_type: Type of cache (repository, pattern, etc.)
            *args, **kwargs: Arguments to generate cache key
            
        Returns:
            Cached value or None if not found
        """
        self.stats["total_requests"] += 1
        
        prefix = self.prefixes.get(cache_type, f"{cache_type}:")
        cache_key = self._generate_cache_key(prefix, *args, **kwargs)
        
        # 1. Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            
            # Check TTL
            if entry.ttl_seconds:
                age = (datetime.utcnow() - entry.created_at).total_seconds()
                if age > entry.ttl_seconds:
                    self._invalidate_key(cache_key)
                    self.stats["misses"] += 1
                    return None
            
            # Update access info
            entry.last_accessed = datetime.utcnow()
            entry.access_count += 1
            
            self.stats["hits"] += 1
            self.stats["memory_hits"] += 1
            logger.debug(f"Cache HIT (memory): {cache_key}")
            return entry.value

        # 2. Check Redis cache
        if self.redis_client:
            try:
                redis_key = f"analysis_cache:{cache_key}"
                # Handle both sync and async Redis clients
                if hasattr(self.redis_client, 'get') and asyncio.iscoroutinefunction(self.redis_client.get):
                    cached_data = await self.redis_client.get(redis_key)
                else:
                    cached_data = self.redis_client.get(redis_key)
                
                if cached_data:
                    try:
                        # Decompress and deserialize
                        decompressed = gzip.decompress(cached_data.encode('latin1'))
                        value = pickle.loads(decompressed)
                        
                        # Store in memory cache for faster future access
                        await self._store_in_memory(cache_key, value, ttl_seconds=3600)
                        
                        self.stats["hits"] += 1
                        self.stats["redis_hits"] += 1
                        logger.debug(f"Cache HIT (redis): {cache_key}")
                        return value
                        
                    except Exception as e:
                        logger.warning(f"Redis cache deserialization failed: {e}")
                        
            except Exception as e:
                logger.warning(f"Redis cache lookup failed: {e}")

        self.stats["misses"] += 1
        logger.debug(f"Cache MISS: {cache_key}")
        return None

    async def set(self, cache_type: str, value: Any, ttl_seconds: int = 3600, 
                  tags: List[str] = None, *args, **kwargs) -> bool:
        """
        Store value in cache with multi-layer storage
        
        Args:
            cache_type: Type of cache (repository, pattern, etc.)
            value: Value to cache
            ttl_seconds: Time to live in seconds
            tags: Tags for cache invalidation
            *args, **kwargs: Arguments to generate cache key
            
        Returns:
            True if successfully cached
        """
        prefix = self.prefixes.get(cache_type, f"{cache_type}:")
        cache_key = self._generate_cache_key(prefix, *args, **kwargs)
        
        if tags is None:
            tags = []
            
        success = True
        
        # Store in memory cache
        await self._store_in_memory(cache_key, value, ttl_seconds, tags)
        
        # Store in Redis cache
        if self.redis_client:
            try:
                redis_key = f"analysis_cache:{cache_key}"
                
                # Serialize and compress
                serialized = pickle.dumps(value)
                compressed = gzip.compress(serialized).decode('latin1')
                
                # Store with TTL - handle both sync and async Redis clients
                if hasattr(self.redis_client, 'setex') and asyncio.iscoroutinefunction(self.redis_client.setex):
                    await self.redis_client.setex(redis_key, ttl_seconds, compressed)
                else:
                    self.redis_client.setex(redis_key, ttl_seconds, compressed)
                
                logger.debug(f"Cache SET (redis): {cache_key}")
                
            except Exception as e:
                logger.warning(f"Redis cache storage failed: {e}")
                success = False
        
        return success

    async def _store_in_memory(self, cache_key: str, value: Any, 
                              ttl_seconds: int = 3600, tags: List[str] = None) -> None:
        """Store value in memory cache with size management"""
        if tags is None:
            tags = []
            
        value_size = self._calculate_size(value)
        
        # Check if eviction is needed
        if self._should_evict_memory(value_size):
            # Free up 25% more space than needed
            target_size = int(value_size * 1.25)
            self._evict_lru_memory(target_size)
        
        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            value=value,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=1,
            ttl_seconds=ttl_seconds,
            size_bytes=value_size,
            tags=tags
        )
        
        self.memory_cache[cache_key] = entry
        self.memory_size += value_size
        
        logger.debug(f"Cache SET (memory): {cache_key}, size: {value_size} bytes")

    async def invalidate(self, cache_type: str = None, tags: List[str] = None, 
                        pattern: str = None) -> int:
        """
        Invalidate cache entries based on criteria
        
        Args:
            cache_type: Invalidate specific cache type
            tags: Invalidate entries with specific tags
            pattern: Invalidate keys matching pattern
            
        Returns:
            Number of invalidated entries
        """
        invalidated_count = 0
        
        # Build list of keys to invalidate
        keys_to_invalidate = []
        
        for key, entry in self.memory_cache.items():
            should_invalidate = False
            
            if cache_type:
                prefix = self.prefixes.get(cache_type, f"{cache_type}:")
                if key.startswith(prefix):
                    should_invalidate = True
            
            if tags:
                if any(tag in entry.tags for tag in tags):
                    should_invalidate = True
            
            if pattern:
                import re
                if re.match(pattern, key):
                    should_invalidate = True
            
            if should_invalidate:
                keys_to_invalidate.append(key)
        
        # Invalidate memory cache
        for key in keys_to_invalidate:
            self._invalidate_key(key)
            invalidated_count += 1
        
        # Invalidate Redis cache
        if self.redis_client and cache_type:
            try:
                prefix = self.prefixes.get(cache_type, f"{cache_type}:")
                redis_pattern = f"analysis_cache:{prefix}*"
                
                # Note: This is a simplified implementation
                # In production, consider using Redis SCAN for large datasets
                # Handle both sync and async Redis clients
                if hasattr(self.redis_client, 'keys') and asyncio.iscoroutinefunction(self.redis_client.keys):
                    keys = await self.redis_client.keys(redis_pattern)
                    if keys:
                        if hasattr(self.redis_client, 'delete') and asyncio.iscoroutinefunction(self.redis_client.delete):
                            await self.redis_client.delete(*keys)
                        else:
                            self.redis_client.delete(*keys)
                else:
                    keys = self.redis_client.keys(redis_pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                    
            except Exception as e:
                logger.warning(f"Redis cache invalidation failed: {e}")
        
        logger.info(f"Invalidated {invalidated_count} cache entries")
        return invalidated_count

    def _invalidate_key(self, key: str) -> None:
        """Invalidate specific cache key"""
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            self.memory_size -= entry.size_bytes
            del self.memory_cache[key]

    async def warm_cache(self, warm_functions: List[Callable]) -> None:
        """
        Warm cache by pre-computing common analysis results
        
        Args:
            warm_functions: List of functions to call for cache warming
        """
        logger.info("Starting cache warming...")
        
        for func in warm_functions:
            try:
                await func()
            except Exception as e:
                logger.warning(f"Cache warming function failed: {e}")
        
        logger.info("Cache warming completed")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        hit_rate = 0
        if self.stats["total_requests"] > 0:
            hit_rate = (self.stats["hits"] / self.stats["total_requests"]) * 100
        
        return {
            **self.stats,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_usage_bytes": self.memory_size,
            "memory_usage_mb": round(self.memory_size / (1024 * 1024), 2),
            "memory_entries": len(self.memory_cache),
            "memory_max_mb": round(self.max_memory_size / (1024 * 1024), 2)
        }

    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        expired_keys = []
        now = datetime.utcnow()
        
        for key, entry in self.memory_cache.items():
            if entry.ttl_seconds:
                age = (now - entry.created_at).total_seconds()
                if age > entry.ttl_seconds:
                    expired_keys.append(key)
        
        for key in expired_keys:
            self._invalidate_key(key)
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)


def cache_analysis_result(cache_type: str, ttl_seconds: int = 3600, tags: List[str] = None):
    """
    Decorator for caching analysis results
    
    Args:
        cache_type: Type of analysis being cached
        ttl_seconds: Time to live for cached result
        tags: Tags for cache invalidation
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get cache service from service manager
            from app.core.service_manager import get_cache_service
            cache_service = get_cache_service()
            
            # Try to get from cache first
            cached_result = await cache_service.get(cache_type, *args, **kwargs)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(self, *args, **kwargs)
            
            if result is not None:
                await cache_service.set(
                    cache_type, result, ttl_seconds, tags, *args, **kwargs
                )
            
            return result
        return wrapper
    return decorator


# Global cache service instance
_cache_service: Optional[AnalysisCacheService] = None


def get_cache_service(redis_client=None) -> AnalysisCacheService:
    """Get global cache service instance"""
    global _cache_service
    
    if _cache_service is None:
        _cache_service = AnalysisCacheService(redis_client)
    
    return _cache_service


def invalidate_repository_cache(repository_id: str) -> None:
    """Convenience function to invalidate all cache for a repository"""
    cache_service = get_cache_service()
    asyncio.create_task(cache_service.invalidate(tags=[f"repo:{repository_id}"]))