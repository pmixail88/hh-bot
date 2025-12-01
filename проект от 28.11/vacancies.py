from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import re
import logging

from aiogram.fsm.state import State, StatesGroup
from core.dependencies import DependencyProvider
from utils.states import VacancyStates
from utils.keyboards import get_back_to_menu_keyboard, get_vacancy_actions_keyboard
import math
from typing import Any, List

logger = logging.getLogger(__name__)

# Константы для пагинации
VACANCIES_PER_PAGE = 5

router = Router()

class VacancyPaginationStates(StatesGroup):
    browsing = State()

# ... после импортов ...

def format_vacancy_message(vacancy: Any, current_page: int, total_pages: int, title: str = "💼 Вакансия:") -> str:
    """Форматирование сообщения о вакансии"""
    
    # Форматируем зарплату
    salary_text = "💰 Зарплата: не указана"
    if vacancy.salary_from or vacancy.salary_to:
        salary_parts = []
        if vacancy.salary_from:
            salary_parts.append(f"от {vacancy.salary_from:,}")
        if vacancy.salary_to:
            salary_parts.append(f"до {vacancy.salary_to:,}")
        salary_text = f"💰 Зарплата: {' '.join(salary_parts)} {vacancy.salary_currency or 'руб.'}"
        if vacancy.salary_gross is not None:
            salary_text += " (до вычета налогов)" if vacancy.salary_gross else " (на руки)"
    
    # Обрезаем описание если слишком длинное
    description = vacancy.description or "Описание отсутствует"
    if len(description) > 1500:
        description = description[:1500] + "..."
    
    # Форматируем опыт, график и занятость
    experience = vacancy.experience or "Не указан"
    schedule = vacancy.schedule or "Не указан"
    employment = vacancy.employment or "Не указан"
    
    # Форматируем дату публикации
    if vacancy.published_at:
        if isinstance(vacancy.published_at, datetime):
            published_date = vacancy.published_at.strftime('%d.%m.%Y')
        elif isinstance(vacancy.published_at, str):
            published_date = vacancy.published_at[:10]  # Берем только дату из строки
        else:
            published_date = "Неизвестно"
    else:
        published_date = "Неизвестно"
    
    message = (
        f"{title}\n\n"
        f"📋 <b>{vacancy.name}</b>\n"
        f"🏢 <b>Компания:</b> {vacancy.company_name}\n"
        f"📍 <b>Локация:</b> {vacancy.area_name}\n"
        f"{salary_text}\n"
        f"🎯 <b>Опыт:</b> {experience}\n"
        f"📅 <b>График:</b> {schedule}\n"
        f"💼 <b>Занятость:</b> {employment}\n"
        f"📅 <b>Опубликовано:</b> {published_date}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"🔗 <a href='{vacancy.url}'>Ссылка на вакансию</a>\n\n"
        f"📄 Страница {current_page + 1} из {total_pages}"
    )
    
    return message

# Теперь обработчики

@router.callback_query(F.data.startswith("page_"))
async def handle_pagination(callback: CallbackQuery, state: FSMContext, provider: DependencyProvider):
    """Обработчик пагинации"""
    try:
        page = int(callback.data.replace("page_", ""))
        
        data = await state.get_data()
        vacancies = data.get('current_vacancies', [])
        
        if not vacancies:
            await callback.answer("❌ Нет данных для отображения", show_alert=True)
            return
        
        # Получаем заголовок из состояния или используем заголовок из сообщения
        title = data.get('vacancies_title', "💼 Вакансии:")
        show_actions = data.get('show_actions', True)
        
        # Показываем запрошенную страницу
        await show_vacancies_page(
            callback.message,
            vacancies,
            page,
            provider,
            title,
            show_actions
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка пагинации: {e}")
        await callback.answer("❌ Ошибка при переключении страницы", show_alert=True)

@router.callback_query(F.data == "menu_vacancies")
async def search_new_vacancies(callback: CallbackQuery, provider: DependencyProvider, state: FSMContext):
    """Поиск новых вакансий по текущим настройкам"""
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    if not active_filter:
        await callback.answer("❌ Настройте фильтр поиска", show_alert=True)
        return

    await callback.message.edit_text("🔍 Ищу новые вакансии...")
    
    # Ищем вакансии через HH API
    logger.info(f"Поиск вакансий для пользователя {user.id} с фильтром: {active_filter.keywords} в {active_filter.region}")
    vacancies = await provider.hh_service.search_vacancies(active_filter)
    
    # ✅ ДОБАВЛЕНО: ПРОВЕРКА НА ПУСТОЙ РЕЗУЛЬТАТ
    
    if not vacancies:
        # Если нет новых, показываем за последние 24 часа из БД
        logger.info("Новых вакансий не найдено, ищем в БД за последние 24 часа")
        recent_vacancies = await provider.vacancy_repo.get_recent_vacancies(24)
        if recent_vacancies:
            # Сохраняем вакансии в состоянии для пагинации
            await state.update_data(current_vacancies=recent_vacancies)
            await show_vacancies_page(
                callback.message, 
                recent_vacancies, 
                0, 
                provider,
                "⚠️ Новых вакансий не найдено. Показываю вакансии за последние 24 часа:"
            )
        else:
            await callback.message.edit_text(
                "❌ Вакансий не найдено по текущим настройкам.\n\n"
                "💡 <b>Советы:</b>\n"
                "• Упростите ключевые слова\n"
                "• Расширьте регион поиска\n" 
                "• Увеличьте период поиска\n"
                "• Уберите фильтр по зарплате",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
        return

    # Сохраняем вакансии в БД и в состоянии для пагинации
    saved_count = 0
    all_vacancies = []
    
    for vacancy_data in vacancies:
        try:
            # Проверяем, есть ли уже такая вакансия
            existing = await provider.vacancy_repo.get_vacancy_by_hh_id(vacancy_data['hh_id'])
            if not existing:
                vacancy = await provider.vacancy_repo.create_vacancy(vacancy_data)
                # Создаем связь пользователь-вакансия
                await provider.user_vacancy_repo.create_user_vacancy(user.id, vacancy.id)
                saved_count += 1
                all_vacancies.append(vacancy)
            else:
                # Показываем и существующие вакансии
                all_vacancies.append(existing)
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении вакансии {vacancy_data.get('hh_id')}: {e}")  # ✅ ИСПРАВЛЕНО
            continue  # ✅ ДОБАВЛЕНО: ПРОДОЛЖАЕМ даже при ошибке

    # ✅ ДОБАВЛЕНО: ПРОВЕРКА ЕСТЬ ЛИ ВАКАНСИИ ДЛЯ ПОКАЗА
    if not all_vacancies:
        await callback.message.edit_text(
            "❌ Не удалось сохранить вакансии. Попробуйте другой поисковый запрос.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # ✅ ДОБАВЛЕНО: ЛОГГИРОВАНИЕ ДЛЯ ДЕБАГА
    logger.info(f"📊 Готово к показу: {len(all_vacancies)} вакансий")

    # ✅ ДОБАВЬТЕ ЭТО: Сохраняем данные в состоянии
    await state.update_data(
        current_vacancies=all_vacancies,
        vacancies_title=f"✅ Найдено {len(vacancies)} вакансий. Сохранено {saved_count} новых.",
        show_actions=True
    )

    # Сохраняем вакансии в состоянии для пагинации
    #await state.update_data(current_vacancies=all_vacancies)
    
    # Показываем первую страницу
    title = (
        f"✅ Найдено {len(vacancies)} вакансий. "
        f"Сохранено {saved_count} новых.\n"
        f"Показываю {len(all_vacancies)} вакансий:"
    )
    
    await show_vacancies_page(callback.message, all_vacancies, 0, provider, title, show_actions=True)

@router.callback_query(F.data == "menu_my_vacancies")
async def show_my_vacancies(callback: CallbackQuery, provider: DependencyProvider, state: FSMContext):
    """Показать сохраненные вакансии пользователя"""
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    
    # Получаем все связи пользователь-вакансия с предзагрузкой вакансий
    user_vacancies = await provider.user_vacancy_repo.get_user_vacancies(user.id)
    
    if not user_vacancies:
        await callback.message.edit_text(
            "📭 У вас нет сохраненных вакансий.\n\n"
            "💡 Используйте поиск вакансий, чтобы сохранить интересные предложения.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Фильтруем активные вакансии
    vacancies = []
    for uv in user_vacancies:
        if uv.vacancy and not uv.vacancy.is_archived:
            vacancies.append(uv.vacancy)
    
    if not vacancies:
        await callback.message.edit_text(
            "📭 Все ваши вакансии устарели или были архивированы.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # ✅ ДОБАВЬТЕ ЭТО: Сохраняем данные в состоянии
    await state.update_data(
        current_vacancies=vacancies,
        vacancies_title=f"📂 Ваши сохраненные вакансии ({len(vacancies)}):",
        show_actions=True
    )
    # Сохраняем вакансии в состоянии для пагинации
    #await state.update_data(current_vacancies=vacancies)
    
    await show_vacancies_page(
        callback.message, 
        vacancies, 
        0, 
        provider, 
        f"📂 Ваши сохраненные вакансии ({len(vacancies)}):",
        show_actions=True
    )

async def show_vacancies_list(message: Message, vacancies: list, provider: DependencyProvider, show_actions: bool = False):
    """Показать список вакансий"""
    if not vacancies:
        await message.answer(
            "❌ Вакансии не найдены",
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # Сортируем по дате публикации (сначала новые)
    vacancies.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
    
    shown_count = 0
    for i, vacancy in enumerate(vacancies):
        try:
            # Пропускаем архивированные вакансии
            if getattr(vacancy, 'is_archived', False):
                continue
                
            salary_info = ""
            if vacancy.salary_from or vacancy.salary_to:
                salary_from = f"{vacancy.salary_from:,}".replace(',', ' ') if vacancy.salary_from else ""
                salary_to = f"{vacancy.salary_to:,}".replace(',', ' ') if vacancy.salary_to else ""
                currency = getattr(vacancy, 'salary_currency', 'руб.') or "руб."
                
                if salary_from and salary_to:
                    salary_info = f"\n💰 <b>Зарплата:</b> {salary_from} - {salary_to} {currency}"
                elif salary_from:
                    salary_info = f"\n💰 <b>Зарплата от:</b> {salary_from} {currency}"
                elif salary_to:
                    salary_info = f"\n💰 <b>Зарплата до:</b> {salary_to} {currency}"

            published = ""
            if vacancy.published_at:
                time_ago = datetime.utcnow() - vacancy.published_at
                if time_ago.days == 0:
                    hours = time_ago.seconds // 3600
                    if hours == 0:
                        published = f"\n🕐 <b>Опубликована:</b> только что"
                    else:
                        published = f"\n🕐 <b>Опубликована:</b> {hours} ч. назад"
                else:
                    published = f"\n🕐 <b>Опубликована:</b> {time_ago.days} д. назад"

            # Обрезаем длинное описание
            description = getattr(vacancy, 'description', '') or ""
            if len(description) > 150:
                description = description[:150] + "..."

            # Формируем текст вакансии
            vacancy_text = (
                f"💼 <b>{vacancy.name}</b>\n"
                f"🏢 <b>Компания:</b> {vacancy.company_name}\n"
                f"📍 <b>Город:</b> {vacancy.area_name}{salary_info}{published}\n"
            )
            
            # Добавляем описание если есть
            if description and description != "Описание не указано":
                vacancy_text += f"📝 <b>Описание:</b> {description}\n"
            
            vacancy_text += f"🔗 <a href='{vacancy.url}'>Ссылка на вакансию</a>"

            keyboard = None
            if show_actions:
                keyboard = get_vacancy_actions_keyboard(vacancy.id)

            await message.answer(
                vacancy_text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=False  # Разрешаем превью ссылок
            )
            
            shown_count += 1
            # Ограничиваем показ 10 вакансиями чтобы не спамить
            if shown_count >= 10:
                break
                
            # Небольшая задержка между сообщениями
            import asyncio
            await asyncio.sleep(0.3)
                
        except Exception as e:
            logger.error(f"Ошибка при показе вакансии: {e}")
            continue

    if len(vacancies) > shown_count:
        await message.answer(
            f"ℹ️ Показано {shown_count} из {len(vacancies)} вакансий\n"
            f"💡 Для просмотра всех вакансий используйте фильтры поиска",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "📊 <b>Главное меню</b> - выберите действие:",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("vacancy_"))
async def handle_vacancy_action(callback: CallbackQuery, provider: DependencyProvider):
    """Обработчик действий с вакансией"""
    action_parts = callback.data.split("_")
    if len(action_parts) < 3:
        await callback.answer("❌ Ошибка действия", show_alert=True)
        return

    action = action_parts[1]
    vacancy_id = int(action_parts[2])
    
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    user_vacancy = await provider.user_vacancy_repo.get_user_vacancy(user.id, vacancy_id)
    
    if not user_vacancy:
        await callback.answer("❌ Вакансия не найдена", show_alert=True)
        return

    if action == "favorite":
        user_vacancy.is_favorite = not user_vacancy.is_favorite
        await provider.user_vacancy_repo.update_user_vacancy(user_vacancy.id, is_favorite=user_vacancy.is_favorite)
        status = "добавлена в избранное" if user_vacancy.is_favorite else "убрана из избранного"
        await callback.answer(f"✅ Вакансия {status}")
    
    elif action == "apply":
        user_vacancy.is_applied = True
        await provider.user_vacancy_repo.update_user_vacancy(user_vacancy.id, is_applied=True)
        await callback.answer("✅ Отметка 'Откликнулся' добавлена")
    
    elif action == "viewed":
        user_vacancy.is_viewed = True
        user_vacancy.viewed_at = datetime.utcnow()
        await provider.user_vacancy_repo.update_user_vacancy(
            user_vacancy.id, 
            is_viewed=True, 
            viewed_at=user_vacancy.viewed_at
        )
        await callback.answer("✅ Вакансия отмечена как просмотренная")
    
    elif action == "notes":
        await callback.answer("📝 Функция заметок в разработке", show_alert=True)
    
    # Обновляем сообщение с вакансией
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_vacancy_actions_keyboard(vacancy_id)
        )
    except Exception:
        pass  # Игнорируем ошибки редактирования

async def show_vacancies_page(
    message: Message, 
    vacancies: List[Any], 
    page: int, 
    provider: DependencyProvider, 
    title: str = "💼 Найденные вакансии:",
    show_actions: bool = True  # Параметр для показа кнопок действий
):
    """Показать страницу с вакансиями (одна вакансия на странице)"""
    if not vacancies:
        await message.answer("❌ Нет вакансий для отображения", reply_markup=get_back_to_menu_keyboard())
        return
    
    total_pages = len(vacancies)
    if page >= total_pages:
        page = total_pages - 1
    elif page < 0:
        page = 0
    
    vacancy = vacancies[page]
    
    # Форматируем сообщение
    message_text = format_vacancy_message(vacancy, page, total_pages, title)
    
    # Получаем информацию о связи пользователь-вакансия
    user_vacancy = None
    if show_actions:
        user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
        # ✅ ДОБАВЛЕНО: ПРОВЕРКА НА НАЛИЧИЕ ПОЛЬЗОВАТЕЛЯ
        if user:
            user_vacancy = await provider.user_vacancy_repo.get_user_vacancy(user.id, vacancy.id)
        else:
            logger.warning(f"Пользователь не найден для telegram_id: {message.from_user.id}")
            show_actions = False  # Отключаем кнопки действий
    
    # Создаем клавиатуру
    from utils.keyboards import get_vacancy_actions_keyboard, get_pagination_keyboard
    
    if show_actions:
        # Клавиатура с действиями и пагинацией
        action_keyboard = get_vacancy_actions_keyboard(vacancy.id, user_vacancy, show_back=False)
        pagination_keyboard = get_pagination_keyboard(page, total_pages, show_actions=True)
        
        # Объединяем клавиатуры
        inline_keyboard = action_keyboard.inline_keyboard + pagination_keyboard.inline_keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    else:
        # Только пагинация
        keyboard = get_pagination_keyboard(page, total_pages, show_actions=False)
    
    # Отправляем или редактируем сообщение
    try:
        await message.edit_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception:
        await message.answer(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        
async def show_single_vacancy(
    message: Message, 
    vacancy: Any, 
    provider: DependencyProvider, 
    show_actions: bool = False
):
    """Показать одну вакансию"""
    try:
        salary_info = ""
        if vacancy.salary_from or vacancy.salary_to:
            salary_from = f"{vacancy.salary_from:,}".replace(',', ' ') if vacancy.salary_from else ""
            salary_to = f"{vacancy.salary_to:,}".replace(',', ' ') if vacancy.salary_to else ""
            currency = getattr(vacancy, 'salary_currency', 'руб.') or "руб."
            
            if salary_from and salary_to:
                salary_info = f"\n💰 <b>Зарплата:</b> {salary_from} - {salary_to} {currency}"
            elif salary_from:
                salary_info = f"\n💰 <b>Зарплата от:</b> {salary_from} {currency}"
            elif salary_to:
                salary_info = f"\n💰 <b>Зарплата до:</b> {salary_to} {currency}"

        published = ""
        if vacancy.published_at:
            time_ago = datetime.utcnow() - vacancy.published_at
            if time_ago.days == 0:
                hours = time_ago.seconds // 3600
                if hours == 0:
                    published = f"\n🕐 <b>Опубликована:</b> только что"
                else:
                    published = f"\n🕐 <b>Опубликована:</b> {hours} ч. назад"
            else:
                published = f"\n🕐 <b>Опубликована:</b> {time_ago.days} д. назад"

        # Обрезаем длинное описание
        description = getattr(vacancy, 'description', '') or ""
        if len(description) > 150:
            description = description[:150] + "..."

        # Формируем текст вакансии
        vacancy_text = (
            f"💼 <b>{vacancy.name}</b>\n"
            f"🏢 <b>Компания:</b> {vacancy.company_name}\n"
            f"📍 <b>Город:</b> {vacancy.area_name}{salary_info}{published}\n"
        )
        
        # Добавляем описание если есть
        if description and description != "Описание не указано":
            vacancy_text += f"📝 <b>Описание:</b> {description}\n"
        
        vacancy_text += f"🔗 <a href='{vacancy.url}'>Ссылка на вакансию</a>"

        keyboard = None
        if show_actions:
            keyboard = get_vacancy_actions_keyboard(vacancy.id)

        await message.answer(
            vacancy_text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=False
        )
            
    except Exception as e:
        logger.error(f"❌ Ошибка при показе вакансии: {e}")

'''
def get_pagination_keyboard(current_page: int, total_pages: int, show_actions: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура пагинации"""
    keyboard = []
    
    # Кнопки навигации
    nav_buttons = []
    
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{current_page - 1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="current_page"))
    
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{current_page + 1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Основные кнопки
    main_buttons = []
    if show_actions:
        main_buttons.append(InlineKeyboardButton(text="📂 Мои вакансии", callback_data="menu_my_vacancies"))
    else:
        main_buttons.append(InlineKeyboardButton(text="🔍 Новый поиск", callback_data="menu_vacancies"))
    
    main_buttons.append(InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main"))
    keyboard.append(main_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
'''

@router.callback_query(F.data == "vacancy_back_to_list")
async def back_to_vacancies_list(callback: CallbackQuery, state: FSMContext, provider: DependencyProvider):
    """Вернуться к списку вакансий"""
    data = await state.get_data()
    vacancies = data.get('current_vacancies', [])
    title = data.get('vacancies_title', "💼 Вакансии:")
    
    if vacancies:
        await show_vacancies_page(
            callback.message,
            vacancies,
            0,
            provider,
            title,
            show_actions=True
        )
    else:
        await callback.message.edit_text(
            "📭 Нет сохраненных вакансий",
            reply_markup=get_back_to_menu_keyboard()
        )

@router.callback_query(F.data == "current_page")
async def current_page_info(callback: CallbackQuery, state: FSMContext):
    """Информация о текущей странице (просто уведомление)"""
    data = await state.get_data()
    vacancies = data.get('current_vacancies', [])
    
    if vacancies:
        await callback.answer(f"Вы на текущей странице", show_alert=True)
    else:
        await callback.answer("❌ Нет данных", show_alert=True)
        
