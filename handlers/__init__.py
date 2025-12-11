from .base import router as base_router
from .profile import router as profile_router
from .search2 import router as search_router
from .vacancies import router as vacancies_router
from .llm import router as llm_router
from .responses import router as responses_router
from .hh_api import router as hh_api_router# Добавляем новый роутер
from aiogram import Router


# Главный роутер
router = Router()

# Включаем все роутеры
router.include_router(base_router)
router.include_router(profile_router)
router.include_router(search_router)
router.include_router(vacancies_router)
router.include_router(llm_router)
router.include_router(responses_router) 
router.include_router(hh_api_router)# Добавляем

__all__ = ['router']