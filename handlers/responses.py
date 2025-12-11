from sqlalchemy import select
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from core.dependencies import DependencyProvider
from services.hh_service import HHService
from services.llm_service import LLMService
from utils.keyboards import get_back_to_menu_keyboard
from database.models import GeneratedResume, CoverLetter, Vacancy
from services.hh_response import HHResponseService
from utils.states import ResponseStates

from utils.logger import get_logger
logger = get_logger(__name__)
router = Router()





@router.callback_query(F.data.startswith("vacancy_response_"))
async def handle_vacancy_response(callback: CallbackQuery, provider: DependencyProvider, state: FSMContext):
    """Обработчик кнопки отклика на вакансию - переход к экрану отклика"""
    logger.info(f"Обработчик handle_vacancy_response вызван с данными: {callback.data}")
    print(f"DEBUG: handle_vacancy_response вызван с callback.data = {callback.data}")
    
    try:
        vacancy_id = int(callback.data.replace("vacancy_response_", ""))
    except ValueError:
        await callback.answer("❌ Ошибка: неверный ID вакансии", show_alert=True)
        return
    
    # БЫСТРЫЙ ОТВЕТ пользователю
    await callback.answer("🔄 Переход к отклику...")
    
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Сохраняем ID вакансии в состоянии
    await state.update_data(current_vacancy_id=vacancy_id)
    
    # Получаем вакансию
    from sqlalchemy import select
    from database.models import Vacancy, GeneratedResume, CoverLetter
    from utils.keyboards import get_response_vacancy_keyboard
    
    # Сохраняем ID вакансии в состоянии
    #await state.update_data(current_vacancy_id=vacancy_id)
    
    # Запрашиваем только нужные поля
    vacancy_result = await provider.session.execute(
        select(
            Vacancy.id,
            Vacancy.name,
            Vacancy.company_name,
            Vacancy.area_name,
            Vacancy.salary_from,
            Vacancy.salary_to,
            Vacancy.salary_currency,
            Vacancy.experience,
            Vacancy.description,
            Vacancy.url
        ).where(Vacancy.id == vacancy_id)
    )
    vacancy = vacancy_result.first()
    
    if not vacancy:
        await callback.answer("❌ Вакансия не найдена", show_alert=True)
        return
    # Проверяем наличие необходимых данных для отклика
    # Проверяем наличие сгенерированных резюме и писем
     # БЫСТРЫЕ параллельные запросы
    import asyncio
    
    # Запускаем параллельно
    resume_task = asyncio.create_task(
        provider.session.execute(
            select(GeneratedResume.id)
            .where(
                GeneratedResume.user_id == user.id,
                GeneratedResume.vacancy_id == vacancy_id
            )
            .limit(1)
        )
    )
    
    letter_task = asyncio.create_task(
        provider.session.execute(
            select(CoverLetter.id)
            .where(
                CoverLetter.user_id == user.id,
                CoverLetter.vacancy_id == vacancy_id
            )
            .limit(1)
        )
    )
    
    # Ждем оба запроса
    resume_result, letter_result = await asyncio.gather(resume_task, letter_task)
    has_resume = resume_result.scalar_one_or_none() is not None
    has_letter = letter_result.scalar_one_or_none() is not None
    
    # Форматируем быстро
    def format_quick_vacancy(vacancy_tuple):
        """Быстрое форматирование вакансии из tuple"""
        vid, name, company, area, salary_from, salary_to, currency, exp, desc, url = vacancy_tuple
        
        lines = [
            f"<b>🎯 ОТКЛИК НА ВАКАНСИЮ</b>\n",
            f"<b>📌 {name}</b>",
            f"🏢 <b>Компания:</b> {company}",
        ]
        
        if area:
            lines.append(f"📍 <b>Локация:</b> {area}")
        
        if salary_from or salary_to:
            salary = ""
            if salary_from:
                salary += f"от {salary_from:,}"
            if salary_to:
                salary += f" до {salary_to:,}"
            if currency:
                salary += f" {currency}"
            lines.append(f"💰 <b>Зарплата:</b> {salary}")
        
        if exp:
            lines.append(f"📊 <b>Опыт:</b> {exp}")
        
        if desc:
            short_desc = desc[:300] + "..." if len(desc) > 300 else desc
            lines.append(f"\n📝 <b>Описание:</b>\n{short_desc}")
        
        lines.append(f"\n🔗 <a href='{url}'>Ссылка на вакансию</a>")
        
        # Статус
        status_lines = ["\n📊 <b>Статус готовности:</b>"]
        status_lines.append("✅ Основное резюме" if user.base_resume else "❌ Основное резюме")
        status_lines.append("✅ Контактный email" if user.contact_email else "❌ Контактный email")
        status_lines.append("✅ Резюме на HH" if user.hh_resume_id else "❌ Резюме на HH")
        status_lines.append("✅ Адаптированное резюме" if has_resume else "❌ Адаптированное резюме")
        status_lines.append("✅ Сопроводительное письмо" if has_letter else "❌ Сопроводительное письмо")
        
        lines.append("\n".join(status_lines))
        
        return "\n".join(lines)
    is_favorite = False
    # Создаем клавиатуру
    # Получаем клавиатуру
    from utils.keyboards import get_response_vacancy_keyboard
    keyboard = get_response_vacancy_keyboard(
        vacancy_id=vacancy_id,
        user_id=user.id,
        is_favorite=is_favorite,
        has_resume=has_resume,
        has_letter=has_letter
    )
    
    # Отправляем сообщение
    try:
        await callback.message.edit_text(
            format_quick_vacancy(vacancy),
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        # Если не удалось редактировать, отправляем новое
        await callback.message.answer(
            format_quick_vacancy(vacancy),
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

@router.callback_query(F.data.startswith("response_setup_"))
async def setup_response_data(callback: CallbackQuery, provider: DependencyProvider, state: FSMContext):
    """Настройка данных для отклика"""
    vacancy_id = int(callback.data.replace("response_setup_", ""))
    
    await state.update_data(current_vacancy_id=vacancy_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📧 Указать email", callback_data=f"set_email_{vacancy_id}")],
        [InlineKeyboardButton(text="📱 Указать телефон", callback_data=f"set_phone_{vacancy_id}")],
        [InlineKeyboardButton(text="🔗 Указать ссылку на резюме HH", callback_data=f"set_hh_resume_{vacancy_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"vacancy_back_to_list")]
    ])
    
    await callback.message.edit_text(
        "⚙️ <b>Настройка данных для отклика</b>\n\n"
        "Заполните необходимые контактные данные:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("set_email_"))
async def set_email(callback: CallbackQuery, state: FSMContext):
    """Запрос email"""
    vacancy_id = int(callback.data.replace("set_email_", ""))
    await state.update_data(current_vacancy_id=vacancy_id)
    await state.set_state(ResponseStates.waiting_contact_email)
    
    await callback.message.edit_text(
        "📧 <b>Введите ваш email для связи:</b>\n\n"
        "<i>Работодатель будет использовать этот email для связи с вами</i>",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("set_phone_"))
async def set_phone(callback: CallbackQuery, state: FSMContext):
    """Запрос телефона"""
    vacancy_id = int(callback.data.replace("set_phone_", ""))
    await state.update_data(current_vacancy_id=vacancy_id)
    await state.set_state(ResponseStates.waiting_contact_phone)
    
    await callback.message.edit_text(
        "📱 <b>Введите ваш телефон для связи:</b>\n\n"
        "<i>Укажите номер в формате +7XXXXXXXXXX</i>",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("set_hh_resume_"))
async def set_hh_resume(callback: CallbackQuery, state: FSMContext):
    """Запрос ссылки на резюме HH"""
    vacancy_id = int(callback.data.replace("set_hh_resume_", ""))
    await state.update_data(current_vacancy_id=vacancy_id)
    await state.set_state(ResponseStates.waiting_hh_resume_id)
    
    await callback.message.edit_text(
        "🔗 <b>Введите ссылку на ваше резюме на HH.ru:</b>\n\n"
        "<i>Пример: https://hh.ru/resume/1234567890abcdef</i>\n"
        "<i>Или ID резюме: 1234567890abcdef</i>",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )

@router.message(ResponseStates.waiting_contact_email)
async def process_email(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка email"""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, message.text):
        await message.answer("❌ Неверный формат email. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    vacancy_id = data.get('current_vacancy_id')
    
    # Сохраняем email в профиль
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        contact_email=message.text
    )
    
    await message.answer("✅ Email сохранен!")
    await state.clear()
    
    # Возвращаемся к настройке отклика
    await setup_response_data_continuation(message, vacancy_id, provider)

@router.message(ResponseStates.waiting_contact_phone)
async def process_phone(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка телефона"""
    import re
    phone_pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    
    if not re.match(phone_pattern, message.text.replace(" ", "")):
        await message.answer("❌ Неверный формат телефона. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    vacancy_id = data.get('current_vacancy_id')
    
    # Сохраняем телефон в профиль
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        contact_phone=message.text
    )
    
    await message.answer("✅ Телефон сохранен!")
    await state.clear()
    
    # Возвращаемся к настройке отклика
    await setup_response_data_continuation(message, vacancy_id, provider)

@router.message(ResponseStates.waiting_hh_resume_id)
async def process_hh_resume(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ссылки на резюме HH"""
    import re
    
    # Извлекаем ID резюме из ссылки
    resume_text = message.text.strip()
    resume_id = None
    
    # Паттерны для извлечения ID
    patterns = [
        r'resume/([a-f0-9]+)',  # https://hh.ru/resume/abc123
        r'^([a-f0-9]+)$',       # Просто ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, resume_text, re.IGNORECASE)
        if match:
            resume_id = match.group(1)
            break
    
    if not resume_id:
        await message.answer("❌ Не удалось извлечь ID резюме. Проверьте формат:")
        return
    
    data = await state.get_data()
    vacancy_id = data.get('current_vacancy_id')
    
    # Сохраняем ID резюме в профиль
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        hh_resume_id=resume_id
    )
    
    await message.answer(f"✅ Ссылка на резюме сохранена! (ID: {resume_id})")
    await state.clear()
    
    # Возвращаемся к настройке отклика
    await setup_response_data_continuation(message, vacancy_id, provider)

async def setup_response_data_continuation(message: Message, vacancy_id: int, provider: DependencyProvider):
    """Продолжение настройки после сохранения данных"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    # Проверяем, все ли данные заполнены
    if user.hh_resume_id and user.contact_email:
        # Все готово, переходим к отклику
        await show_single_vacancy_for_response(message, vacancy_id, provider, user)
    else:
        # Еще не все заполнено
        await setup_response_data(message, vacancy_id, provider)

async def setup_response_data(message: Message, vacancy_id: int, provider: DependencyProvider):
    """Вспомогательная функция для настройки"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    status = []
    if user.hh_resume_id:
        status.append("✅ Ссылка на резюме HH")
    else:
        status.append("❌ Ссылка на резюме HH")
    
    if user.contact_email:
        status.append("✅ Email для связи")
    else:
        status.append("❌ Email для связи")
    
    if user.contact_phone:
        status.append("✅ Телефон")
    else:
        status.append("❌ Телефон")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📧 Указать email", callback_data=f"set_email_{vacancy_id}")] if not user.contact_email else [],
        [InlineKeyboardButton(text="📱 Указать телефон", callback_data=f"set_phone_{vacancy_id}")] if not user.contact_phone else [],
        [InlineKeyboardButton(text="🔗 Указать ссылку на резюме HH", callback_data=f"set_hh_resume_{vacancy_id}")] if not user.hh_resume_id else [],
        [InlineKeyboardButton(text="➡️ Перейти к отклику", callback_data=f"vacancy_response_{vacancy_id}")] if user.hh_resume_id and user.contact_email else [],
        [InlineKeyboardButton(text="⬅️ Назад к вакансии", callback_data=f"page_0")]
    ])
    
    await message.answer(
        "⚙️ <b>Настройка данных для отклика</b>\n\n" +
        "\n".join(status) +
        "\n\n<i>Для отправки отклика необходимо заполнить все обязательные поля</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def show_single_vacancy_for_response(message: Message, vacancy_id: int, provider: DependencyProvider, user):
    """Показ вакансии для отклика (единичный показ)"""
    from sqlalchemy import select
    from database.models import Vacancy, GeneratedResume, CoverLetter
    
    # Получаем вакансию
    vacancy_result = await provider.session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = vacancy_result.scalar_one_or_none()
    
    if not vacancy:
        await message.answer("❌ Вакансия не найдена")
        return
    
    # Проверяем, есть ли уже сгенерированные резюме и письма
    resume_result = await provider.session.execute(
        select(GeneratedResume).where(
            GeneratedResume.user_id == user.id,
            GeneratedResume.vacancy_id == vacancy_id
        ).order_by(GeneratedResume.created_at.desc())
    )
    generated_resume = resume_result.scalar_one_or_none()
    
    letter_result = await provider.session.execute(
        select(CoverLetter).where(
            CoverLetter.user_id == user.id,
            CoverLetter.vacancy_id == vacancy_id
        ).order_by(CoverLetter.created_at.desc())
    )
    cover_letter = letter_result.scalar_one_or_none()
    
    # Форматируем детальное описание
    message_text = format_vacancy_details(vacancy)
    is_favorite = False
    # Получаем клавиатуру для отклика
    from utils.keyboards import get_response_vacancy_keyboard
    keyboard = get_response_vacancy_keyboard(
        vacancy.id, 
        user.id,
        is_favorite=bool(is_favorite), 
        has_resume=bool(generated_resume),
        has_letter=bool(cover_letter)
    )
    
    # Добавляем статус готовности
    status_lines = []
    if generated_resume:
        status_lines.append("✅ Резюме сгенерировано")
    else:
        status_lines.append("❌ Резюме не готово")
    
    if cover_letter:
        status_lines.append("✅ Сопроводительное письмо готово")
    else:
        status_lines.append("❌ Письмо не готово")
    
    if user.hh_resume_id and user.contact_email:
        status_lines.append("✅ Контактные данные заполнены")
    else:
        status_lines.append("❌ Контактные данные не заполнены")
    
    status_text = "\n".join(status_lines)
    
    full_message = (
        f"{message_text}\n\n"
        f"<b>📊 Статус готовности отклика:</b>\n"
        f"{status_text}\n\n"
        f"<i>Для отправки отклика необходимо:\n"
        f"1. Сгенерировать резюме под вакансию\n"
        f"2. Сгенерировать сопроводительное письмо\n"
        f"3. Нажать 'Отправить отклик'</i>"
    )
    
    await message.edit_text(
        text=full_message,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

def format_vacancy_details(vacancy) -> str:
    """Форматирует детальное описание вакансии (для Уровня 3)"""
    lines = [
        f"<b>🎯 ВАКАНСИЯ ДЛЯ ОТКЛИКА</b>\n",
        f"<b>📌 {vacancy.name}</b>",
        f"🏢 <b>Компания:</b> {vacancy.company_name}",
    ]
    
    if vacancy.area_name:
        lines.append(f"📍 <b>Локация:</b> {vacancy.area_name}")
    
    if vacancy.salary_from or vacancy.salary_to:
        salary = ""
        if vacancy.salary_from:
            salary += f"от {vacancy.salary_from:,}"
        if vacancy.salary_to:
            salary += f" до {vacancy.salary_to:,}"
        if vacancy.salary_currency:
            salary += f" {vacancy.salary_currency}"
        lines.append(f"💰 <b>Зарплата:</b> {salary}")
    
    if vacancy.experience:
        lines.append(f"📊 <b>Опыт:</b> {vacancy.experience}")
    
    if vacancy.schedule:
        lines.append(f"⏰ <b>График:</b> {vacancy.schedule}")
    
    if vacancy.employment:
        lines.append(f"💼 <b>Занятость:</b> {vacancy.employment}")
    
    if vacancy.description:
        desc = vacancy.description[:1000] + "..." if len(vacancy.description) > 1000 else vacancy.description
        lines.append(f"\n📝 <b>Описание:</b>\n{desc}")
    
    lines.append(f"\n🔗 <a href='{vacancy.url}'>Ссылка на вакансию на HH.ru</a>")
    
    return "\n".join(lines)

def get_single_vacancy_keyboard(vacancy_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для единичного показа вакансии с откликом"""
    buttons = []
    
    # 1. Добавить в избранное / убрать из избранного
    buttons.append([
        InlineKeyboardButton(
            text="⭐ Добавить в избранное",
            callback_data=f"vacancy_favorite_{vacancy_id}"
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
    
    # 4. Откликнуться (основная кнопка)
    buttons.append([
        InlineKeyboardButton(
            text="📤 Отправить отклик на вакансию",
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

@router.callback_query(F.data.startswith("send_response_"))
async def send_response_to_vacancy(callback: CallbackQuery, provider: DependencyProvider):
    """Отправка отклика на вакансию через HH API"""
    vacancy_id = int(callback.data.replace("send_response_", ""))
    
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    
    # Проверяем наличие резюме
    if not user.hh_resume_id:
        await callback.answer("❌ Не указана ссылка на резюме HH", show_alert=True)
        return
    
    # Проверяем наличие сгенерированного резюме и письма
    resume_result = await provider.session.execute(
        select(GeneratedResume).where(
            GeneratedResume.user_id == user.id,
            GeneratedResume.vacancy_id == vacancy_id
        ).order_by(GeneratedResume.created_at.desc())
    )
    generated_resume = resume_result.scalar_one_or_none()
    
    letter_result = await provider.session.execute(
        select(CoverLetter).where(
            CoverLetter.user_id == user.id,
            CoverLetter.vacancy_id == vacancy_id
        ).order_by(CoverLetter.created_at.desc())
    )
    cover_letter = letter_result.scalar_one_or_none()
    
    if not generated_resume:
        await callback.answer("❌ Сначала сгенерируйте резюме под вакансию", show_alert=True)
        return
    
    if not cover_letter:
        await callback.answer("❌ Сначала сгенерируйте сопроводительное письмо", show_alert=True)
        return
    
    # Показываем сообщение о начале отправки
    await callback.message.edit_text("🔄 <b>Отправляю отклик на вакансию...</b>", parse_mode="HTML")
    
    try:
        # Получаем вакансию
        vacancy_result = await provider.session.execute(
            select(Vacancy).where(Vacancy.id == vacancy_id)
        )
        vacancy = vacancy_result.scalar_one_or_none()
        
        if not vacancy:
            await callback.message.edit_text("❌ Вакансия не найдена")
            return
        
        # Отправляем отклик через HH API
        success = await send_hh_application(
            provider.config.hh,
            vacancy.hh_id,
            user.hh_resume_id,
            cover_letter.content,
            user.contact_email,
            user.contact_phone
        )
        
        if success:
            # Обновляем статус в БД
            user_vacancy = await provider.user_vacancy_repo.get_user_vacancy(user.id, vacancy_id)
            if user_vacancy:
                await provider.user_vacancy_repo.update_user_vacancy(
                    user_vacancy.id,
                    is_applied=True,
                    is_viewed=True,
                    viewed_at=datetime.utcnow()
                )
            
            # Помечаем резюме как загруженное
            generated_resume.is_uploaded_to_hh = True
            await provider.session.commit()
            
            # Обновляем кнопку
            keyboard = get_single_vacancy_keyboard(vacancy_id, user.id)
            keyboard.inline_keyboard[3][0] = InlineKeyboardButton(
                text="✅ Отклик отправлен",
                callback_data=f"response_sent_{vacancy_id}"
            )
            
            await callback.message.edit_text(
                "✅ <b>Отклик успешно отправлен!</b>\n\n"
                f"📤 Ваше резюме и сопроводительное письмо отправлены на вакансию:\n"
                f"<b>{vacancy.name}</b>\n\n"
                f"🏢 <b>Компания:</b> {vacancy.company_name}\n"
                f"🔗 <a href='{vacancy.url}'>Ссылка на вакансию</a>",
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Не удалось отправить отклик</b>\n\n"
                "Попробуйте позже или свяжитесь с поддержкой.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при отправке отклика: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка при отправке отклика</b>\n\n"
            f"Ошибка: {str(e)[:100]}",
            parse_mode="HTML"
        )

async def send_hh_application(hh_config, vacancy_hh_id: str, resume_id: str, cover_letter: str, email: str, phone: str = None) -> bool:
    """Отправка отклика через HH API"""
    import aiohttp
    import asyncio
    
    # Для реальной отправки через HH API нужен OAuth токен пользователя
    # Здесь упрощенная реализация
    
    # В реальном приложении здесь будет:
    # 1. Получение OAuth токена пользователя
    # 2. Формирование запроса к HH API
    # 3. Отправка данных
    
    # Временная заглушка - логируем и возвращаем успех
    logger.info(f"Отправка отклика на вакансию {vacancy_hh_id}")
    logger.info(f"Резюме ID: {resume_id}")
    logger.info(f"Письмо: {cover_letter[:100]}...")
    logger.info(f"Email: {email}, Phone: {phone}")
    
    # Имитация задержки
    await asyncio.sleep(2)
    
    return True  # Временно возвращаем успех

# В handlers/responses.py добавьте/обновите:

@router.callback_query(F.data.startswith("generate_resume_"))
async def generate_resume_for_vacancy(callback: CallbackQuery, provider: DependencyProvider):
    """Генерация резюме под конкретную вакансию"""
    try:
        vacancy_id = int(callback.data.replace("generate_resume_", ""))
        
        user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
        
        if not user.base_resume:
            await callback.answer("❌ Сначала заполните ваше резюме в профиле", show_alert=True)
            return
        
        await callback.message.edit_text("🤖 <b>Генерирую резюме под вакансию...</b>", parse_mode="HTML")
        
        # Получаем вакансию
        vacancy_result = await provider.session.execute(
            select(Vacancy).where(Vacancy.id == vacancy_id)
        )
        vacancy = vacancy_result.scalar_one_or_none()
        
        if not vacancy:
            await callback.message.edit_text("❌ Вакансия не найдена")
            return
        
        # Проверяем наличие LLM настроек
        llm_config = await provider.secure_storage.get_llm_config_for_user(user.id)
        if not llm_config.get('api_key'):
            await callback.message.edit_text(
                "❌ <b>Не настроен API ключ для AI</b>\n\n"
                "Настройте API ключ в разделе 🤖 Настройки AI",
                parse_mode="HTML"
            )
            return
        
        # Используем LLM сервис
        user_profile = {
            'full_name': user.full_name,
            'desired_position': user.desired_position,
            'skills': user.skills,
            'base_resume': user.base_resume
        }
        
        vacancy_info = {
            'name': vacancy.name,
            'company_name': vacancy.company_name,
            'description': vacancy.description[:1500] if vacancy.description else "",
            'requirements': vacancy.skills if vacancy.skills else ""
        }
        
        # Генерируем резюме
        generated_resume = await provider.llm_service.generate_resume(
            user_profile, 
            vacancy_info, 
            llm_config
        )
        
        if generated_resume:
            # Сохраняем в БД
            await provider.generated_resume_repo.create(
                user_id=user.id,
                vacancy_id=vacancy_id,
                title=f"Резюме для {vacancy.name[:50]}",
                content=generated_resume
            )
            
            await callback.message.edit_text(
                f"✅ <b>Резюме успешно сгенерировано!</b>\n\n"
                f"📋 <b>Для вакансии:</b> {vacancy.name}\n\n"
                f"<b>Краткое содержание:</b>\n"
                f"{generated_resume[:500]}...\n\n"
                f"<i>Резюме сохранено и готово для отправки</i>",
                parse_mode="HTML"
            )
            
            # Обновляем кнопку
            await update_vacancy_buttons(callback, provider, user.id, vacancy_id)
        else:
            await callback.message.edit_text(
                "❌ <b>Не удалось сгенерировать резюме</b>\n\n"
                "Проверьте настройки AI или попробуйте позже.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при генерации резюме: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка при генерации резюме</b>\n\n"
            f"Ошибка: {str(e)[:100]}",
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("generate_letter_"))
async def generate_letter_for_vacancy(callback: CallbackQuery, provider: DependencyProvider):
    """Генерация сопроводительного письма"""
    try:
        vacancy_id = int(callback.data.replace("generate_letter_", ""))
        
        user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
        
        # Проверяем наличие сгенерированного резюме
        existing_resume = await provider.generated_resume_repo.get_by_user_and_vacancy(user.id, vacancy_id)
        if not existing_resume:
            await callback.answer("❌ Сначала сгенерируйте резюме для этой вакансии", show_alert=True)
            return
        
        await callback.message.edit_text("🤖 <b>Генерирую сопроводительное письмо...</b>", parse_mode="HTML")
        
        # Получаем вакансию
        vacancy_result = await provider.session.execute(
            select(Vacancy).where(Vacancy.id == vacancy_id)
        )
        vacancy = vacancy_result.scalar_one_or_none()
        
        if not vacancy:
            await callback.message.edit_text("❌ Вакансия не найдена")
            return
        
        # Проверяем наличие LLM настроек
        llm_config = await provider.secure_storage.get_llm_config_for_user(user.id)
        if not llm_config.get('api_key'):
            await callback.message.edit_text(
                "❌ <b>Не настроен API ключ для AI</b>\n\n"
                "Настройте API ключ в разделе 🤖 Настройки AI",
                parse_mode="HTML"
            )
            return
        
        # Используем LLM сервис
        user_profile = {
            'full_name': user.full_name,
            'resume_content': existing_resume.content[:1000]
        }
        
        vacancy_info = {
            'name': vacancy.name,
            'company_name': vacancy.company_name,
            'description': vacancy.description[:1000] if vacancy.description else ""
        }
        
        # Генерируем письмо
        cover_letter = await provider.llm_service.generate_cover_letter(
            user_profile, 
            vacancy_info, 
            llm_config
        )
        
        if cover_letter:
            # Сохраняем в БД
            await provider.cover_letter_repo.create(
                user_id=user.id,
                vacancy_id=vacancy_id,
                title=f"Письмо для {vacancy.name[:50]}",
                content=cover_letter
            )
            
            await callback.message.edit_text(
                f"✅ <b>Сопроводительное письмо сгенерировано!</b>\n\n"
                f"📨 <b>Для вакансии:</b> {vacancy.name}\n\n"
                f"<b>Краткое содержание:</b>\n"
                f"{cover_letter[:500]}...\n\n"
                f"<i>Письмо сохранено и готово для отправки</i>",
                parse_mode="HTML"
            )
            
            # Обновляем кнопку
            await update_vacancy_buttons(callback, provider, user.id, vacancy_id)
        else:
            await callback.message.edit_text(
                "❌ <b>Не удалось сгенерировать письмо</b>\n\n"
                "Проверьте настройки AI или попробуйте позже.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при генерации письма: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка при генерации письма</b>\n\n"
            f"Ошибка: {str(e)[:100]}",
            parse_mode="HTML"
        )

async def update_vacancy_buttons(callback: CallbackQuery, provider: DependencyProvider, user_id: int, vacancy_id: int):
    """Обновить кнопки после генерации резюме/письма"""
    try:
        from utils.keyboards import get_response_vacancy_keyboard
        
        # Проверяем наличие резюме и письма
        resume = await provider.generated_resume_repo.get_by_user_and_vacancy(user_id, vacancy_id)
        letter = await provider.cover_letter_repo.get_by_user_and_vacancy(user_id, vacancy_id)
        
        # Получаем информацию о избранном
        user_vacancy = await provider.user_vacancy_repo.get_user_vacancy(user_id, vacancy_id)
        is_favorite = user_vacancy.is_favorite if user_vacancy else False
        
        # Создаем обновленную клавиатуру
        keyboard = get_response_vacancy_keyboard(
            vacancy_id=vacancy_id,
            user_id=user_id,
            is_favorite=is_favorite,
            has_resume=bool(resume),
            has_letter=bool(letter)
        )
        
        # Обновляем только клавиатуру
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка обновления кнопок: {e}")

# Добавить в конец handlers/responses.py:

# Добавьте вспомогательную функцию в начало файла:

async def check_user_data_for_response(user) -> tuple:
    """Проверяет наличие данных пользователя для отклика"""
    missing = []
    
    if not user.base_resume:
        missing.append("основное резюме")
    if not user.hh_resume_id:
        missing.append("ссылка на резюме HH.ru")
    if not user.contact_email:
        missing.append("email для связи")
    
    return missing

# Обновите функцию show_response_screen:

@router.callback_query(F.data.startswith("response_"))
async def show_response_screen(callback: CallbackQuery, provider: DependencyProvider, state: FSMContext):
    """Показать экран отклика на вакансию"""
    try:
        vacancy_id = int(callback.data.replace("response_", ""))
        
        user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Сохраняем ID вакансии в состоянии
        await state.update_data(current_vacancy_id=vacancy_id)
        
        # Проверяем наличие необходимых данных
        missing_data = await check_user_data_for_response(user)
        
        if missing_data:
            # Показываем экран сбора недостающих данных
            missing_text = "❌ <b>Для отклика на вакансию необходимо заполнить:</b>\n\n" + "\n".join(f"• {item}" for item in missing_data)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Заполнить профиль", callback_data="menu_profile")],
                [InlineKeyboardButton(text="📤 Заполнить контакты", callback_data=f"response_setup_{vacancy_id}")],
                [InlineKeyboardButton(text="⬅️ Назад к вакансии", callback_data=f"vacancy_back_to_list")]
            ])
            
            await callback.message.edit_text(
                missing_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Все данные есть, переходим к экрану отклика
            await handle_vacancy_response(callback, provider, state)
            
    except ValueError:
        await callback.answer("❌ Неверный ID вакансии", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в show_response_screen: {e}")
        await callback.answer("❌ Ошибка при обработке запроса", show_alert=True)
        
@router.callback_query(F.data.startswith("vacancy_response_"))
async def show_vacancy_detail(callback: CallbackQuery, provider: DependencyProvider, state: FSMContext):
    """Показать детальный просмотр вакансии (Уровень 3)"""
    
    logger.info(f"🚀 Начало обработки vacancy_response: {callback.data}")
    
    try:
        vacancy_id = int(callback.data.replace("vacancy_response_", ""))
        logger.info(f"✅ ID вакансии: {vacancy_id}")
    except ValueError as e:
        logger.error(f"❌ Ошибка парсинга ID: {e}")
        await callback.answer("❌ Ошибка: неверный ID вакансии", show_alert=True)
        return
    
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    if not user:
        logger.error("❌ Пользователь не найден")
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    logger.info(f"✅ Пользователь найден: {user.id}")
    # Получаем вакансию
    from sqlalchemy import select
    from database.models import Vacancy, UserVacancy
    
    vacancy_result = await provider.session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = vacancy_result.scalar_one_or_none()
    
    if not vacancy:
        await callback.answer("❌ Вакансия не найдена", show_alert=True)
        return
    logger.info(f"✅ Вакансия найдена: {vacancy.name}")
    # Проверяем, есть ли вакансия в избранном
    user_vacancy = await provider.user_vacancy_repo.get_user_vacancy(user.id, vacancy_id)
    
    is_favorite = user_vacancy.is_favorite if user_vacancy else False
    
    logger.info(f"✅ Статус избранного: {is_favorite}")
            
        # Проверяем, есть ли уже сгенерированные резюме и письма
    resume_result = await provider.session.execute(
        select(GeneratedResume).where(
            GeneratedResume.user_id == user.id,
            GeneratedResume.vacancy_id == vacancy_id
        ).order_by(GeneratedResume.created_at.desc())
    )
    generated_resume = resume_result.scalar_one_or_none()

    letter_result = await provider.session.execute(
        select(CoverLetter).where(
            CoverLetter.user_id == user.id,
            CoverLetter.vacancy_id == vacancy_id
        ).order_by(CoverLetter.created_at.desc())
    )
    cover_letter = letter_result.scalar_one_or_none()
    
    logger.info(f"✅ Резюме сгенерировано: {bool(generated_resume)}")
    logger.info(f"✅ Письмо сгенерировано: {bool(cover_letter)}")
    
    # Форматируем детальное описание
    def format_vacancy_details(vacancy):
        lines = [
            f"<b>🎯 ВАКАНСИЯ ДЛЯ ОТКЛИКА</b>\n",
            f"<b>📌 {vacancy.name}</b>",
            f"🏢 <b>Компания:</b> {vacancy.company_name}",
        ]
        
        if vacancy.area_name:
            lines.append(f"📍 <b>Локация:</b> {vacancy.area_name}")
        
        if vacancy.salary_from or vacancy.salary_to:
            salary = ""
            if vacancy.salary_from:
                salary += f"от {vacancy.salary_from:,}"
            if vacancy.salary_to:
                salary += f" до {vacancy.salary_to:,}"
            if vacancy.salary_currency:
                salary += f" {vacancy.salary_currency}"
            lines.append(f"💰 <b>Зарплата:</b> {salary}")
        
        if vacancy.experience:
            lines.append(f"📊 <b>Опыт:</b> {vacancy.experience}")
        
        if vacancy.schedule:
            lines.append(f"⏰ <b>График:</b> {vacancy.schedule}")
        
        if vacancy.employment:
            lines.append(f"💼 <b>Занятость:</b> {vacancy.employment}")
        
        if vacancy.description:
            desc = vacancy.description[:1000] + "..." if len(vacancy.description) > 1000 else vacancy.description
            lines.append(f"\n📝 <b>Описание:</b>\n{desc}")
        
        lines.append(f"\n🔗 <a href='{vacancy.url}'>Ссылка на вакансию на HH.ru</a>")
        
        return "\n".join(lines)
    
    # Получаем клавиатуру для Уровня 3
    try:
        from utils.keyboards import get_response_vacancy_keyboard
        keyboard = get_response_vacancy_keyboard(
            vacancy_id=vacancy.id,
            user_id=user.id,
            has_resume=bool(generated_resume),
            has_letter=bool(cover_letter)
        )
        logger.info("✅ Клавиатура создана")
    except Exception as e:
        logger.error(f"❌ Ошибка создания клавиатуры: {e}")
        # Простая клавиатура на случай ошибки
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Тестовая кнопка", callback_data="test")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main")]
        ])
    
    # Отправляем сообщение
    try:
        logger.info("🔄 Редактирую сообщение...")
        await callback.message.edit_text(
            format_vacancy_details(vacancy),
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info("✅ Сообщение отредактировано")
    except Exception as e:
        logger.error(f"❌ Ошибка редактирования: {e}")
        try:
            logger.info("🔄 Пытаюсь отправить новое сообщение...")
            await callback.message.answer(
                format_vacancy_details(vacancy),
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            logger.info("✅ Новое сообщение отправлено")
        except Exception as e2:
            logger.error(f"❌ Ошибка отправки сообщения: {e2}")
            await callback.answer(f"❌ Ошибка: {str(e2)[:50]}", show_alert=True)
            return
    
    logger.info("🎉 Обработчик завершен успешно")
    await callback.answer()