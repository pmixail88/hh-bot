from bot.services.hh_service import HHService
from bot.db.database import get_db
from bot.db.models import Vacancy, User, UserVacancy
from sqlalchemy.orm import Session

def test_vacancy_storage():
    print("Тестирование сохранения вакансий в базу данных...")
    
    db: Session = next(get_db())
    try:
        # Создадим тестового пользователя
        user = User(
            telegram_id="987654321",
            full_name="Test Bot User",
            city="Москва",
            desired_position="Python Developer",
            skills='{"python": 5}',
            base_resume="Test bot resume"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"Создан пользователь с ID: {user.id}")
        
        # Получим вакансии через HH сервис
        hh_service = HHService()
        vacancies_data = hh_service.search_vacancies(text="python", city="Москва", salary=100000, period=1)
        
        print(f"Получено вакансий из HH: {len(vacancies_data)}")
        
        # Сохраним вакансии в базу данных
        saved_count = 0
        for vacancy_data in vacancies_data[:5]:  # Сохраним только первые 5 для тестирования
            # Проверим, существует ли уже вакансия
            existing_vacancy = db.query(Vacancy).filter(Vacancy.hh_id == vacancy_data['id']).first()
            
            if not existing_vacancy:
                new_vacancy = Vacancy(
                    hh_id=vacancy_data['id'],
                    title=vacancy_data['title'],
                    company=vacancy_data['company'],
                    city=vacancy_data['city'],
                    salary_from=vacancy_data['salary_from'],
                    salary_to=vacancy_data['salary_to'],
                    salary_currency=vacancy_data['salary_currency'],
                    description=vacancy_data['description'],
                    url=vacancy_data['url'],
                    published_at=vacancy_data['published_at'],
                    employer_id=vacancy_data['employer_id']
                )
                
                db.add(new_vacancy)
                db.flush()  # Чтобы получить ID вакансии
                
                # Создадим связь с пользователем
                user_vacancy = UserVacancy(
                    user_id=user.id,
                    vacancy_id=new_vacancy.id,
                    is_interesting=True
                )
                
                db.add(user_vacancy)
                saved_count += 1
        
        db.commit()
        
        print(f"Сохранено новых вакансий: {saved_count}")
        
        # Проверим, что вакансии действительно сохранены
        user_vacancies = db.query(UserVacancy).filter(UserVacancy.user_id == user.id).all()
        print(f"Связей пользователь-вакансия в базе: {len(user_vacancies)}")
        
        # Проверим общее количество вакансий
        total_vacancies = db.query(Vacancy).count()
        print(f"Общее количество вакансий в базе: {total_vacancies}")
        
    except Exception as e:
        print(f"Ошибка при сохранении вакансий: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_vacancy_storage()