import aiohttp
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from utils.logger import get_logger
logger = get_logger(__name__)

class HHAuthManager:
    """Менеджер OAuth-авторизации HH.ru для бота"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_base_url = "https://api.hh.ru" # для API запросов
        self.oauth_base_url = "https://hh.ru/oauth" # для OAuth
    
    # В класс HHAuthManager добавьте:
    def get_auth_url(self, state: str = "default") -> str:
        """Получить URL для авторизации через OAuth"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Client ID или Client Secret не установлены")
        
        redirect_uri = "http://127.0.0.1:8080/callback"  # Убедитесь, что этот URI совпадает с настройками!
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'state': state,
        }
        # 1. Сначала формируем ссылку
        auth_url = f"{self.oauth_base_url}/authorize?{urllib.parse.urlencode(params)}"
        
        # 2. Затем логируем её (теперь переменная auth_url определена)
        logger.info(f"Сгенерирован auth_url: {auth_url[:100]}...")
        
        # 3. Возвращаем
        return auth_url
    
    async def exchange_code_for_token(self, auth_code: str) -> Optional[Dict]:
        """Обмен authorization_code на access_token и refresh_token"""
        url = f"{self.oauth_base_url}/token" # <-- ИСПРАВЛЕНО
        #url = f"{self.api_base_url}/token"
        #url = f"{self.oauth_base_url}/token"
        # Для бота используем redirect_uri=https://hh.ru
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'redirect_uri': 'http://127.0.0.1:8080/callback'  # Важно: должен совпадать с использованным в oauth_base_url
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'HH-Bot/1.0'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers) as response:
                    
                    if response.status == 200:
                        token_data = await response.json()
                        logger.info(f"Токен успешно получен для client_id: {self.client_id[:8]}...")
                        return token_data
                    elif response.status == 400:
                        error_text = await response.text()
                        logger.error(f"Ошибка 400 (неверный код или параметры): {error_text}")
                    elif response.status == 401:
                        logger.error("Ошибка 401 (неверный client_id/client_secret)")
                    elif response.status == 403:
                        logger.error("Ошибка 403 (доступ запрещен)")
                    else:
                        error_text = await response.text()
                        logger.error(f"Неизвестная ошибка {response.status}: {error_text}")
                    return None
                                        
        except Exception as e:
            logger.error(f"Ошибка в exchange_code_for_token: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """Обновление access_token с помощью refresh_token"""
        url = f"{self.api_base_url}/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Ошибка обновления токена: {e}")
            return None
    
    def is_token_expired(self, token_expires_timestamp: float) -> bool:
        """Проверка истек ли токен (с запасом в 5 минут)"""
        from datetime import datetime
        current_time = datetime.utcnow().timestamp()
        # Считаем токен просроченным за 5 минут до фактического истечения
        return current_time >= (token_expires_timestamp - 300)

    def calculate_expiry_time(self, expires_in_seconds: int) -> float:
        """Рассчитать timestamp истечения токена"""
        from datetime import datetime
        return datetime.utcnow().timestamp() + expires_in_seconds