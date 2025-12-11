from typing import Optional, List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
            InlineKeyboardButton(text="📂 Мои вакансии", callback_data="menu_my_vacancies")
        ],
        [
            InlineKeyboardButton(text="🤖 AI Помощник", callback_data="menu_llm_settings"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")
        ],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="menu_help")
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

def get_vacancy_actions_keyboard(vacancy_id: int, user_vacancy: Any = None, show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура действий с вакансией"""
    buttons = []
    
    # Кнопка "В избранное" / "Убрать из избранного"
    if user_vacancy and user_vacancy.is_favorite:
        buttons.append([InlineKeyboardButton(text="⭐ Убрать из избранного", callback_data=f"vacancy_unfavorite_{vacancy_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="⭐ В избранное", callback_data=f"vacancy_favorite_{vacancy_id}")])
    
    # Кнопка "Заметки"
    notes_text = "📝 Заметки"
    if user_vacancy and user_vacancy.notes:
        notes_text = "📝 Заметки (есть)"
    buttons.append([InlineKeyboardButton(text=notes_text, callback_data=f"vacancy_notes_{vacancy_id}")])
    
    # Кнопка "Откликнуться" / "Отклик отправлен"
    if user_vacancy and user_vacancy.is_applied:
        buttons.append([InlineKeyboardButton(text="✅ Отклик отправлен", callback_data=f"vacancy_applied_{vacancy_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="📤 Откликнуться", callback_data=f"vacancy_apply_{vacancy_id}")])
    
    # Кнопка "Просмотрено" / "Не просмотрено"
    if user_vacancy and user_vacancy.is_viewed:
        buttons.append([InlineKeyboardButton(text="👁️ Просмотрено", callback_data=f"vacancy_viewed_{vacancy_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="👁️‍🗨️ Отметить просмотренным", callback_data=f"vacancy_view_{vacancy_id}")])
    
    # Навигация
    nav_buttons = []
    if show_back:
        nav_buttons.append(InlineKeyboardButton(text="← Назад к списку", callback_data="vacancy_back_to_list"))
    nav_buttons.append(InlineKeyboardButton(text="📂 В меню", callback_data="menu_main"))
    
    buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_vacancy_navigation_keyboard(current_page: int, total_pages: int, vacancy_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура навигации по вакансиям"""
    buttons = []
    
    # Навигационные кнопки
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Предыдущая", callback_data=f"page_{current_page-1}"))
    
    if vacancy_id:
        nav_buttons.append(InlineKeyboardButton(text="🔍 Подробнее", callback_data=f"vacancy_detail_{vacancy_id}"))
    
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Следующая ▶️", callback_data=f"page_{current_page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Кнопки действий (если есть vacancy_id)
    if vacancy_id:
        action_buttons = [
            InlineKeyboardButton(text="⭐ Избранное", callback_data=f"vacancy_favorite_{vacancy_id}"),
            InlineKeyboardButton(text="📤 Отклик", callback_data=f"vacancy_apply_{vacancy_id}"),
            InlineKeyboardButton(text="👁️ Просмотрено", callback_data=f"vacancy_view_{vacancy_id}")
        ]
        buttons.append(action_buttons)
    
    # Кнопка возврата в меню
    buttons.append([InlineKeyboardButton(text="📂 В меню", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_pagination_keyboard(current_page: int, total_pages: int, show_actions: bool = False) -> InlineKeyboardMarkup:   
    """Клавиатура пагинации для вакансий"""
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
    
    buttons.append([InlineKeyboardButton(text="📂 Мои вакансии", callback_data="menu_my_vacancies")])
    
    # Основные кнопки
    main_buttons = []
    #if show_actions:
    #main_buttons.append(InlineKeyboardButton(text="📂 Мои вакансии", callback_data="menu_my_vacancies"))
    #else:
    main_buttons.append(InlineKeyboardButton(text="🔍 Новый поиск", callback_data="menu_vacancies"))
    
    main_buttons.append(InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main"))
    
    buttons.append(main_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)