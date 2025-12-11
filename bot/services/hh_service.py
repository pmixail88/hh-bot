import aiohttp
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode
import re

from core.config import HHConfig
from services.cache import CacheService

logger = logging.getLogger(__name__)

class HHService:
    def __init__(self, config: HHConfig):
        self.config = config
        self.base_url = "https://api.hh.ru"
        self.cache = CacheService()
        self.timeout = aiohttp.ClientTimeout(total=config.timeout)
        self.areas_cache = {}
        self.semaphore = asyncio.Semaphore(5)
        
        # Кэш для ID регионов
        #self.areas_cache = {}

    async def search_vacancies(self, search_filter: Any) -> List[Dict]:
        """Поиск вакансий с кэшированием и обработкой ошибок"""
        cache_key = f"vacancies:{self._get_filter_hash(search_filter)}"
        
        # Кэшируем на 30 минут вместо 10 and Пробуем получить из кэша
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"✅ Найдено {len(cached)} вакансий в кэше")
            return cached
        
        
        try:
            params = await self._build_search_params(search_filter)
            vacancies = []
            
            logger.info(f"🔍 Поиск с параметрами: {params}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Получаем первую страницу для определения общего количества
                #data = await self._fetch_page(session, params, 0)
                # Получаем первую страницу
                async with self.semaphore:  # Ограничиваем параллелизм
                    data = await self._fetch_page(session, params, 0)
                    
                if not data:
                    logger.info("❌ Нет данных от HH API")
                    return []
                
                items = data.get('items', [])
                logger.info(f"📄 Найдено {len(items)} вакансий на первой странице")
                vacancies.extend(items)
                
                total_pages = data.get('pages', 1)
                found = data.get('found', 0)
                logger.info(f"📊 Всего найдено: {found} вакансий, страниц: {total_pages}")
                
                # Ограничиваем количество страниц для производительности
                pages_to_fetch = min(total_pages, 10)  # Увеличили до 10 страниц
                
                # Собираем задачи для параллельного выполнения
                tasks = [
                    self._fetch_page(session, params, page) 
                    for page in range(1, pages_to_fetch)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, dict):
                        page_items = result.get('items', [])
                        vacancies.extend(page_items)
                        logger.info(f"📄 Добавлено {len(page_items)} вакансий с страницы")
                
                # Ограничиваем общее количество
                vacancies = vacancies[:self.config.max_results]
                logger.info(f"📦 Итого собрано {len(vacancies)} вакансий")
                
                # Парсим вакансии
                parsed_vacancies = []
                parse_errors = 0
                
                for vacancy_data in vacancies:
                    parsed = self._parse_vacancy(vacancy_data)
                    if parsed:
                        parsed_vacancies.append(parsed)
                    else:
                        parse_errors += 1
                
                logger.info(f"✅ Успешно распарсено {len(parsed_vacancies)} вакансий, ошибок: {parse_errors}")
                
                # Кэшируем на 15 минут
                #await self.cache.set(cache_key, parsed_vacancies, expire=600) - 10 минут
                if parsed_vacancies:
                    await self.cache.set(cache_key, parsed_vacancies, expire=1200)
                return parsed_vacancies
                
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске вакансий: {e}")
            return []

    async def _build_search_params(self, search_filter: Any) -> Dict[str, Any]:
        """Построение параметров запроса для HH API"""
        params = {
            'per_page': 100,  # Максимальное количество на странице
            'page': 0,
            'order_by': 'publication_time',  # Сначала новые
            'search_field': 'name'  # Искать в названии
        }
        
        # Ключевые слова - обязательный параметр
        if search_filter.keywords and search_filter.keywords.strip():
            params['text'] = search_filter.keywords.strip()
        else:
            # Если ключевые слова не указаны, ищем популярные профессии
            params['text'] = "разработчик программист"
        
        # Регион
        if search_filter.region and search_filter.region.strip():
            area_id = await self._get_area_id(search_filter.region.strip())
            if area_id:
                params['area'] = area_id
            else:
                # Если регион не найден, используем Россию
                params['area'] = 113  # Россия
        else:
            params['area'] = 113  # Россия по умолчанию
        
        # Зарплата
        if search_filter.salary_from:
            params['salary'] = search_filter.salary_from
            params['only_with_salary'] = True
        
        # Опыт работы
        if search_filter.experience:
            experience_map = {
                'нет опыта': 'noExperience',
                'от 1 года': 'between1And3', 
                'от 3 лет': 'between3And6',
                'от 6 лет': 'moreThan6'
            }
            params['experience'] = experience_map.get(
                search_filter.experience.lower().strip(), 
                search_filter.experience
            )
        
        # Тип занятости
        if search_filter.employment:
            employment_map = {
                'полная занятость': 'full',
                'частичная занятость': 'part',
                'проектная работа': 'project',
                'волонтерство': 'volunteer',
                'стажировка': 'probation'
            }
            params['employment'] = employment_map.get(
                search_filter.employment.lower().strip(),
                search_filter.employment
            )
        
        # График работы
        if search_filter.schedule:
            schedule_map = {
                'полный день': 'fullDay',
                'сменный график': 'shift',
                'гибкий график': 'flexible',
                'удаленная работа': 'remote',
                'вахтовый метод': 'flyInFlyOut'
            }
            params['schedule'] = schedule_map.get(
                search_filter.schedule.lower().strip(),
                search_filter.schedule
            )
        
        # Период публикации (по умолчанию 1 день)
        params['period'] = search_filter.period or 1
        
        # Очищаем от пустых значений
        clean_params = {k: v for k, v in params.items() if v is not None and v != ''}
        logger.info(f"🔄 Параметры поиска: {clean_params}")
        
        return clean_params

    async def _fetch_page(self, session: aiohttp.ClientSession, params: Dict, page: int) -> Optional[Dict]:
        """Запрос одной страницы с вакансиями"""
        try:
            params['page'] = page
            # Очищаем параметры от None значений
            clean_params = {k: v for k, v in params.items() if v is not None}
            
            async with session.get(f"{self.base_url}/vacancies", params=clean_params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.debug(f"❌ Ошибка HH API: {response.status} для параметров {clean_params}")
                    return None
        except asyncio.TimeoutError:
            logger.debug("⏰ Таймаут при запросе вакансий")
            return None
        except Exception as e:
            logger.debug(f"❌ Ошибка при запросе вакансий: {e}")
            return None

    async def _get_area_id(self, region_name: str) -> Optional[str]:
        """Получить ID региона по названию с кэшированием"""
        if region_name in self.areas_cache:
            return self.areas_cache[region_name]
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/suggests/areas",
                    params={'text': region_name}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('items'):
                            area_id = data['items'][0]['id']
                            self.areas_cache[region_name] = area_id
                            return area_id
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске региона {region_name}: {e}")
        
        return None

    def _parse_vacancy(self, raw_vacancy: Dict) -> Optional[Dict]:
        """Парсинг данных вакансии из HH API"""
        try:
            # Проверяем, что raw_vacancy не None и содержит необходимые поля
            if not raw_vacancy or 'id' not in raw_vacancy:
                logger.debug("❌ Пустая вакансия или отсутствует ID")
                return None
            
            salary = raw_vacancy.get('salary', {}) or {}
            employer = raw_vacancy.get('employer', {}) or {}
            area = raw_vacancy.get('area', {}) or {}
            snippet = raw_vacancy.get('snippet', {}) or {}
            
            # Проверяем обязательные поля
            if not employer.get('name') or not raw_vacancy.get('name'):
                logger.debug("❌ Отсутствует название компании или вакансии")
                return None
            
            # Обработка даты публикации
            published_at = None
            if raw_vacancy.get('published_at'):
                try:
                    published_str = raw_vacancy['published_at'].replace('Z', '+00:00')
                    #published_at = datetime.fromisoformat(published_str)
                    published_at = datetime.utcnow()
                except ValueError:
                    published_at = datetime.utcnow()
            else:
                published_at = datetime.utcnow()
            
            # Формирование описания
            requirement = snippet.get('requirement', '') or ''
            responsibility = snippet.get('responsibility', '') or ''

            description_parts = []
            if requirement:
                # Убираем HTML теги если есть
                requirement = re.sub('<[^<]+?>', '', requirement)  # ✅ re уже импортирован
                description_parts.append(f"Требования: {requirement}")
            if responsibility:
                responsibility = re.sub('<[^<]+?>', '', responsibility)  # ✅ re уже импортирован
                description_parts.append(f"Обязанности: {responsibility}")

            description = ' '.join(description_parts)
            
            if len(description) > 2000:
                description = description[:2000] + "..."
            elif not description:
                description = "Описание не указано"
            
            parsed = {
                'hh_id': raw_vacancy['id'],
                'name': raw_vacancy.get('name', 'Без названия').strip(),
                'company_name': employer.get('name', 'Не указано').strip(),
                'area_name': area.get('name', 'Не указан'),
                'salary_from': salary.get('from'),
                'salary_to': salary.get('to'),
                'salary_currency': salary.get('currency'),
                'salary_gross': salary.get('gross'),
                'experience': raw_vacancy.get('experience', {}).get('name'),
                'schedule': raw_vacancy.get('schedule', {}).get('name'),
                'employment': raw_vacancy.get('employment', {}).get('name'),
                'description': description,
                'skills': '',
                'url': raw_vacancy.get('alternate_url', ''),
                'published_at': published_at,
                #'employer_id': employer.get('id')
            }
            
            logger.debug(f"✅ Успешно распарсена вакансия: {parsed['name']}")
            return parsed
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга вакансии {raw_vacancy.get('id', 'unknown')}: {e}")
            return None

    def _get_filter_hash(self, search_filter: Any) -> str:
        """Создание хэша для кэширования на основе параметров фильтра"""
        params = [
            search_filter.keywords or '',
            search_filter.region or '',
            str(search_filter.salary_from or ''),
            str(search_filter.salary_to or ''),
            search_filter.experience or '',
            search_filter.employment or '',
            search_filter.schedule or '',
            str(search_filter.period or '')
        ]
        return str(hash(''.join(params)))

    async def check_vacancy_archived(self, vacancy_id: str) -> bool:
        """Проверка, архивирована ли вакансия"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/vacancies/{vacancy_id}") as response:
                    return response.status == 404  # Если 404 - вакансия архивирована
        except Exception:
            return True

    async def test_connection(self) -> bool:
        """Тестирование подключения к HH API"""
        try:
            async with aiohttp.ClientSession(timeout=10) as session:
                async with session.get(f"{self.base_url}/vacancies", params={'text': 'test'}) as response:
                    return response.status == 200
        except Exception:
            return False