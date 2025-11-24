import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bot.config import get_settings


class HHService:
    """
    Сервис для работы с API HH.ru
    """
    def __init__(self):
        self.base_url = "https://api.hh.ru"
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HH-Bot/1.0 (Educational Project)'
        })

    def search_vacancies(self, 
                        text: str = "",
                        city: str = "",
                        salary: Optional[int] = None,
                        employment: Optional[List[str]] = None,
                        experience: Optional[str] = None,
                        period: int = 3,
                        employer_type: Optional[str] = None,
                        company_size: Optional[str] = None) -> List[Dict]:
        """
        Поиск вакансий по заданным параметрам
        
        :param text: Текст поиска (должность)
        :param city: Город
        :param salary: Минимальная зарплата
        :param employment: Тип занятости (full', 'part', 'project', 'volunteer', 'probation')
        :param experience: Опыт работы (noExperience', 'between1And3', 'between3And6', 'moreThan6')
        :param period: Период публикации (в днях)
        :param employer_type: Тип работодателя ('direct' для прямых работодателей)
        :param company_size: Размер компании ('small', 'medium', 'large')
        :return: Список вакансий
        """
        params = {
            'text': text,
            'area': self.get_area_id(city) if city else None,
            'salary': salary,
            'experience': experience,
            'period': period,
            'page': 0,
            'per_page': 100  # Максимальное количество вакансий на странице
        }

        # Фильтр по типу занятости
        if employment:
            for i, emp_type in enumerate(employment):
                params[f'employment[{i}]'] = emp_type

        # Фильтр по типу работодателя
        if employer_type:
            params['employer_type'] = employer_type

        # Фильтр по размеру компании
        if company_size:
            params['employer_size'] = company_size

        # Убираем None-значения
        params = {k: v for k, v in params.items() if v is not None}

        vacancies = []
        page = 0

        # Запрашиваем все страницы
        while True:
            params['page'] = page
            response = self.session.get(f"{self.base_url}/vacancies", params=params)
            
            if response.status_code != 200:
                print(f"Ошибка при запросе вакансий: {response.status_code}")
                break

            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break

            for item in items:
                vacancy = self.parse_vacancy(item)
                if vacancy:
                    vacancies.append(vacancy)

            # Если достигли последней страницы, выходим
            if page >= data.get('pages', 1) - 1:
                break

            page += 1

        return vacancies

    def get_vacancy(self, vacancy_id: str) -> Optional[Dict]:
        """
        Получение информации о конкретной вакансии
        """
        response = self.session.get(f"{self.base_url}/vacancies/{vacancy_id}")
        
        if response.status_code != 200:
            return None

        return self.parse_vacancy(response.json())

    def get_area_id(self, city_name: str) -> Optional[str]:
        """
        Получение ID региона по названию города
        """
        response = self.session.get(f"{self.base_url}/suggests/area", params={'text': city_name})
        
        if response.status_code != 200:
            return None

        data = response.json()
        items = data.get('items', [])
        
        for item in items:
            if item.get('text', '').lower() == city_name.lower():
                return item.get('id')
        
        return None

    def parse_vacancy(self, raw_vacancy: Dict) -> Optional[Dict]:
        """
        Парсинг вакансии из сырого ответа API
        """
        try:
            salary = raw_vacancy.get('salary')
            employer = raw_vacancy.get('employer', {})

            published_at_str = raw_vacancy.get('published_at')
            if published_at_str:
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            else:
                published_at = datetime.utcnow()

            parsed_vacancy = {
                'id': raw_vacancy.get('id'),
                'title': raw_vacancy.get('name', ''),
                'company': employer.get('name', ''),
                'city': raw_vacancy.get('area', {}).get('name', ''),
                'salary_from': salary.get('from') if salary else None,
                'salary_to': salary.get('to') if salary else None,
                'salary_currency': salary.get('currency') if salary else None,
                'description': raw_vacancy.get('snippet', {}).get('requirement', ''),
                'url': raw_vacancy.get('alternate_url', ''),
                'published_at': published_at,
                'employer_id': employer.get('id', ''),
                'experience': raw_vacancy.get('experience', {}).get('name', ''),
                'employment': raw_vacancy.get('employment', {}).get('name', ''),
                'schedule': raw_vacancy.get('schedule', {}).get('name', '')
            }

            return parsed_vacancy
        except Exception as e:
            print(f"Ошибка при парсинге вакансии: {e}")
            return None