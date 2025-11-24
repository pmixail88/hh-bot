import asyncio
from bot.utils.scheduler import VacancyScheduler
from bot.db.database import get_db
from bot.db.models import User, SearchFilter
from aiogram import Bot
from sqlalchemy.orm import Session

async def test_scheduler():
    print("Тестирование планировщика...")
    
    # Создаем фейковый бот для тестирования
    # В реальности нужно использовать реальный токен, но для теста базовой функциональности
    # можно использовать заглушку или пропустить отправку сообщений
    fake_bot = Bot(token="7721173847:AAGaR_Qs6TzzXIrgRASZNYc0jj2FrDhLjCc")  # Это реальный токен из .env
    
    scheduler = VacancyScheduler(fake_bot)
    
    db: Session = next(get_db())
    try:
        # Создадим тестового пользователя с фильтром поиска
        user = User(
            telegram_id="112334455",
            full_name="Scheduler Test User",
            city="Москва",
            desired_position="Python Developer",
            skills='{"python": 5}',
            base_resume="Test scheduler resume"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Создадим фильтр поиска для пользователя
        search_filter = SearchFilter(
            user_id=user.id,
            position="python",
            city="Москва",
            min_salary=100000,
            freshness_days=1,
            is_active=True
        )
        db.add(search_filter)
        db.commit()
        
        print(f"Создан пользователь с ID: {user.id} и фильтром поиска")
        
        # Прямо вызовем метод проверки новых вакансий
        await scheduler.check_new_vacancies()
        
        # Проверим, сколько вакансий теперь связано с пользователем
        from bot.db.models import UserVacancy, Vacancy
        user_vacancies = db.query(UserVacancy).filter(UserVacancy.user_id == user.id).all()
        print(f"Количество вакансий, связанных с пользователем: {len(user_vacancies)}")
        
        # Проверим общее количество вакансий в базе
        total_vacancies = db.query(Vacancy).count()
        print(f"Общее количество вакансий в базе: {total_vacancies}")
        
    except Exception as e:
        print(f"Ошибка при тестировании планировщика: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_scheduler())