from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import logging
from core.dependencies import DependencyProvider
from utils.states import SearchStates
from utils.keyboards import get_search_settings_keyboard, get_back_to_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)

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
    
@router.callback_query(F.data == "menu_search_vacancies")
async def search_and_save_vacancies(callback: CallbackQuery, provider: DependencyProvider):
    """Поиск и сохранение вакансий"""
    await callback.answer("🔍 Начинаю поиск вакансий...")
    
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    active_filter = await provider.search_filter_repo.get_active_filter(user.id)
    
    if not active_filter:
        await callback.message.answer("❌ Не найден активный фильтр поиска!")
        return
    
    # Статус сообщение
    status_msg = await callback.message.answer("🔍 Поиск вакансий... 0%")
    
    try:
        await status_msg.edit_text("🔍 Ищу вакансии через HH API... 10%")
        # Получаем вакансии через HH Service
        hh_service = provider.hh_service
        
        # 2. Инициализируем поиск
        import asyncio
        await asyncio.sleep(0.5)  # Имитация загрузки
        await status_msg.edit_text("🔍 Формирую поисковый запрос... 20%")
        
        # Создаем задачу для отслеживания прогресса поиска
        #search_task = asyncio.create_task(hh_service.search_vacancies(active_filter))
        
        # Показываем прогресс во время поиска
        search_progress = [
            "🔍 Запрашиваю первую страницу... 20%",
            "🔍 Анализирую результаты... 30%",
            "🔍 Получаю дополнительные страницы... 40%",
            "🔍 Обрабатываю данные... 50%",
            "🔍 Форматирую вакансии... 60%",
            "🔍 Завершаю поиск... 70%"
        ]
        
        all_vacancies = []
        error_occurred = False
        
        for progress_text, progress_percent in search_progress:
            try:
                await asyncio.sleep(2)  # Реальная задержка между этапами
                await status_msg.edit_text(f"{progress_text} {progress_percent}%")
                
                # На 50% выполняем реальный поиск
                if progress_percent == 50 and not error_occurred:
                    try:
                        # Выполняем реальный поиск
                        all_vacancies = await hh_service.search_vacancies(active_filter)
                        
                        if not all_vacancies:
                            await status_msg.edit_text("❌ По вашему запросу не найдено вакансий")
                            return
                            
                    except Exception as e:
                        logger.error(f"Ошибка при поиске: {e}")
                        error_occurred = True
                        all_vacancies = []
                
            except Exception as e:
                logger.error(f"Ошибка при показе прогресса: {e}")
                continue
        
        if error_occurred or not all_vacancies:
            await status_msg.edit_text("❌ Произошла ошибка при поиске. Попробуйте позже.")
            return
        
        '''
        for i, progress_msg in enumerate(search_progress_messages):
            if search_task.done():
                break
            await asyncio.sleep(3)  # Ждем 3 секунды между обновлениями
            await status_msg.edit_text(f"{progress_msg}\n\n⏳ Поиск выполняется...")
        
        # Ждем завершения поиска
        all_vacancies = await search_task
        
        #all_vacancies = await hh_service.search_vacancies(active_filter)
        
        if not all_vacancies:
            await status_msg.edit_text("❌ По вашему запросу не найдено вакансий")
            return
        '''
        
        total_count = len(all_vacancies)
        await status_msg.edit_text(f"✅ Найдено {total_count} вакансий\n\n💾 Сохраняю в базу... 0%")
        
        # Сохраняем вакансии в БД
        saved_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, vacancy_data in enumerate(all_vacancies):
            try:
                # Проверяем обязательные поля
                if not vacancy_data.get('hh_id'):
                    error_count += 1
                    continue
                
                # Сохраняем вакансию в базу
                vacancy = await provider.vacancy_repo.get_or_create_vacancy(vacancy_data)
                
                if not vacancy:
                    error_count += 1
                    continue
                
                # Создаем связь пользователь-вакансия (если не существует)
                existing_link = await provider.user_vacancy_repo.get_user_vacancy(user.id, vacancy.id)
                if not existing_link:
                    await provider.user_vacancy_repo.create_user_vacancy(
                        user_id=user.id, 
                        vacancy_id=vacancy.id,
                        is_viewed=False
                    )
                    saved_count += 1
                else:
                    skipped_count += 1
                
                # Обновляем статус каждые 10% или каждые 10 вакансий
                if i % max(1, total_count // 10) == 0 or i % 10 == 0:
                    # Расчет процента с учетом того, что поиск уже занял 75%
                    base_progress = 75
                    save_progress = (i + 1) * 25 // total_count  # Оставшиеся 25% на сохранение
                    percent = base_progress + save_progress
                    #percent = (i + 1) * 100 // total_count
                    await status_msg.edit_text(
                        f"💾 Сохранение: {percent}%\n"
                        f"✅ Новых: {saved_count}\n"
                        f"⏩ Уже есть: {skipped_count}\n"
                        f"❌ Ошибок: {error_count}\n"
                        f"📊 Обработано: {i+1}/{total_count}"
                        f"⏳ Пожалуйста, подождите..."
                    )
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Ошибка при сохранении вакансии {i}: {e}")
                continue
        
        # Финальное сообщение
        await status_msg.edit_text(
            f"✅ <b>Поиск завершен!</b>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Всего найдено: {total_count}\n"
            f"• Новых сохранено: {saved_count}\n"
            f"• Уже было в базе: {skipped_count}\n"
            f"• Ошибок: {error_count}\n\n"
            f"📂 Теперь вы можете посмотреть их в разделе "
            f"<b>'Мои вакансии'</b>\n\n"
            f"💡 <i>Совет: Проверьте настройки поиска, "
            f"чтобы получить более точные результаты</i>",
            parse_mode="HTML"
        )
    except asyncio.TimeoutError:
        await status_msg.edit_text("⏰ Поиск занял слишком много времени. Попробуйте упростить фильтры.")
    except Exception as e:
        logger.error(f"Ошибка при поиске вакансий: {e}")
        await status_msg.edit_text(f"❌ Ошибка при поиске: {str(e)}")    
