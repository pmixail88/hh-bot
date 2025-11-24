from bot.services.hh_service import HHService

def test_hh_service():
    print("Тестирование HH сервиса...")
    
    hh_service = HHService()
    
    try:
        # Попробуем найти вакансии
        print("Поиск вакансий по ключевому слову 'python'...")
        vacancies = hh_service.search_vacancies(text="python", city="Москва", salary=100000)
        
        print(f"Найдено вакансий: {len(vacancies)}")
        
        if vacancies:
            # Выведем информацию о первой вакансии
            first_vacancy = vacancies[0]
            print(f"Первая вакансия: {first_vacancy['title']} в {first_vacancy['company']}")
            print(f"Зарплата: {first_vacancy.get('salary_from')} - {first_vacancy.get('salary_to')} {first_vacancy.get('salary_currency')}")
            print(f"Город: {first_vacancy['city']}")
            print(f"URL: {first_vacancy['url']}")
        else:
            print("Вакансии не найдены. Это может быть связано с ограничениями API HH.ru.")
            
    except Exception as e:
        print(f"Ошибка при работе с HH сервисом: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hh_service()