from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, BigInteger, Float
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    username = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True, default="Санкт-Петербург")
    desired_position = Column(String(200), nullable=True)
    skills = Column(Text, nullable=True)
    base_resume = Column(Text, nullable=True)
    
    # Исходные контактные поля (для обратной совместимости)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    hh_resume_id = Column(String(100), nullable=True)
    
    # Срок действия токенов HH
    hh_token_expires = Column(DateTime, nullable=True)  # Убедиться что тип DateTime
    
    # БАЗОВЫЕ ПОЛЯ ШИФРОВАНИЯ
    encryption_key = Column(String(500), nullable=True)  # Основной ключ шифрования
    encryption_salt = Column(String(100), nullable=True)  # Соль для генерации ключа
    hh_encryption_key = Column(String(100), nullable=True)  # Добавить после encryption_salt
    data_integrity_hash = Column(String(200), nullable=True)  # Хеш для проверки целостности
    
    # HH API - зашифрованные поля
    hh_client_id_encrypted = Column(String(500), nullable=True)
    hh_client_secret_encrypted = Column(String(500), nullable=True)
    hh_access_token_encrypted = Column(String(500), nullable=True)
    hh_refresh_token_encrypted = Column(String(500), nullable=True)
    
    # LLM API - зашифрованные поля
    llm_api_key_encrypted = Column(String(500), nullable=True)
    llm_base_url_encrypted = Column(String(500), nullable=True)
    
    # Контактная информация - зашифрованные поля
    contact_email_encrypted = Column(String(500), nullable=True)
    contact_phone_encrypted = Column(String(500), nullable=True)
    
    # Настройки планировщика
    scheduler_enabled = Column(Boolean, default=True)
    scheduler_times = Column(String(100), default="09:00,18:00")
    check_interval_hours = Column(Integer, default=24)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    search_filters = relationship("SearchFilter", back_populates="user", cascade="all, delete-orphan")
    user_vacancies = relationship("UserVacancy", back_populates="user")
    llm_settings = relationship("LLMSettings", back_populates="user", uselist=False)
    generated_resumes = relationship("GeneratedResume", back_populates="user", cascade="all, delete-orphan")
    cover_letters = relationship("CoverLetter", back_populates="user", cascade="all, delete-orphan")

class SearchFilter(Base):
    __tablename__ = "search_filters"
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False, default="Основной")
    
    # Параметры поиска
    keywords = Column(String(500), nullable=True)
    region = Column(String(100), nullable=True, default="Санкт-Петербург")
    salary_from = Column(Integer, nullable=True)
    salary_to = Column(Integer, nullable=True)
    experience = Column(String(50), nullable=True)  # noExperience, between1And3, etc.
    employment = Column(String(50), nullable=True)  # full, part, project, etc.
    schedule = Column(String(50), nullable=True)    # fullDay, shift, flexible, etc.
    
    # Дополнительные параметры
    only_with_salary = Column(Boolean, default=False)
    search_radius = Column(Integer, default=0)  # в км
    period = Column(Integer, default=1)  # дни для поиска
    
    is_active = Column(Boolean, default=True)
    last_checked = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="search_filters")

class Vacancy(Base):
    __tablename__ = "vacancies"
    
    id = Column(BigInteger, primary_key=True)
    hh_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Основная информация
    name = Column(String(500), nullable=False)
    company_name = Column(String(300), nullable=False)
    area_name = Column(String(100), nullable=True)
    
    # Зарплата
    salary_from = Column(Integer, nullable=True)
    salary_to = Column(Integer, nullable=True)
    salary_currency = Column(String(10), nullable=True)
    salary_gross = Column(Boolean, nullable=True)
    
    # Условия
    experience = Column(String(100), nullable=True)
    schedule = Column(String(100), nullable=True)
    employment = Column(String(100), nullable=True)
    
    # Описание
    description = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    url = Column(String(500), nullable=False)
    
    # Статусы
    is_archived = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # В класс Vacancy добавить в конец:
    generated_resumes = relationship("GeneratedResume", back_populates="vacancy")
    cover_letters = relationship("CoverLetter", back_populates="vacancy")

class UserVacancy(Base):
    __tablename__ = "user_vacancies"
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(BigInteger, ForeignKey("vacancies.id"), nullable=False)
    
    # Статусы пользователя
    is_saved = Column(Boolean, default=True)
    is_applied = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    is_viewed = Column(Boolean, default=False)
    
    notes = Column(Text, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="user_vacancies")
    vacancy = relationship("Vacancy")

class LLMSettings(Base):
    __tablename__ = "llm_settings"
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Настройки API
    provider = Column(String(50), default="openai")
    api_key = Column(String(500), nullable=True)
    base_url = Column(String(500), default="https://api.openai.com/v1")
    model_name = Column(String(100), default="gpt-4o")
    
    # Параметры генерации
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    
    # Включенные функции
    enable_resume_generation = Column(Boolean, default=True)
    enable_cover_letter_generation = Column(Boolean, default=True)
    enable_vacancy_analysis = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="llm_settings")
    
# Добавить новую модель для хранения сгенерированных резюме
class GeneratedResume(Base):
    """Сгенерированные резюме под конкретные вакансии"""
    __tablename__ = "generated_resumes"
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(BigInteger, ForeignKey("vacancies.id"), nullable=False)
    title = Column(String(200), nullable=False, default="Адаптированное резюме")
    content = Column(Text, nullable=False)
    hh_resume_id = Column(String(100), nullable=True)  # ID на HH если загружено
    is_uploaded_to_hh = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="generated_resumes")
    vacancy = relationship("Vacancy", back_populates="generated_resumes")

class CoverLetter(Base):
    """Сопроводительные письма для вакансий"""
    __tablename__ = "cover_letters"
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(BigInteger, ForeignKey("vacancies.id"), nullable=False)
    title = Column(String(200), nullable=False, default="Сопроводительное письмо")
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="cover_letters")
    vacancy = relationship("Vacancy", back_populates="cover_letters")
