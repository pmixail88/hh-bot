import pickle
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis = None
        self.memory_cache = {}  # Простой in-memory кэш как fallback
    
    async def _ensure_connection(self):
        """Обеспечивает подключение к Redis (пропускаем если не доступен)"""
        if self.redis is None:
            try:
                import redis.asyncio as redis
                self.redis = redis.from_url(
                    self.redis_url, 
                    decode_responses=False,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                await self.redis.ping()
                logger.info("✅ Подключение к Redis установлено")
            except Exception as e:
                logger.debug(f"⚠️ Redis недоступен, используем memory cache: {e}")
                self.redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить данные из кэша"""
        try:
            await self._ensure_connection()
            if self.redis:
                data = await self.redis.get(key)
                if data:
                    return pickle.loads(data)
        except Exception:
            # Используем memory cache как fallback
            return self.memory_cache.get(key)
        return None
    
    async def set(self, key: str, value: Any, expire: int = 3600):
        """Сохранить данные в кэш"""
        try:
            await self._ensure_connection()
            if self.redis:
                data = pickle.dumps(value)
                from datetime import timedelta
                await self.redis.setex(key, timedelta(seconds=expire), data)
        except Exception:
            # Используем memory cache как fallback
            self.memory_cache[key] = value
    
    async def delete(self, key: str):
        """Удалить данные из кэша"""
        try:
            await self._ensure_connection()
            if self.redis:
                await self.redis.delete(key)
        except Exception:
            # Удаляем из memory cache
            self.memory_cache.pop(key, None)
    
    async def close(self):
        """Закрыть соединение с Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None