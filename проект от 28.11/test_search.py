import asyncio
import sys
import os
import logging
sys.path.append(os.path.dirname(__file__))

# Включаем подробное логирование
logging.basicConfig(level=logging.INFO)

from core.config import get_config
from services.hh_service import HHService
from database.models import SearchFilter

async def test_search():
    config = get_config()
    hh_service = HHService(config.hh)
    
    # Тестовые фильтры
    test_filters = [
        SearchFilter(keywords="Python", region="Москва", period=7),
        SearchFilter(keywords="разработчик", region="Санкт-Петербург", period=7),
        SearchFilter(keywords="программист", region="", period=7),  # Вся Россия
        SearchFilter(keywords="", region="Москва", period=1),  # Без ключевых слов
    ]
    
    for i, test_filter in enumerate(test_filters, 1):
        print(f"\n🔍 Тест {i}: {test_filter.keywords or 'без ключевых'} в {test_filter.region or 'России'}")
        
        vacancies = await hh_service.search_vacancies(test_filter)
        
        if vacancies:
            print(f"✅ Найдено {len(vacancies)} вакансий:")
            for j, vacancy in enumerate(vacancies[:5], 1):
                print(f"   {j}. {vacancy['name'][:50]}...")
                print(f"      Компания: {vacancy['company_name']}")
                print(f"      Город: {vacancy['area_name']}")
                salary = f"{vacancy['salary_from'] or '?'} - {vacancy['salary_to'] or '?'}"
                print(f"      Зарплата: {salary}")
                print()
        else:
            print("❌ Вакансии не найдены")

if __name__ == "__main__":
    asyncio.run(test_search())