import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class SimpleCache:
    """Простой in-memory кэш как заглушка"""
    
    def __init__(self):
        self.cache = {}
        logger.info("✅ Используется SimpleCache (in-memory)")
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить данные из кэша"""
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any, expire: int = 3600):
        """Сохранить данные в кэш"""
        self.cache[key] = value
    
    async def delete(self, key: str):
        """Удалить данные из кэша"""
        self.cache.pop(key, None)
    
    async def close(self):
        """Закрыть кэш"""
        self.cache.clear()