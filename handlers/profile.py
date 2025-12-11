
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from asyncio.log import logger
from datetime import datetime, timedelta
from core.dependencies import DependencyProvider
from utils.states import HHAPIStates, ProfileStates, ResponseStates
from utils.keyboards import get_back_to_menu_keyboard
from services.hh_response import HHResponseService  # Нужно создать этот файл или импортировать
from services.hh_auth_manager import HHAuthManager
from utils.logger import get_logger  # <-- ДОБАВИТЬ
from services.local_oauth_server import LocalOAuthServer


logger = get_logger(__name__)  # <-- ДОБАВИТЬ

router = Router()

async def show_profile_callback(callback: CallbackQuery, provider: DependencyProvider):
    """Показать профиль из callback"""
    await _show_profile_internal(callback.message, provider, callback.from_user.id)

async def show_profile_message(message: Message, provider: DependencyProvider):
    """Показать профиль из message"""
    await _show_profile_internal(message, provider, message.from_user.id)

async def _show_profile_internal(message_obj: Message, provider: DependencyProvider, user_id: int):
    """Внутренняя функция показа профиля"""
    try:
        user = await provider.user_repo.get_user_by_telegram_id(str(user_id))
        
        if not user:
            await message_obj.answer("❌ Пользователь не найден")
            return
        
        # Получаем зашифрованные данные через SecureStorageService
        secrets = await provider.secure_storage.get_user_secrets(user.id)
        
        # Определяем статус HeadHunter
        hh_access_token = secrets.get('hh_access_token')
        hh_token_status = "✅ Авторизован" if hh_access_token else "❌ Не авторизован"
        
        # Определяем статус LLM
        llm_config = await provider.secure_storage.get_llm_config_for_user(user.id)
        llm_status = "✅ Настроен" if llm_config.get('api_key') else "❌ Не настроен"
        
        # Получаем статистику
        from database.repository import StatisticsRepository
        stats_repo = StatisticsRepository(provider.session)
        user_stats = await stats_repo.get_user_statistics(user.id)
                
        # Временно используем наличие базового резюме как индикатор
        has_resume = bool(user.base_resume)
        # Получаем количество откликов
        applications_count = user_stats['vacancies'].get('applied', 0) if 'vacancies' in user_stats else 0
        
        # Добавляем email и HH статус
        email_status = user.contact_email or "❌ Не указан"
        phone_status = user.contact_phone or "❌ Не указан"
        hh_encryp_status = "✅ Авторизован" if user.hh_access_token_encrypted else "❌ Не авторизован"
        hh_resume = user.hh_resume_id or "❌ Не указано"
                
        profile_text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"📛 <b>Имя:</b> {user.full_name or 'Не указано'}\n"
            f"📧 <b>Email:</b> {email_status}\n"
            f"📱 <b>Телефон:</b> {phone_status}\n"
            f"🏙️ <b>Город:</b> {user.city or 'Не указан'}\n"
            f"💼 <b>Желаемая должность:</b> {user.desired_position or 'Не указана'}\n"
            f"🛠️ <b>Навыки:</b> {user.skills or 'Не указаны'}\n"
            f"🔑 <b>HH.ru:</b> админ: {hh_token_status} и шифр: {hh_encryp_status}\n"
            f"📋 <b>Резюме на HH:</b> {'✅ Указано' if has_resume else '❌ Не указано'}\n"
            f"⏰ <b>Автопроверка:</b> {'✅ Включена' if user.scheduler_enabled else '❌ Выключена'}\n"
            f"🕐 <b>Время проверок:</b> {user.scheduler_times}\n"
            f"🔄 <b>Интервал:</b> каждые {user.check_interval_hours} часов\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"📨 Откликов: {applications_count}\n\n"
            f"🔗 <b>Интеграции:</b>\n"
            f"• AI Помощник: {llm_status}\n\n"
            f"🕒 <b>Регистрация:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Имя", callback_data="profile_edit_name"),
                InlineKeyboardButton(text="🏙️ Город", callback_data="profile_edit_city")
            ],
            [
                InlineKeyboardButton(text="💼 Должность", callback_data="profile_edit_position"),
                InlineKeyboardButton(text="🛠️ Навыки", callback_data="profile_edit_skills")
            ],
            [
                InlineKeyboardButton(text="📄 Резюме", callback_data="profile_edit_resume"),
                InlineKeyboardButton(text="📧 Email", callback_data="profile_edit_email")
            ],
            [
                InlineKeyboardButton(text="📱 Телефон", callback_data="profile_edit_phone"),
                InlineKeyboardButton(text="🔑 HH Авторизация", callback_data="profile_hh_auth")
            ],
            [
                InlineKeyboardButton(text="⏰ Расписание", callback_data="profile_edit_schedule")
            ],
            [
                InlineKeyboardButton(text="📊 Главное меню", callback_data="menu_main")
            ]
        ])
        
        await message_obj.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")
    
    except Exception as e:
        await message_obj.answer(f"❌ Ошибка при загрузке профиля: {str(e)}")

@router.callback_query(F.data == "menu_profile")
async def menu_profile_handler(callback: CallbackQuery, provider: DependencyProvider):
    """Обработчик кнопки профиля"""
    await show_profile_callback(callback, provider)        

@router.callback_query(F.data.startswith("profile_edit_"))
async def handle_profile_edit(callback: CallbackQuery, state: FSMContext):
    """Обработчик редактирования профиля"""
    action = callback.data.replace("profile_edit_", "")
    
    state_mapping = {
        "name": (ProfileStates.waiting_name, "✏️ Введите ваше имя и фамилию:"),
        "phone": (ProfileStates.waiting_phone, "📱 Введите ваш телефон:"),
        "email": (ProfileStates.waiting_email, "📧 Введите ваш email:"),
        "city": (ProfileStates.waiting_city, "🏙️ Введите ваш город:"),
        "position": (ProfileStates.waiting_position, "💼 Введите желаемую должность:"),
        "skills": (ProfileStates.waiting_skills, "🛠️ Введите ваши навыки:"),
        "resume": (ProfileStates.waiting_resume, "📄 Введите текст вашего резюме:"),
        "schedule": (ProfileStates.waiting_schedule, "⏰ Настройте расписание проверок:")
    }
    
    if action in state_mapping:
        state_class, message_text = state_mapping[action]
        await state.set_state(state_class)
    
        if action == "phone":
            message_text += "\n\n<i>Телефон будет использоваться для связи с работодателями и будет зашифрован</i>"
        elif action == "email":
            message_text += "\n\n<i>Email будет зашифрован и сохранен безопасно</i>"
    
        await callback.message.edit_text(
            f"{message_text}\n\n<i>Отправьте текст или нажмите 'Отмена' для возврата</i>",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()

@router.message(ProfileStates.waiting_name)
async def process_name(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода имени"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        full_name=message.text
    )
    await message.answer("✅ Имя успешно обновлено!")
    await state.clear()
    await show_profile_message(message, provider)

@router.message(ProfileStates.waiting_city)
async def process_city(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода города"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        city=message.text
    )
    await message.answer("✅ Город успешно обновлен!")
    await state.clear()
    await show_profile_message(message, provider)

@router.message(ProfileStates.waiting_position)
async def process_position(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода должности"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        desired_position=message.text
    )
    await message.answer("✅ Должность успешно обновлена!")
    await state.clear()
    await show_profile_message(message, provider)

@router.message(ProfileStates.waiting_skills)
async def process_skills(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода навыков"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        skills=message.text
    )
    await message.answer("✅ Навыки успешно обновлены!")
    await state.clear()
    await show_profile_message(message, provider)

# Добавьте новые обработчики в конец файла:
@router.callback_query(F.data == "profile_edit_phone")
async def edit_phone_profile(callback: CallbackQuery, state: FSMContext):
    print("🟢 КНОПКА ТЕЛЕФОНА НАЖАТА")
    print(f"🔵 [PHONE BUTTON] User: {callback.from_user.id}, Data: {callback.data}")
    print(f"🔵 [PHONE BUTTON] Setting state to: {ProfileStates.waiting_phone}")
    """Редактирование телефона с шифрованием"""
    await state.set_state(ProfileStates.waiting_phone)
    
    # Сохраняем user_id в состоянии для проверки
    await state.update_data(user_id=callback.from_user.id, action="phone")
    
    print(f"🔵 [PHONE BUTTON] State set successfully")

    await callback.message.edit_text(
        "📱 <b>Введите ваш телефон:</b>\n\n"
        "<i>Телефон будет использоваться для связи с работодателями и будет зашифрован</i>",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(ProfileStates.waiting_phone)
async def process_phone_profile(message: Message, state: FSMContext, provider: DependencyProvider):
    print(f"🟢 ПОЛУЧЕН ТЕЛЕФОН: {message.text}")
    """Обработка ввода телефона с шифрованием"""
    print(f"🟢 [PHONE INPUT] User: {message.from_user.id}, Text: {message.text}")
    print(f"🟢 [PHONE INPUT] Current state: {await state.get_state()}")
    
    # Проверяем данные состояния
    data = await state.get_data()
    print(f"🟢 [PHONE INPUT] State data: {data}")
    """Обработка ввода телефона с шифрованием"""
    phone = message.text.strip()
    import re
    phone_pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    
    if not re.match(phone_pattern, message.text.replace(" ", "")):
        await message.answer("❌ Неверный формат телефона. Попробуйте еще раз:")
        return
    # Простая валидация
    if len(phone) < 5:
        await message.answer("❌ Телефон слишком короткий. Попробуйте еще раз:")
        return
    
    # Сохраняем с шифрованием
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        await state.clear()
        return
    
    # Преобразуем user.id в int
    user_id = int(user.id) if hasattr(user.id, '__int__') else user.id
    
    success = await provider.secure_storage.encrypt_and_save(user_id, 'contact_phone', phone)
    
    if success:
        await message.answer("✅ Телефон сохранен и зашифрован!")
        # Также сохраняем в открытом виде для обратной совместимости (можно убрать позже)
        await provider.user_repo.update_user_profile(
            str(message.from_user.id),
            contact_phone=phone
        )
    else:
        await message.answer("❌ Ошибка при сохранении телефона")
    
    await state.clear()
    await show_profile_message(message, provider)

@router.callback_query(F.data == "profile_hh_auth")
async def hh_auth_from_profile(callback: CallbackQuery, state: FSMContext, provider: DependencyProvider):
    """Авторизация HH из профиля"""
    hh_response_service = HHResponseService(provider.config.hh)
    auth_url = hh_response_service.get_auth_url("profile_auth")
    
    
    await callback.message.edit_text(
        "🔑 <b>Авторизация на HH.ru для получения API ключей</b>\n\n"
        "Для отправки откликов необходимо получить доступ к HH API:\n\n"
        "1. Перейдите по ссылке ниже (откроется dev.hh.ru)\n"
        "2. Нажмите 'Создать приложение' или используйте существующее\n"
        "3. В разделе 'Мои приложения' создайте OAuth приложение\n"
        "4. Получите Client ID и Client Secret\n"
        "5. Сохраните их в безопасном месте\n\n"
        f"🔗 <a href='https://dev.hh.ru/admin'>Панель разработчика HH.ru</a>\n\n"
        "<i>После создания приложения введите Client ID и Client Secret по очереди</i>",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=False
    )
    
    await state.set_state(HHAPIStates.waiting_client_id)

# Добавить обработку кода авторизации
@router.message(ResponseStates.waiting_hh_auth)
async def process_hh_auth_code_profile(message: Message, state: FSMContext, provider: DependencyProvider):
    """НОВАЯ ЛОГИКА: Запуск OAuth потока с локальным сервером"""
    
    # 1. Получаем пользователя
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    # 2. Получаем сохраненные client_id и client_secret (они должны быть уже введены пользователем)
    #secrets = await provider.secure_storage.get_user_secrets(user.id)
    #client_id = secrets.get('hh_client_id')
    #client_secret = secrets.get('hh_client_secret')
    from core.config import get_config
    # Берем ключи напрямую из конфига (.env файла)
    config = get_config()
    client_id = config.hh.client_id
    client_secret = config.hh.client_secret
    
    # Добавьте проверку
    if not client_id or not client_secret:
        await message.answer("❌ Client ID или Secret не найдены в .env файле.")
        await state.clear()
        return
    
    if not client_id or not client_secret:
        await message.answer("❌ Сначала сохраните Client ID и Client Secret в настройках HH API.")
        await state.clear()
        return
    
    # 3. Создаем менеджер авторизации
    from services.hh_auth_manager import HHAuthManager
    auth_manager = HHAuthManager(client_id, client_secret)
    
    # 4. Получаем URL для авторизации (передаем user.id в state для безопасности)
    auth_url = auth_manager.get_auth_url(str(user.id))
    
    # 5. Запускаем локальный сервер и ожидаем код
    await message.answer("🔄 <b>Открываю окно авторизации HH.ru...</b>\n\n"
                        "<i>Если браузер не открылся автоматически, скопируйте эту ссылку:</i>\n"
                        f"<code>{auth_url[:100]}...</code>", 
                        parse_mode="HTML")
    
    oauth_server = LocalOAuthServer()
    code_data = await oauth_server.wait_for_code(auth_url)
    
    # 6. Обрабатываем результат
    if not code_data:
        await message.answer("❌ <b>Не удалось получить код авторизации.</b>\n\n"
            "Возможные причины:\n"
            "• Время ожидания истекло (более 3 минут)\n"
            "• Вы не завершили авторизацию в браузере\n"
            "• Порт 8080 занят другим приложением", 
            parse_mode="HTML")
        await state.clear()
        return
    
    auth_code, received_state = code_data
    
    # Проверяем state для безопасности (опционально)
    if received_state != str(user.id):
        await message.answer("⚠️ <b>Ошибка безопасности при авторизации.</b> Попробуйте еще раз.", parse_mode="HTML")
        await state.clear()
        return
    
    # 7. Обмениваем код на токен
    await message.answer("🔑 <b>Получаю токен доступа...</b>", parse_mode="HTML")
    
    token_data = await auth_manager.exchange_code_for_token(auth_code)
    
    if token_data and 'access_token' in token_data:
        # 8. Сохраняем токены через secure_storage
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 3600)
        
        # Сохраняем каждый токен
        success_access = await provider.secure_storage.encrypt_and_save(
            user.id, 'hh_access_token', access_token
        )
        
        if refresh_token:
            success_refresh = await provider.secure_storage.encrypt_and_save(
                user.id, 'hh_refresh_token', refresh_token
            )
        
        # Обновляем срок действия
        from datetime import datetime, timedelta
        await provider.user_repo.update_user_profile(
            str(message.from_user.id),
            hh_token_expires=datetime.utcnow() + timedelta(seconds=expires_in)
        )
        
        await message.answer(
            f"✅ <b>Авторизация успешна!</b>\n\n"
            f"🔑 Токен доступа получен и сохранен\n"
            f"⏰ Срок действия: {expires_in // 86400} дней\n\n"
            f"Теперь можно отправлять отклики на вакансии!",
            parse_mode="HTML"
        )
        
    else:
        await message.answer(
            "❌ <b>Не удалось получить токен</b>\n\n"
            "Возможные причины:\n"
            "1. Код авторизации неверен или устарел\n"
            "2. Client ID/Secret не совпадают с приложением\n"
            "3. С момента получения кода прошло больше 10 минут\n\n"
            "Попробуйте получить новый код авторизации",
            parse_mode="HTML"
        )
    
    # 9. Очищаем состояние FSM
    await state.clear()
    
    # 10. Показываем обновленный профиль
    from handlers.profile import show_profile_message
    await show_profile_message(message, provider)

@router.message(ProfileStates.waiting_resume)
async def process_resume(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода резюме"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        base_resume=message.text
    )
    await message.answer("✅ Резюме успешно обновлено!")
    await state.clear()
    await show_profile_message(message, provider)

@router.callback_query(F.data == "hh_connect")
async def connect_hh(callback: CallbackQuery, provider: DependencyProvider):
    """Подключение к HH.ru"""
    
    config = provider.config
    auth_url = (
        f"https://hh.ru/oauth/authorize?"
        f"response_type=code&"
        f"client_id={config.hh.client_id}&"
        f"redirect_uri=http://127.0.0.1:8080/callback"
    )
    
    await callback.message.answer(
        f"🔗 Для подключения к HH.ru перейдите по ссылке:\n\n"
        f"{auth_url}\n\n"
        f"После авторизации отправьте мне полученный код.",
        parse_mode="HTML"
    )



@router.callback_query(F.data == "profile_edit_email")
async def edit_email_profile(callback: CallbackQuery, state: FSMContext):
    print("🟢 КНОПКА ТЕЛЕФОНА НАЖАТА")
    print(f"🔵 [email BUTTON] User: {callback.from_user.id}, Data: {callback.data}")
    print(f"🔵 [email BUTTON] Setting state to: {ProfileStates.waiting_phone}")
    """Редактирование email с шифрованием"""
    await state.set_state(ProfileStates.waiting_email)
    await state.update_data(user_id=callback.from_user.id, action="phone")
    
    print(f"🔵 [email BUTTON] State set successfully")
    await callback.message.edit_text(
        "📧 <b>Введите ваш email:</b>\n\n"
        "<i>Email будет зашифрован и сохранен безопасно</i>",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(ProfileStates.waiting_email)
async def process_email_profile(message: Message, state: FSMContext, provider: DependencyProvider):
    print(f"🟢 [email INPUT] User: {message.from_user.id}, Text: {message.text}")
    print(f"🟢 [email INPUT] Current state: {await state.get_state()}")
    
    # Проверяем данные состояния
    data = await state.get_data()
    print(f"🟢 [email INPUT] State data: {data}")
    """Обработка ввода email с шифрованием"""
    import re
    email = message.text.strip()
    
    # Простая валидация email
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        await message.answer("❌ Неверный формат email. Попробуйте еще раз:")
        return
    
    # Проверяем user и получаем ID как int
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    if not user:
        await message.answer("❌ Пользователь не найден")
        await state.clear()
        return
    
    # Преобразуем user.id в int
    user_id = int(user.id) if hasattr(user.id, '__int__') else user.id
    
    
    # Сохраняем с шифрованием
    #user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
        
    success = await provider.secure_storage.encrypt_and_save(user_id, 'contact_email', email)
    
    if success:
        await message.answer("✅ Email сохранен и зашифрован!")
        # Также сохраняем в открытом виде для обратной совместимости
        await provider.user_repo.update_user_profile(
            str(message.from_user.id),
            contact_email=email
        )
    else:
        await message.answer("❌ Ошибка при сохранении email")
    
    await state.clear()
    await show_profile_message(message, provider)  # Показываем обновленный профиль

@router.message(HHAPIStates.waiting_client_id)
async def process_client_id_profile(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка Client ID из профиля"""
    client_id = message.text.strip()
    
    if len(client_id) < 10:
        await message.answer("❌ Client ID слишком короткий. Проверьте правильность.")
        return
    
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    # Преобразуем ID как в других местах
    user_id = int(user.id) if hasattr(user.id, '__int__') else user.id
    
    # Сохраняем с шифрованием
    success = await provider.secure_storage.encrypt_and_save(user_id, 'hh_client_id', client_id)
    
    if success:
        # Также обновляем конфиг
        provider.config.hh.client_id = client_id
        
        await message.answer("✅ Client ID сохранен и зашифрован! Теперь введите Client Secret:")
        await state.set_state(HHAPIStates.waiting_client_secret)
    else:
        await message.answer("❌ Ошибка при сохранении Client ID. Попробуйте еще раз.")

@router.message(HHAPIStates.waiting_client_secret)
async def process_client_secret_profile(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка Client Secret из профиля"""
    client_secret = message.text.strip()
    
    if len(client_secret) < 20:
        await message.answer("❌ Client Secret слишком короткий. Проверьте правильность.")
        return
    
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    # Преобразуем ID как в других местах
    user_id = int(user.id) if hasattr(user.id, '__int__') else user.id
    
    # Сохраняем с шифрованием
    success = await provider.secure_storage.encrypt_and_save(user_id, 'hh_client_secret', client_secret)
    
    if success:
        # Также обновляем конфиг
        provider.config.hh.client_secret = client_secret
        
        await message.answer("✅ Client Secret сохранен и зашифрован!")
        
        # Предлагаем получить OAuth токен
        from services.hh_response import HHResponseService
        hh_response_service = HHResponseService(provider.config.hh)
        auth_url = hh_response_service.get_auth_url("profile_auth")
        
        await message.answer(
            "🔗 <b>Ключи сохранены! Теперь получите токен доступа:</b>\n\n"
            f"1. Перейдите по ссылке:\n{auth_url}\n\n"
            f"2. Авторизуйтесь на HH.ru\n"
            f"3. Скопируйте код авторизации из адресной строки\n"
            f"4. Отправьте его мне",
            parse_mode="HTML"
        )
        
        await state.set_state(ResponseStates.waiting_hh_auth)
        
    else:
        await message.answer("❌ Ошибка при сохранении Client Secret. Попробуйте еще раз.")

@router.callback_query(F.data == "refresh_hh_token")
async def refresh_hh_token(callback: CallbackQuery, provider: DependencyProvider):
    """Обновление токена HH"""
    await callback.answer("🔄 Обновляю токен...")
    
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    user_id = int(user.id) if hasattr(user.id, '__int__') else user.id
    
    # Получаем сохраненные данные
    secrets = await provider.secure_storage.get_user_secrets(user_id)
    client_id = secrets.get('hh_client_id')
    client_secret = secrets.get('hh_client_secret')
    refresh_token = secrets.get('hh_refresh_token')
    
    if not all([client_id, client_secret, refresh_token]):
        await callback.message.answer("❌ Недостаточно данных для обновления токена")
        return
    
    auth_manager = HHAuthManager(client_id, client_secret)
    token_data = await auth_manager.refresh_access_token(refresh_token)
    
    if token_data and 'access_token' in token_data:
        # Обновляем токены в secure storage
        await provider.secure_storage.encrypt_and_save(
            user_id, 'hh_access_token', token_data['access_token']
        )
        
        if 'refresh_token' in token_data:
            await provider.secure_storage.encrypt_and_save(
                user_id, 'hh_refresh_token', token_data['refresh_token']
            )
        
        # Обновляем срок действия
        if 'expires_in' in token_data:
            expiry_time = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            await provider.user_repo.update_user_profile(
                str(callback.from_user.id),
                hh_token_expires=expiry_time
            )
        
        await callback.message.answer("✅ Токен успешно обновлен!")
    else:
        await callback.message.answer("❌ Не удалось обновить токен. Требуется повторная авторизация.")
        
'''
@router.callback_query(F.data == "test_phone")
async def test_phone_button(callback: CallbackQuery):
    """Тестовая функция для проверки работы кнопки телефона"""
    print(f"🟢 ТЕСТ: Кнопка телефона нажата! User: {callback.from_user.id}")
    await callback.answer("✅ Тестовая кнопка телефона работает!", show_alert=True)

@router.callback_query(F.data == "test_email")
async def test_email_button(callback: CallbackQuery):
    """Тестовая функция для проверки работы кнопки email"""
    print(f"🟢 ТЕСТ: Кнопка email нажата! User: {callback.from_user.id}")
    await callback.answer("✅ Тестовая кнопка email работает!", show_alert=True)
'''

