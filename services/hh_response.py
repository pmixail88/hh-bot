import aiohttp
import urllib.parse
from typing import Optional, Dict, List
from datetime import datetime

from utils.logger import get_logger
logger = get_logger(__name__)

class HHResponseService:
    """Сервис для работы с HH API (авторизация и отклики)"""
    
    def __init__(self, config):
        self.config = config
        self.api_base_url = "https://api.hh.ru"
        self.oauth_base_url = "https://hh.ru/oauth"
        self.client_id = config.client_id
        self.client_secret = config.client_secret
    
    def get_auth_url(self, state: str = "default") -> str:
        """Получить URL для авторизации через OAuth"""
        # HH требует точный redirect_uri, зарегистрированный в приложении
        redirect_uri = "http://127.0.0.1:8080/callback"  # Или ваш зарегистрированный URL
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'state': state,
            #'client_secret': self.client_secret
        }
        return f"{self.oauth_base_url}/authorize?{urllib.parse.urlencode(params)}"
    
    async def get_access_token(self, code: str) -> Optional[Dict]:
        """Получить access token по коду авторизации"""
        try:
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': 'http://127.0.0.1:8080/callback'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.oauth_base_url}/token", data=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка получения токена: {response.status}, {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка в get_access_token: {e}")
            return None
    
    async def send_application(self, access_token: str, vacancy_id: str, resume_id: str, message: str = "", phone: str = None, email: str = None) -> bool:
        """Отправить отклик на вакансию через HH API"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "HH-Bot/1.0",
                "HH-User-Agent": "HH-Bot/1.0"
            }
            
            data = {
                "resume_id": resume_id,
                "message": message[:4000],  # Ограничение HH API
                "vacancy_id": vacancy_id
            }
            
            # Добавляем контакты если указаны
            if phone:
                data["phone"] = phone
            if email:
                data["email"] = email
            
            logger.info(f"Отправка отклика на вакансию {vacancy_id}")
            logger.info(f"Данные: {data}")
            
            # Временно возвращаем True для тестирования
            # Для реальной отправки раскомментируйте код ниже:
            """
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/negotiations",
                    headers=headers,
                    json=data
                ) as response:
                    
                    if response.status == 201:
                        logger.info(f"Отклик отправлен на вакансию {vacancy_id}")
                        return True
                    elif response.status == 403:
                        logger.error("Нет доступа (возможно, требуется подтверждение телефона)")
                        return False
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка отправки отклика: {response.status} - {error_text}")
                        return False
            """
            
            # Временная заглушка для тестирования
            import asyncio
            await asyncio.sleep(2)
            logger.info("✅ Отклик отправлен (заглушка)")
            return True
                        
        except Exception as e:
            logger.error(f"Ошибка в send_application: {e}")
            return False
    
    async def get_user_resumes(self, access_token: str) -> List[Dict]:
        """Получить список резюме пользователя на HH"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "HH-Bot/1.0"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/resumes/mine",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
        except Exception as e:
            logger.error(f"Ошибка получения резюме: {e}")
            return []
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict]:
        """Обновить access token"""
        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.oauth_base_url}/token", data=data) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Ошибка обновления токена: {e}")
            return None