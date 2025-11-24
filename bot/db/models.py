from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    full_name = Column(String)
    city = Column(String)
    desired_position = Column(String)
    skills = Column(Text)  # JSON string
    base_resume = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationship with search filters
    search_filters = relationship("SearchFilter", back_populates="user")
    # Relationship with generated documents
    documents = relationship("GeneratedDocument", back_populates="user")


class SearchFilter(Base):
    __tablename__ = "search_filters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    position = Column(String)
    city = Column(String)
    min_salary = Column(Integer, nullable=True)
    metro_stations = Column(Text)  # JSON string for metro stations
    freshness_days = Column(Integer, default=3)  # How fresh the vacancies should be
    employment_types = Column(Text)  # JSON string for employment types
    experience_level = Column(String)  # Experience level required
    only_direct_employers = Column(Boolean, default=False)
    company_size = Column(String)  # small, medium, large
    only_top_companies = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationship
    user = relationship("User", back_populates="search_filters")


class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    hh_id = Column(String, unique=True, index=True)  # HH.ru vacancy ID
    title = Column(String)
    company = Column(String)
    city = Column(String)
    salary_from = Column(Integer, nullable=True)
    salary_to = Column(Integer, nullable=True)
    salary_currency = Column(String)
    description = Column(Text)
    url = Column(String)
    published_at = Column(DateTime)
    employer_id = Column(String)  # HH.ru employer ID
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with users who marked this vacancy
    user_vacancies = relationship("UserVacancy", back_populates="vacancy")


class UserVacancy(Base):
    __tablename__ = "user_vacancies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"))
    is_interesting = Column(Boolean, default=True)  # True if user didn't mark as "not interesting"
    viewed_at = Column(DateTime, default=datetime.utcnow)
    resume_generated = Column(Boolean, default=False)
    cover_letter_generated = Column(Boolean, default=False)

    # Relationships
    user = relationship("User")
    vacancy = relationship("Vacancy", back_populates="user_vacancies")


class LLMSettings(Base):
    __tablename__ = "llm_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    base_url = Column(String)
    api_key = Column(String)
    model_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User")


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"))
    document_type = Column(String)  # 'resume' or 'cover_letter'
    content = Column(Text)  # The generated document content
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
    vacancy = relationship("Vacancy")