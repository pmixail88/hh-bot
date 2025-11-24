from bot.db.database import get_db
from bot.db.models import User
from sqlalchemy.orm import Session

def test_user_insertion():
    print("Тестирование добавления пользователя в базу данных...")
    
    db: Session = next(get_db())
    try:
        # Создаем нового пользователя
        new_user = User(
            telegram_id="123456789",
            full_name="Test User",
            city="Moscow",
            desired_position="Developer",
            skills='{"python": 5, "sql": 4}',
            base_resume="Test resume content"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"Пользователь успешно добавлен с ID: {new_user.id}")
        
        # Проверяем, что пользователь действительно добавлен
        user_from_db = db.query(User).filter(User.telegram_id == "123456789").first()
        if user_from_db:
            print(f"Пользователь найден в базе: {user_from_db.full_name}")
        else:
            print("Пользователь не найден в базе")
            
        # Подсчитываем общее количество пользователей
        user_count = db.query(User).count()
        print(f"Общее количество пользователей в базе: {user_count}")
        
    except Exception as e:
        print(f"Ошибка при добавлении пользователя: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_user_insertion()