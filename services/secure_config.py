import logging
from typing import Any, Dict, Optional
from core.config import HHConfig
from services.secure_storage import SecureStorageService
from core.config import HHConfig

logger = logging.getLogger(__name__)

class SecureConfigService:
    """Сервис для получения зашифрованных конфигураций"""
    
    def __init__(self, secure_storage: SecureStorageService):
        self.secure_storage = secure_storage
    
    async def get_hh_config_for_user(self, user_id: int) -> Optional[HHConfig]:
        """Получение конфигурации HH для пользователя"""
        try:
            secrets = await self.secure_storage.get_user_secrets(user_id)
            
            # Получаем значения с проверкой на None
            client_id = secrets.get('hh_client_id')
            client_secret = secrets.get('hh_client_secret')
            
            # Проверяем что оба значения не None
            if not client_id or not client_secret:
                return None
            
            # Создаем конфиг с зашифрованными данными
            # Теперь TypeScript знает что client_id и client_secret не None
            config = HHConfig(
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Добавляем токены если есть
            if secrets.get('hh_access_token'):
                config.access_token = secrets['hh_access_token']
            if secrets.get('hh_refresh_token'):
                config.refresh_token = secrets['hh_refresh_token']
            
            return config
            
        except Exception as e:
            logger.error(f"Ошибка получения HH конфига: {e}")
            return None
    
    async def get_llm_config_for_user(self, user_id: int) -> Dict[str, Any]:
        """Получение конфигурации LLM для пользователя в виде словаря"""
        try:
            # Используем метод из SecureStorageService
            config = await self.secure_storage.get_llm_config_for_user(user_id)
            return config
            
        except Exception as e:
            logger.error(f"Ошибка получения LLM конфига: {e}")
            return {}
    
    async def get_llm_service_for_user(self, user_id: int, config: Optional[Dict[str, Any]] = None):
        """Создание LLMService для пользователя на основе конфигурации"""
        try:
            from services.llm_service import LLMService  # <-- ПЕРЕНЕСТИ СЮДА
            from core.config import LLMConfig
            
            # Получаем конфиг если не передан
            if config is None:
                config = await self.get_llm_config_for_user(user_id)
            
            if not config.get('api_key'):
                return None
            
            # Создаем LLMConfig из словаря
            llm_config = LLMConfig()
            llm_config.api_key = config.get('api_key', '')
            llm_config.base_url = config.get('base_url', 'https://api.openai.com/v1')
            llm_config.model_name = config.get('model_name', 'gpt-4o-mini')
            
            # Создаем сервис
            return LLMService(llm_config)
            
        except Exception as e:
            logger.error(f"Ошибка создания LLMService: {e}")
            return None
    
    async def get_contact_info_for_user(self, user_id: int) -> Dict[str, Optional[str]]:
        """Получение контактной информации пользователя"""
        try:
            secrets = await self.secure_storage.get_user_secrets(user_id)
            
            return {
                'email': secrets.get('contact_email'),
                'phone': secrets.get('contact_phone')
            }
        except Exception as e:
            logger.error(f"Ошибка получения контактов: {e}")
            return {}