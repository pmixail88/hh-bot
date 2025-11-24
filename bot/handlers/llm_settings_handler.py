from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.db.database import get_db
from bot.db.models import User, LLMSettings
from sqlalchemy.orm import Session


router = Router()


@router.message(Command("llm_settings"))
async def cmd_llm_settings(message: Message):
    """
    Обработчик команды /llm_settings
    Позволяет пользователю настроить параметры LLM для генерации резюме и сопроводительных писем
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        # Проверяем, существует ли пользователь
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Проверяем, есть ли у пользователя уже настройки LLM
        llm_settings = db.query(LLMSettings).filter(LLMSettings.user_id == user.id).first()
        
        if llm_settings:
            await message.answer(
                f"Ваши текущие настройки LLM:\n"
                f"Base URL: {llm_settings.base_url}\n"
                f"Model: {llm_settings.model_name}\n\n"
                f"Для изменения настроек используйте команды:\n"
                f"/set_llm_url - Установить URL для LLM API\n"
                f"/set_llm_key - Установить API ключ\n"
                f"/set_llm_model - Установить модель"
            )
        else:
            # Создаем новые настройки LLM для пользователя
            new_settings = LLMSettings(
                user_id=user.id,
                base_url="https://api.openai.com/v1",
                api_key="",
                model_name="gpt-4o"
            )
            
            db.add(new_settings)
            db.commit()
            
            await message.answer(
                f"Настройки LLM по умолчанию установлены.\n\n"
                f"Для настройки используйте команды:\n"
                f"/set_llm_url - Установить URL для LLM API\n"
                f"/set_llm_key - Установить API ключ\n"
                f"/set_llm_model - Установить модель"
            )
    
    finally:
        db.close()


@router.message(Command("set_llm_url"))
async def cmd_set_llm_url(message: Message):
    """
    Установка URL для LLM API
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        url = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not url:
            await message.answer("Пожалуйста, укажите URL после команды. Пример: /set_llm_url https://api.openai.com/v1")
            return
        
        # Проверяем, есть ли уже настройки LLM для пользователя
        llm_settings = db.query(LLMSettings).filter(LLMSettings.user_id == user.id).first()
        
        if llm_settings:
            llm_settings.base_url = url
            db.commit()
            await message.answer(f"URL для LLM API установлен: {url}")
        else:
            await message.answer("Сначала настройте LLM с помощью команды /llm_settings")
    
    finally:
        db.close()


@router.message(Command("set_llm_key"))
async def cmd_set_llm_key(message: Message):
    """
    Установка API ключа для LLM
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        api_key = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not api_key:
            await message.answer("Пожалуйста, укажите API ключ после команды. Пример: /set_llm_key sk-...")
            return
        
        # Проверяем, есть ли уже настройки LLM для пользователя
        llm_settings = db.query(LLMSettings).filter(LLMSettings.user_id == user.id).first()
        
        if llm_settings:
            llm_settings.api_key = api_key
            db.commit()
            await message.answer("API ключ для LLM установлен")
        else:
            await message.answer("Сначала настройте LLM с помощью команды /llm_settings")
    
    finally:
        db.close()


@router.message(Command("set_llm_model"))
async def cmd_set_llm_model(message: Message):
    """
    Установка модели для LLM
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        model = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not model:
            await message.answer("Пожалуйста, укажите модель после команды. Пример: /set_llm_model gpt-4o")
            return
        
        # Проверяем, есть ли уже настройки LLM для пользователя
        llm_settings = db.query(LLMSettings).filter(LLMSettings.user_id == user.id).first()
        
        if llm_settings:
            llm_settings.model_name = model
            db.commit()
            await message.answer(f"Модель для LLM установлена: {model}")
        else:
            await message.answer("Сначала настройте LLM с помощью команды /llm_settings")
    
    finally:
        db.close()