from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.dependencies import DependencyProvider
from utils.states import SearchStates
from utils.keyboards import get_search_settings_keyboard, get_back_to_menu_keyboard

router = Router()

@router.callback_query(F.data == "menu_search_settings")
async def show_search_settings(callback: CallbackQuery, provider: DependencyProvider):
    """Показать настройки поиска"""
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    # Тестовый поиск для показа примерного количества вакансий
    from services.hh_service import HHService
    hh_service = HHService(provider.config.hh)
    sample_vacancies = await hh_service.search_vacancies(active_filter)
    
    stats_info = ""
    if sample_vacancies:
        stats_info = f"\n📈 <b>Примерно найдется:</b> {len(sample_vacancies)}+ вакансий"
    else:
        stats_info = f"\n📈 <b>Примерно найдется:</b> 0 вакансий (упростите фильтры)"
    
    settings_text = (
        "🔧 <b>Настройки поиска вакансий</b>\n\n"
        f"📝 <b>Ключевые слова:</b> {active_filter.keywords or 'Не задано'}\n"
        f"🌍 <b>Регион:</b> {active_filter.region or 'Не задано'}\n"
        f"💰 <b>Зарплата от:</b> {active_filter.salary_from or 'Не задано'}\n"
        f"💰 <b>Зарплата до:</b> {active_filter.salary_to or 'Не задано'}\n"
        f"🎯 <b>Опыт:</b> {active_filter.experience or 'Не задано'}\n"
        #f"💼 <b>Занятость:</b> {active_filter.employment or 'Не задано'}\n"
        f"📋 <b>График:</b> {active_filter.schedule or 'Не задано'}\n"
        f"📅 <b>Период:</b> {active_filter.period or 1} день"
        f"{stats_info}"
    )
    
    await callback.message.edit_text(
        settings_text,
        reply_markup=get_search_settings_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("settings_"))
async def handle_search_setting(callback: CallbackQuery, state: FSMContext, provider: DependencyProvider):
    """Обработчик настройки параметров поиска"""
    setting = callback.data.replace("settings_", "")
    
    state_mapping = {
        "keywords": (SearchStates.waiting_keywords, "📝 Введите ключевые слова для поиска:"),
        "region": (SearchStates.waiting_region, "🌍 Введите регион для поиска:"),
        "salary_from": (SearchStates.waiting_salary_from, "💰 Введите минимальную зарплату:\n\n<i>Или введите 0 чтобы убрать фильтр</i>"),
        "salary_to": (SearchStates.waiting_salary_to, "💰 Введите максимальную зарплату:\n\n<i>Или введите 0 чтобы убрать фильтр</i>"),
        "experience": (SearchStates.waiting_experience, "🎯 Введите требуемый опыт:\n\n<i>Или введите 'любой' чтобы убрать фильтр</i>"),
        "employment": (SearchStates.waiting_employment, "💼 Введите тип занятости:\n\n<i>Или введите 'любой' чтобы убрать фильтр</i>"),
        "schedule": (SearchStates.waiting_schedule, "📋 Введите график работы:\n\n<i>Или введите 'любой' чтобы убрать фильтр</i>"),
        "period": (SearchStates.waiting_period, "📅 Введите период поиска (в днях):\n\n<i>Рекомендуется 1-7 дней</i>")
    }
    
    if setting in state_mapping:
        state_class, message_text = state_mapping[setting]
        await state.set_state(state_class)
        try:
            await callback.message.edit_text(
                f"{message_text}\n\n<i>Отправьте значение или нажмите 'Отмена' для возврата</i>",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.answer(
                f"{message_text}\n\n<i>Отправьте значение или нажмите 'Отмена' для возврата</i>",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
    elif setting == "reset_salary":
        # Сброс зарплаты
        user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
        active_filter = await provider.search_filter_repo.get_active_filter(user.id)
        await provider.search_filter_repo.update_filter(active_filter.id, salary_from=None, salary_to=None)
        await callback.answer("✅ Фильтр по зарплате сброшен!", show_alert=True)
        await show_search_settings(callback, provider)
    elif setting == "reset_all":
        # Сброс всех фильтров
        user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
        active_filter = await provider.search_filter_repo.get_active_filter(user.id)
        await provider.search_filter_repo.update_filter(
            active_filter.id, 
            salary_from=None, 
            salary_to=None,
            experience=None,
            employment=None,
            schedule=None,
            period=1
        )
        await callback.answer("✅ Все фильтры сброшены!", show_alert=True)
        await show_search_settings(callback, provider)
    elif setting == "save":
        await callback.answer("✅ Настройки сохранены!", show_alert=True)
        try:
            await show_search_settings(callback, provider)
        except Exception:
            await callback.message.answer("✅ Настройки сохранены!")
    else:
        await callback.answer("❌ Неизвестная настройка", show_alert=True)


@router.message(SearchStates.waiting_keywords)
async def process_keywords(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ключевых слов"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    await provider.search_filter_repo.update_filter(active_filter.id, keywords=message.text)
    await message.answer("✅ Ключевые слова сохранены!")
    await state.clear()
    await show_search_settings_message(message, provider)

@router.message(SearchStates.waiting_region)
async def process_region(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка региона"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    await provider.search_filter_repo.update_filter(active_filter.id, region=message.text)
    await message.answer("✅ Регион сохранен!")
    await state.clear()
    await show_search_settings_message(message, provider)

@router.message(SearchStates.waiting_salary_from)
async def process_salary_from(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка зарплаты от"""
    if message.text.strip() == "0":
        # Сброс зарплаты
        salary_value = None
    elif not message.text.isdigit():
        await message.answer("❌ Пожалуйста, введите число или 0 для сброса")
        return
    else:
        salary_value = int(message.text)
        if salary_value <= 0:
            await message.answer("❌ Зарплата должна быть положительным числом")
            return
        
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    await provider.search_filter_repo.update_filter(active_filter.id, salary_from=salary_value)
    
    if salary_value is None:
        await message.answer("✅ Фильтр 'зарплата от' сброшен!")
    else:
        await message.answer(f"✅ Зарплата 'от' сохранена: {salary_value} руб.")
    
    await state.clear()
    await show_search_settings_message(message, provider)

@router.message(SearchStates.waiting_salary_to)
async def process_salary_to(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка зарплаты до"""
    if message.text.strip() == "0":
        # Сброс зарплаты
        salary_value = None
    elif not message.text.isdigit():
        await message.answer("❌ Пожалуйста, введите число или 0 для сброса")
        return
    else:
        salary_value = int(message.text)
        if salary_value <= 0:
            await message.answer("❌ Зарплата должна быть положительным числом")
            return
        
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    await provider.search_filter_repo.update_filter(active_filter.id, salary_to=salary_value)
    
    if salary_value is None:
        await message.answer("✅ Фильтр 'зарплата до' сброшен!")
    else:
        await message.answer(f"✅ Зарплата 'до' сохранена: {salary_value} руб.")
    
    await state.clear()
    await show_search_settings_message(message, provider)

@router.message(SearchStates.waiting_experience)
async def process_experience(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка опыта"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    if message.text.strip().lower() == 'любой':
        experience_value = None
        await message.answer("✅ Фильтр по опыту сброшен!")
    else:
        experience_value = message.text
        await message.answer("✅ Опыт сохранен!")
    
    await provider.search_filter_repo.update_filter(active_filter.id, experience=experience_value)
    await state.clear()
    await show_search_settings_message(message, provider)

@router.message(SearchStates.waiting_employment)
async def process_employment(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка типа занятости"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    if message.text.strip().lower() == 'любой':
        employment_value = None
        await message.answer("✅ Фильтр по занятости сброшен!")
    else:
        employment_value = message.text
        await message.answer("✅ Тип занятости сохранен!")
    
    await provider.search_filter_repo.update_filter(active_filter.id, employment=employment_value)
    await state.clear()
    await show_search_settings_message(message, provider)

@router.message(SearchStates.waiting_schedule)
async def process_schedule(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка графика работы"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    if message.text.strip().lower() == 'любой':
        schedule_value = None
        await message.answer("✅ Фильтр по графику сброшен!")
    else:
        schedule_value = message.text
        await message.answer("✅ График работы сохранен!")
    
    await provider.search_filter_repo.update_filter(active_filter.id, schedule=schedule_value)
    await state.clear()
    await show_search_settings_message(message, provider)

@router.message(SearchStates.waiting_period)
async def process_period(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка периода поиска"""
    if not message.text.isdigit():
        await message.answer("❌ Пожалуйста, введите число (дни)")
        return
        
    period_value = int(message.text)
    if period_value <= 0:
        await message.answer("❌ Период должен быть положительным числом")
        return
        
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    await provider.search_filter_repo.update_filter(active_filter.id, period=period_value)
    await message.answer("✅ Период поиска сохранен!")
    await state.clear()
    await show_search_settings_message(message, provider)

async def show_search_settings_message(message: Message, provider: DependencyProvider):
    """Вспомогательная функция для показа настроек поиска"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    # Форматируем значения
    salary_from_display = active_filter.salary_from if active_filter.salary_from else 'Не задано'
    salary_to_display = active_filter.salary_to if active_filter.salary_to else 'Не задано'
    experience_display = active_filter.experience if active_filter.experience else 'Любой'
    employment_display = active_filter.employment if active_filter.employment else 'Любой'
    schedule_display = active_filter.schedule if active_filter.schedule else 'Любой'
    
    settings_text = (
        "🔧 <b>Настройки поиска вакансий</b>\n\n"
        f"📝 <b>Ключевые слова:</b> {active_filter.keywords or 'Не задано'}\n"
        f"🌍 <b>Регион:</b> {active_filter.region or 'Не задано'}\n"
        f"💰 <b>Зарплата от:</b> {salary_from_display}\n"
        f"💰 <b>Зарплата до:</b> {salary_to_display}\n"
        f"🎯 <b>Опыт:</b> {experience_display}\n"
        f"💼 <b>Занятость:</b> {employment_display}\n"
        f"📋 <b>График:</b> {schedule_display}\n"
        f"📅 <b>Период:</b> {active_filter.period or 1} день\n\n"
        f"💡 <b>Совет:</b> Используйте 'Сбросить все' для минимальных фильтров"
    )
    
    await message.answer(
        settings_text,
        reply_markup=get_search_settings_keyboard(),
        parse_mode="HTML"
    )