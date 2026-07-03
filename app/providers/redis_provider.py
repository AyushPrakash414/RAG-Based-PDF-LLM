import json
import hashlib
import logging
from typing import Any, Optional
import redis.asyncio as redis
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class RedisProvider:
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = None
        if self.settings.redis_url:
            self.redis_client = redis.from_url(
                self.settings.redis_url, 
                encoding="utf-8", 
                decode_responses=True
            )
            logger.info("Initialized Redis client.")
        else:
            logger.warning("REDIS_URL not set. Caching is disabled.")

    async def get_knowledge_base_version(self) -> str:
        """Get the current knowledge base version from Redis."""
        if not self.redis_client:
            return "0"
        
        try:
            version = await self.redis_client.get("knowledge_base_version")
            if not version:
                version = "1"
                await self.redis_client.set("knowledge_base_version", version)
            return version
        except Exception as e:
            logger.error(f"Error getting knowledge base version from Redis: {e}")
            return "0"

    async def increment_knowledge_base_version(self) -> str:
        """Increment the knowledge base version when documents are ingested."""
        if not self.redis_client:
            return "0"
            
        try:
            version = await self.redis_client.incr("knowledge_base_version")
            logger.info(f"Incremented knowledge base version to {version}")
            return str(version)
        except Exception as e:
            logger.error(f"Error incrementing knowledge base version: {e}")
            return "0"

    def _generate_cache_key(self, question: str, kb_version: str) -> str:
        """Generate a version-aware cache key using SHA256."""
        normalized_question = " ".join(question.lower().split())
        raw_key = f"{normalized_question}_{kb_version}"
        return f"rag_cache:{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()}"

    async def get_cached_response(self, question: str) -> Optional[dict]:
        """Retrieve a cached response for the given question."""
        if not self.redis_client:
            return None
            
        try:
            kb_version = await self.get_knowledge_base_version()
            cache_key = self._generate_cache_key(question, kb_version)
            
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for question: {question}")
                return json.loads(cached_data)
                
            return None
        except Exception as e:
            logger.error(f"Error reading from Redis cache: {e}")
            return None

    async def set_cached_response(self, question: str, response_data: dict, ttl_seconds: int = 21600):
        """Cache the response data for the given question."""
        if not self.redis_client:
            return
            
        try:
            kb_version = await self.get_knowledge_base_version()
            cache_key = self._generate_cache_key(question, kb_version)
            
            # Default TTL is 6 hours (21600 seconds)
            await self.redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(response_data)
            )
            logger.info(f"Cached response for question: {question}")
        except Exception as e:
            logger.error(f"Error writing to Redis cache: {e}")

redis_provider = RedisProvider()
