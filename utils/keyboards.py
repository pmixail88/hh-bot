from typing import Optional, List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database.models import Vacancy
# УДАЛИТЬ весь код с router и обработчиками! Только функции клавиатур

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Обновленная клавиатура главного меню"""
    keyboard = [
        [
            InlineKeyboardButton(text="🔍 Поиск вакансий", callback_data="menu_vacancies"),
            InlineKeyboardButton(text="⚙️ Настройки поиска", callback_data="menu_search_settings")
        ],
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu_profile"),
            InlineKeyboardButton(text="💼 Новые вакансии", callback_data="menu_vacancies")
        ],
        [
            InlineKeyboardButton(text="📂 Мои вакансии", callback_data="menu_my_vacancies")
        ],
        [
            InlineKeyboardButton(text="🤖 AI Помощник", callback_data="menu_llm_settings"),
            InlineKeyboardButton(text="🔐 HH API", callback_data="hh_api_settings")
            
        ],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="menu_help"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в меню"""
    keyboard = [
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_search_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек поиска"""
    keyboard = [
        [
            InlineKeyboardButton(text="📝 Ключевые слова", callback_data="settings_keywords"),
            InlineKeyboardButton(text="🌍 Регион", callback_data="settings_region")
        ],
        [
            InlineKeyboardButton(text="💰 Зарплата от", callback_data="settings_salary_from"),
            InlineKeyboardButton(text="💰 Зарплата до", callback_data="settings_salary_to")
        ],
        [
            InlineKeyboardButton(text="🎯 Опыт", callback_data="settings_experience"),
            InlineKeyboardButton(text="📋 График", callback_data="settings_schedule")
        ],
        [
            InlineKeyboardButton(text="📅 Период", callback_data="settings_period"),
            InlineKeyboardButton(text="🔄 Сбросить все", callback_data="settings_reset_all")
        ],
        [
            InlineKeyboardButton(text="💾 Сохранить", callback_data="settings_save"),
            InlineKeyboardButton(text="🔍 НАЧАТЬ ПОИСК", callback_data="menu_search_vacancies")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pagination_keyboard(current_page: int, total_pages: int, vacancy_id=Vacancy.id, show_actions: bool = False) -> InlineKeyboardMarkup:   
    """Клавиатура пагинации для вакансий (Уровень 2)"""
    buttons = []
    
    # Кнопки навигации
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Предыдущая", callback_data=f"page_{current_page-1}"))
    
    # Кнопка номера страницы
    nav_buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="show_current_page"))
    
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Следующая ▶️", callback_data=f"page_{current_page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    # ВАЖНО: Кнопка перехода на Уровень 3 ДОЛЖНА содержать vacancy_id!
    if vacancy_id:
        buttons.append([
            InlineKeyboardButton(
                text="📤 Откликнуться на вакансию", 
                callback_data=f"vacancy_response_{vacancy_id}"  # <-- ИСПРАВЛЕНО!
            )
        ])
    
    # Основные кнопки
    main_buttons = []
    
    main_buttons.append(InlineKeyboardButton(text="🔍 Новый поиск", callback_data="menu_vacancies"))
    
    main_buttons.append(InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main"))
    
    buttons.append(main_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_response_vacancy_keyboard(vacancy_id: int, user_id: int, is_favorite: bool = False, has_resume: bool = False, has_letter: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для экрана отклика на вакансию (одна вакансия)"""
    
    buttons = []
    
    # 1. Добавить в избранное / убрать из избранного
    favorite_text = "⭐ Убрать из избранного" if is_favorite else "⭐ Добавить в избранное"
    buttons.append([
        InlineKeyboardButton(
            text=favorite_text,
            callback_data=f"vacancy_favorite_{vacancy_id}"
        )
    ])
    
    # 2. Сгенерировать резюме под вакансию
    resume_text = "📝 Редактировать резюме" if has_resume else "📝 Сгенерировать резюме под вакансию"
    buttons.append([
        InlineKeyboardButton(
            text=resume_text,
            callback_data=f"generate_resume_{vacancy_id}"
        )
    ])
    
    # 3. Сгенерировать сопроводительное письмо
    letter_text = "✉️ Редактировать письмо" if has_letter else "✉️ Сгенерировать сопроводительное письмо"
    buttons.append([
        InlineKeyboardButton(
            text=letter_text,
            callback_data=f"generate_letter_{vacancy_id}"
        )
    ])
    
    # 4. Откликнуться (основная кнопка)
    buttons.append([
        InlineKeyboardButton(
            text="📤 Отправить отклик на вакансию на HH.ru",
            callback_data=f"send_response_{vacancy_id}"
        )
    ])
    
    # 5. Назад к списку вакансий
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Назад к вакансиям",
            callback_data="vacancy_back_to_list"
        )
    ])
    
    # 6. Главное меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="menu_main"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_single_vacancy_keyboard(vacancy_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для единичного показа вакансии"""
    buttons = []
    
    # 1. Добавить в избранное
    buttons.append([
        InlineKeyboardButton(
            text="⭐ Добавить в избранное",
            callback_data=f"favorite_{vacancy_id}"
        )
    ])
    
    # 2. Сгенерировать резюме под вакансию
    buttons.append([
        InlineKeyboardButton(
            text="📝 Сгенерировать резюме под вакансию",
            callback_data=f"generate_resume_{vacancy_id}"
        )
    ])
    
    # 3. Сгенерировать сопроводительное письмо
    buttons.append([
        InlineKeyboardButton(
            text="✉️ Сгенерировать сопроводительное письмо",
            callback_data=f"generate_letter_{vacancy_id}"
        )
    ])
    
    # 4. Откликнуться
    buttons.append([
        InlineKeyboardButton(
            text="📤 Откликнуться на вакансию",
            callback_data=f"response_{vacancy_id}"
        )
    ])
    
    # 5. Назад к вакансиям
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Назад к вакансиям",
            callback_data="back_to_vacancies_list"
        )
    ])
    
    # 6. Главное меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="menu_main"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)