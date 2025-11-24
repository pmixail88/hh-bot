from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from bot.db.database import get_db
from bot.db.models import User
from sqlalchemy.orm import Session


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    Создает профиль пользователя
    """
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    # Проверяем, существует ли уже пользователь
    db: Session = next(get_db())
    
    existing_user = db.query(User).filter(User.telegram_id == str(user_id)).first()
    
    if existing_user:
        await message.answer(
            f"Привет, {full_name}! Вы уже зарегистрированы в боте.\n"
            f"Для настройки поиска вакансий используйте команду /search_settings\n"
            f"Для просмотра вакансий используйте команду /vacancies"
        )
    else:
        # Создаем нового пользователя
        new_user = User(
            telegram_id=str(user_id),
            full_name=full_name,
            city="",
            desired_position="",
            skills="",
            base_resume=""
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        await message.answer(
            f"Привет, {full_name}! Добро пожаловать в бот поиска вакансий HH.ru!\n\n"
            f"Для начала настройте параметры поиска с помощью команды /search_settings\n"
            f"Команды бота:\n"
            f"/search_settings - Настройка фильтров поиска вакансий\n"
            f"/vacancies - Просмотр подходящих вакансий\n"
            f"/my_profile - Просмотр и редактирование профиля\n"
            f"/llm_settings - Настройка параметров генерации резюме и сопроводительных писем"
        )
    
    db.close()