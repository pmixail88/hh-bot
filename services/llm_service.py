import os
import sys
import aiohttp
import asyncio
import json
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from core.config import get_config
from utils.logger import get_logger
# from core import config  # ← ДОБАВЬ ЭТО

# ЗАГРУЖАЕМ .env файл
load_dotenv()

# Настраиваем пути
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


logger = get_logger(__name__)

# Динамический импорт CacheService
try:
    from services.cache import CacheService

    cache_available = True
except ImportError:
    logger.warning("CacheService не найден, использую простой кэш")

class CacheService:
    def __init__(self):
        self.cache = {}

    async def get(self, key):
        return self.cache.get(key)

    async def set(self, key, value, expire=None):
        self.cache[key] = value

cache_available = False


logger = get_logger(__name__)


class LLMService:
    """Сервис для работы с LLM через OpenRouter"""

    def __init__(self, config):
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.model_name = config.model_name
        self.timeout = config.timeout
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature

        logger.info(f"LLMService инициализирован: {self.model_name} на {self.base_url}")

    async def _make_request(self, messages: list, max_tokens: int = None, temperature: float = None) -> Optional[str]:
        """Отправляет запрос к LLM API"""
        if not self.api_key:
            logger.error("API ключ не настроен")
            return None

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/pmixail88/hh-bot",
            "X-Title": "HH Work Day Bot",
        }

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:

                    if response.status == 200:
                        data = await response.json()

                        # Извлекаем ответ из различных форматов
                        if "choices" in data and len(data["choices"]) > 0:
                            if "message" in data["choices"][0]:
                                return data["choices"][0]["message"]["content"].strip()
                            elif "text" in data["choices"][0]:
                                return data["choices"][0]["text"].strip()
                        elif "text" in data:
                            return data["text"].strip()
                        elif "response" in data:
                            return data["response"].strip()
                        else:
                            logger.error(f"Неожиданный формат ответа: {data}")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {response.status} - {error_text}")
                        return None

        except aiohttp.ClientError as e:
            logger.error(f"Ошибка подключения: {e}")
            return None
        except asyncio.TimeoutError:
            logger.error("Таймаут при запросе к LLM")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return None

    async def generate_resume(
        self, user_profile: Dict, vacancy_info: Dict, llm_settings: Dict = None
    ) -> Optional[str]:
        """Генерация резюме с использованием LLM"""
        settings = llm_settings or {}
        api_key = settings.get("api_key") or self.api_key

        if not api_key:
            logger.info("API ключ не настроен, использую шаблон")
            return self._get_template_resume(user_profile, vacancy_info)

        cache_key = f"resume:{hash(str(user_profile))}:{hash(str(vacancy_info))}"

        cached = await self.cache.get(cache_key)
        if cached:
            logger.info("✅ Найдено резюме в кэше")
            return cached

        try:
            prompt = self._create_resume_prompt(user_profile, vacancy_info)

            call_settings = {
                "api_key": api_key,
                "model_name": settings.get("model_name", self.model_name),
                "base_url": settings.get("base_url", self.base_url),
                "temperature": settings.get("temperature", self.temperature),
                "max_tokens": settings.get("max_tokens", self.max_tokens),
            }

            result = await self._call_llm_api(prompt, call_settings)

            if result:
                await self.cache.set(cache_key, result, expire=3600)
                return result
            return self._get_template_resume(user_profile, vacancy_info)

        except Exception as e:
            logger.error(f"❌ Ошибка при генерации резюме: {e}")
            return self._get_template_resume(user_profile, vacancy_info)

    async def generate_cover_letter(
        self, user_profile: Dict, vacancy_info: Dict, llm_settings: Dict = None
    ) -> Optional[str]:
        """Генерация сопроводительного письма"""
        settings = llm_settings or {}
        api_key = settings.get("api_key") or self.api_key

        if not api_key:
            logger.info("API ключ не настроен, использую шаблон")
            return self._get_template_cover_letter(user_profile, vacancy_info)

        cache_key = f"cover_letter:{hash(str(user_profile))}:{hash(str(vacancy_info))}"

        cached = await self.cache.get(cache_key)
        if cached:
            logger.info("✅ Найдено сопроводительное письмо в кэше")
            return cached

        try:
            prompt = self._create_cover_letter_prompt(user_profile, vacancy_info)

            call_settings = {
                "api_key": api_key,
                "model_name": settings.get("model_name", self.model_name),
                "base_url": settings.get("base_url", self.base_url),
                "temperature": settings.get("temperature", self.temperature),
                "max_tokens": settings.get("max_tokens", self.max_tokens),
            }

            result = await self._call_llm_api(prompt, call_settings)

            if result:
                await self.cache.set(cache_key, result, expire=3600)
                return result
            return self._get_template_cover_letter(user_profile, vacancy_info)

        except Exception as e:
            logger.error(f"❌ Ошибка при генерации сопроводительного письма: {e}")
            return self._get_template_cover_letter(user_profile, vacancy_info)

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
5. Объем: 500-1500 слов
6. Формат: чистый текст без разметки

Создай профессиональное резюме:
"""

    def _create_cover_letter_prompt(
        self, user_profile: Dict, vacancy_info: Dict
    ) -> str:
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
        """Вызов LLM API для OpenRouter"""
        try:
            api_key = llm_settings.get("api_key", self.api_key)
            base_url = llm_settings.get("base_url", self.base_url)
            model_name = llm_settings.get("model_name", self.model_name)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://t.me/hr_assistant_bot",
                "X-Title": "HR Assistant Bot",
            }

            data = {
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты профессиональный HR-консультант с опытом составления резюме и сопроводительных писем. Отвечай только на русском языке.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": llm_settings.get("temperature", self.temperature),
                "max_tokens": llm_settings.get("max_tokens", self.max_tokens),
                "top_p": 0.9,
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{base_url}/chat/completions", headers=headers, json=data
                ) as response:

                    response_text = await response.text()

                    if response.status == 200:
                        try:
                            result = json.loads(response_text)
                            logger.debug(f"LLM Response keys: {list(result.keys())}")

                            # OpenRouter может возвращать разный формат
                            if "choices" in result and len(result["choices"]) > 0:
                                return result["choices"][0]["message"]["content"]
                            elif (
                                "result" in result
                                and "alternatives" in result["result"]
                            ):
                                # Яндекс GPT формат
                                return result["result"]["alternatives"][0]["message"][
                                    "text"
                                ]
                            else:
                                logger.error(f"Неизвестный формат ответа: {result}")
                                return None
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Ошибка парсинга JSON: {e}, текст: {response_text[:200]}"
                            )
                            return None
                    else:
                        logger.error(
                            f"Ошибка LLM API: {response.status}, текст: {response_text[:500]}"
                        )
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

    def _get_template_resume(self, user_profile: Dict, vacancy_info: Dict) -> str:
        """Шаблонное резюме при недоступности API"""
        return f"""
{user_profile.get('full_name', 'Имя Фамилия')}
Город: {user_profile.get('city', 'Не указан')}
Телефон: [Ваш телефон]
Email: [Ваш email]

Цель: Замещение должности {vacancy_info.get('name', 'воспитателя')}

Опыт работы:
{user_profile.get('base_resume', 'Опыт работы в образовательной сфере.')}

Образование: [Ваше образование]

Навыки:
{user_profile.get('skills', 'Навыки работы с детьми, организация мероприятий, ведение документации')}

Дополнительная информация: [Ваша дополнительная информация]
"""

    def _get_template_cover_letter(self, user_profile: Dict, vacancy_info: Dict) -> str:
        """Шаблонное сопроводительное письмо"""
        return f"""
Уважаемые представители компании {vacancy_info.get('company_name', '')}!

Меня зовут {user_profile.get('full_name', 'Имя Фамилия')}, и я хотел(а) бы выразить свою заинтересованность в вакансии {vacancy_info.get('name', 'воспитателя')}.

Мой опыт работы включает: {user_profile.get('base_resume', 'работу с детьми')}. 
Я обладаю следующими навыки: {user_profile.get('skills', 'организация учебного процесса')}.

Буду рад(а) обсудить возможность сотрудничества на собеседовании.

С уважением,
{user_profile.get('full_name', 'Имя Фамилия')}
"""

    async def test_connection(self, llm_settings: Dict = None) -> bool:
        """Тестирование подключения к LLM API"""
        try:
            settings = llm_settings or {}
            api_key = settings.get("api_key") or self.api_key

            if not api_key:
                logger.warning("Нет API ключа для теста")
                return False

            test_prompt = "Ответь одним словом на русском: 'готов'"

            test_settings = {
                "api_key": api_key,
                "model_name": settings.get("model_name", self.model_name),
                "base_url": settings.get("base_url", self.base_url),
                "temperature": 0.1,
                "max_tokens": 10,
            }

            result = await self._call_llm_api(test_prompt, test_settings)
            return result is not None and "готов" in result.lower()

        except Exception as e:
            logger.error(f"Ошибка при тестировании LLM: {e}")
            return False


# Тестирование
async def test():
    """Тестирование LLM сервиса"""
    print("🧪 ТЕСТ LLM СЕРВИСА")
    print("=" * 50)

    try:
        # Получаем конфигурацию
        config = get_config()

        print(f"API ключ: {'✅ Есть' if config.llm.api_key else '❌ Нет'}")
        print(f"Модель: {config.llm.model_name}")
        print(f"Base URL: {config.llm.base_url}")

        if not config.llm.api_key:
            print("❌ API ключ не настроен в .env файле!")
            return

        # Создаем сервис с конфигурацией
        llm = LLMService(config.llm)

        # Тестируем подключение
        print("\n🔍 Тестирую подключение к LLM...")
        connected = await llm.test_connection()

        if connected:
            print("✅ Подключение к LLM: РАБОТАЕТ")

            # Простой тест
            print("\n🔍 Тестовый запрос...")
            test_messages = [
                {"role": "system", "content": "Ты полезный ассистент."},
                {"role": "user", "content": "Привет! Ответь очень коротко."},
            ]

            response = await llm._make_request(test_messages, max_tokens=30)
            if response:
                print(f"✅ Ответ LLM: {response}")
            else:
                print("❌ Нет ответа от LLM")

        else:
            print("❌ Подключение к LLM: НЕ РАБОТАЕТ")
            print("\n🔧 Проверьте:")
            print("1. API ключ в .env файле")
            print("2. Подключение к интернету")
            print("3. Что модель доступна: mistralai/mistral-7b-instruct:free")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Запускаем тест
    asyncio.run(test())
