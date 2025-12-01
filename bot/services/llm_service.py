import aiohttp
import asyncio
from typing import Dict, Optional, List
import logging

from core.config import LLMConfig
from services.cache import CacheService

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.cache = CacheService()
        self.timeout = aiohttp.ClientTimeout(total=config.timeout)

    async def generate_resume(self, user_profile: Dict, vacancy_info: Dict, llm_settings: Dict) -> Optional[str]:
        """Генерация резюме с использованием LLM"""
        cache_key = f"resume:{hash(frozenset(user_profile.items()))}:{hash(frozenset(vacancy_info.items()))}"
        
        # Пробуем получить из кэша
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info("✅ Найдено резюме в кэше")
            return cached

        try:
            prompt = self._create_resume_prompt(user_profile, vacancy_info)
            result = await self._call_llm_api(prompt, llm_settings)
            
            if result:
                # Кэшируем на 1 час
                await self.cache.set(cache_key, result, expire=3600)
                return result
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при генерации резюме: {e}")
            return None

    async def generate_cover_letter(self, user_profile: Dict, vacancy_info: Dict, llm_settings: Dict) -> Optional[str]:
        """Генерация сопроводительного письма"""
        cache_key = f"cover_letter:{hash(frozenset(user_profile.items()))}:{hash(frozenset(vacancy_info.items()))}"
        
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info("✅ Найдено сопроводительное письмо в кэше")
            return cached

        try:
            prompt = self._create_cover_letter_prompt(user_profile, vacancy_info)
            result = await self._call_llm_api(prompt, llm_settings)
            
            if result:
                await self.cache.set(cache_key, result, expire=3600)
                return result
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при генерации сопроводительного письма: {e}")
            return None

    def _create_resume_prompt(self, user_profile: Dict, vacancy_info: Dict) -> str:
        """Создание промпта для генерации резюме"""
        return f"""
Создай профессиональное резюме на русском языке на основе профиля кандидата и требований вакансии.

ПРОФИЛЬ КАНДИДАТА:
- Имя: {user_profile.get('full_name', 'Не указано')}
- Город: {user_profile.get('city', 'Не указан')}
- Желаемая должность: {user_profile.get('desired_position', 'Не указана')}
- Навыки: {user_profile.get('skills', 'Не указаны')}
- Опыт и квалификация: {user_profile.get('base_resume', 'Не указано')}

ИНФОРМАЦИЯ О ВАКАНСИИ:
- Должность: {vacancy_info.get('name', 'Не указана')}
- Компания: {vacancy_info.get('company_name', 'Не указана')}
- Описание: {vacancy_info.get('description', 'Не указано')[:1500]}

ТРЕБОВАНИЯ:
1. Структура: ФИО и контакты, Цель, Опыт работы, Образование, Навыки, Дополнительная информация
2. Адаптируй резюме под конкретную вакансию
3. Подчеркни релевантные навыки
4. Используй профессиональный язык
5. Объем: 300-500 слов
6. Формат: чистый текст без разметки

Создай профессиональное резюме:
"""

    def _create_cover_letter_prompt(self, user_profile: Dict, vacancy_info: Dict) -> str:
        """Создание промпта для генерации сопроводительного письма"""
        return f"""
Напиши сопроводительное письмо на русском языке для отклика на вакансию.

ПРОФИЛЬ КАНДИДАТА:
- Имя: {user_profile.get('full_name', 'Не указано')}
- Навыки: {user_profile.get('skills', 'Не указаны')}
- Опыт: {user_profile.get('base_resume', 'Не указано')}

ИНФОРМАЦИЯ О ВАКАНСИИ:
- Должность: {vacancy_info.get('name', 'Не указана')}
- Компания: {vacancy_info.get('company_name', 'Не указана')}
- Описание: {vacancy_info.get('description', 'Не указано')[:1500]}

ТРЕБОВАНИЯ:
1. Структура: Приветствие, Введение, Соответствие требованиям, Мотивация, Заключение
2. Персонализируй обращение к компании
3. Ссылайся на конкретные требования из описания вакансии
4. Подчеркни 2-3 ключевых навыка кандидата
5. Прояви энтузиазм и профессиональный интерес
6. Объем: 200-300 слов
7. Формат: деловое письмо

Напиши убедительное сопроводительное письмо:
"""

    async def _call_llm_api(self, prompt: str, llm_settings: Dict) -> Optional[str]:
        """Вызов LLM API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {llm_settings.get('api_key', self.config.api_key)}"
            }

            data = {
                "model": llm_settings.get('model_name', self.config.model_name),
                "messages": [
                    {
                        "role": "system", 
                        "content": "Ты профессиональный HR-консультант с опытом составления резюме и сопроводительных писем. Отвечай только на русском языке."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": llm_settings.get('temperature', self.config.temperature),
                "max_tokens": llm_settings.get('max_tokens', self.config.max_tokens),
                "top_p": 0.9
            }

            base_url = llm_settings.get('base_url', self.config.base_url)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            return result['choices'][0]['message']['content']
                        else:
                            logger.error(f"Неожиданный формат ответа LLM API: {result}")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка LLM API: {response.status}, {error_text}")
                        return None

        except asyncio.TimeoutError:
            logger.error("Таймаут при вызове LLM API")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при вызове LLM API: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при вызове LLM API: {e}")
            return None

    async def test_connection(self, llm_settings: Dict) -> bool:
        """Тестирование подключения к LLM API"""
        try:
            test_prompt = "Ответь одним словом: 'работает'"
            result = await self._call_llm_api(test_prompt, llm_settings)
            return result is not None and 'работает' in result.lower()
        except Exception as e:
            logger.error(f"Ошибка при тестировании LLM: {e}")
            return False