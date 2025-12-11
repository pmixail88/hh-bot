from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.dependencies import DependencyProvider
from utils.states import LLMStates
from utils.keyboards import get_back_to_menu_keyboard

router = Router()

# handlers/llm.py - обновить обработчики

@router.callback_query(F.data == "menu_llm_settings")
async def show_llm_settings(callback: CallbackQuery, provider: DependencyProvider):
    """Показать настройки AI с учетом конфигурации из .env"""
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    if not llm_settings:
        await callback.answer("❌ Настройки AI не найдены", show_alert=True)
        return

    # Получаем конфигурацию с учетом .env
    llm_config = await provider.secure_storage.get_llm_config_for_user(user.id)
    
    # Определяем статус ключа
    if llm_config.get('source') == 'env':
        api_key_status = "✅ Из .env файла"
    elif llm_config.get('source') == 'encrypted_storage':
        api_key_status = "✅ Зашифрован в БД"
    elif llm_config.get('source') == 'plain_storage':
        api_key_status = "✅ Сохранен в БД"
    else:
        api_key_status = "❌ Не установлен"
    
    settings_text = (
        "🤖 <b>Настройки AI помощника</b>\n\n"
        f"🌐 <b>Base URL:</b> {llm_config.get('base_url', 'Не установлен')}\n"
        f"🔑 <b>API Key:</b> {api_key_status}\n"
        f"⚙️ <b>Model:</b> {llm_config.get('model_name', 'Не установлена')}\n"
        f"🌡️ <b>Temperature:</b> {llm_settings.temperature}\n"
        f"📝 <b>Max Tokens:</b> {llm_settings.max_tokens}\n\n"
    )
    
    # Добавляем информацию о необходимости ввода
    if llm_config.get('requires_user_input', False):
        settings_text += "⚠️ <b>Требуется настройка:</b> введите API ключ\n\n"
    
    settings_text += (
        f"📋 <b>Функции:</b>\n"
        f"• Генерация резюме: {'✅' if llm_settings.enable_resume_generation else '❌'}\n"
        f"• Сопроводительные письма: {'✅' if llm_settings.enable_cover_letter_generation else '❌'}\n"
        f"• Анализ вакансий: {'✅' if llm_settings.enable_vacancy_analysis else '❌'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 API Key", callback_data="llm_edit_api_key"),
            InlineKeyboardButton(text="🌐 Base URL", callback_data="llm_edit_base_url")
        ],
        [
            InlineKeyboardButton(text="⚙️ Model", callback_data="llm_edit_model"),
            InlineKeyboardButton(text="🌡️ Temperature", callback_data="llm_edit_temperature")
        ],
        [
            InlineKeyboardButton(text="📊 Главное меню", callback_data="menu_main")
        ]
    ])
    
    await callback.message.edit_text(settings_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("llm_edit_"))
async def handle_llm_edit(callback: CallbackQuery, state: FSMContext, provider: DependencyProvider):
    """Обработчик редактирования настроек LLM с проверкой необходимости ключа"""
    setting = callback.data.replace("llm_edit_", "")
    
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    
    if setting == "model":
        # Проверяем, нужно ли запрашивать ключ при смене модели
        await state.update_data(editing_llm_model=True)
        
        # Получаем текущую модель
        llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
        current_model = llm_settings.model_name if llm_settings else None
        
        await callback.message.edit_text(
            "⚙️ <b>Введите название новой модели:</b>\n\n"
            f"<i>Текущая модель: {current_model or 'Не установлена'}</i>\n\n"
            "Примеры моделей:\n"
            "• gpt-4o-mini\n• gpt-3.5-turbo\n• claude-3-haiku\n• gemini-pro",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(LLMStates.waiting_model)
        
    elif setting == "api_key":
        # Проверяем нужно ли запрашивать ключ
        should_ask = await provider.secure_storage.should_ask_for_llm_key(user.id)
        
        if not should_ask:
            # Ключ есть в .env или у пользователя
            llm_config = await provider.secure_storage.get_llm_config_for_user(user.id)
            
            await callback.message.edit_text(
                f"🔑 <b>API ключ уже настроен</b>\n\n"
                f"Источник: {llm_config.get('source', 'неизвестно')}\n"
                f"Model: {llm_config.get('model_name', 'Не установлена')}\n\n"
                f"<i>Ключ загружен автоматически. "
                f"Для изменения введите новый ключ или оставьте пустым:</i>",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "🔑 <b>Введите ваш API ключ:</b>\n\n"
                "<i>Если ключ указан в .env файле, можно оставить поле пустым</i>",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
        
        await state.set_state(LLMStates.waiting_api_key)
        
    else:
        # Остальные настройки
        state_mapping = {
            "base_url": (LLMStates.waiting_base_url, "🌐 Введите Base URL:"),
            "temperature": (LLMStates.waiting_temperature, "🌡️ Введите значение temperature (0.0-1.0):"),
        }
        
        if setting in state_mapping:
            state_class, message_text = state_mapping[setting]
            await state.set_state(state_class)
            await callback.message.edit_text(
                f"{message_text}\n\n<i>Отправьте значение или нажмите 'Отмена' для возврата</i>",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Неизвестная настройка", show_alert=True)

@router.message(LLMStates.waiting_model)
async def process_model(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода модели"""
    model_name = message.text.strip()
    
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    # Получаем данные из состояния
    data = await state.get_data()
    is_model_change = data.get('editing_llm_model', False)
    
    if is_model_change:
        # Проверяем, нужно ли запрашивать ключ при смене модели
        should_ask = await provider.secure_storage.should_ask_for_llm_key(user.id, model_name)
        
        if should_ask:
            # Нужно запросить все данные
            await message.answer(
                "🔑 <b>Смена модели требует обновления настроек</b>\n\n"
                f"Новая модель: <b>{model_name}</b>\n\n"
                "Пожалуйста, введите API ключ для этой модели:",
                parse_mode="HTML"
            )
            await state.update_data(new_model_name=model_name)
            await state.set_state(LLMStates.waiting_api_key)
            return
    
    # Просто обновляем модель
    if llm_settings:
        await provider.llm_settings_repo.update_settings(llm_settings.id, model_name=model_name)
        await message.answer(f"✅ Модель сохранена: {model_name}")
    else:
        await message.answer("❌ Не удалось сохранить модель")
    
    await state.clear()
    await _show_llm_settings_message(message, provider)


@router.message(LLMStates.waiting_api_key)
async def process_api_key(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода API ключа с шифрованием"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    # Сохраняем с шифрованием
    success = await provider.secure_storage.encrypt_and_save(user.id, 'llm_api_key', message.text)
    
    if success:
        # Также сохраняем в LLM настройки для обратной совместимости
        llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
        if llm_settings:
            await provider.llm_settings_repo.update_settings(llm_settings.id, api_key=message.text)
        
        await message.answer("✅ API ключ сохранен и зашифрован!")
    else:
        await message.answer("❌ Ошибка при сохранении API ключа")
    
    await state.clear()
    await _show_llm_settings_message(message, provider)

@router.message(LLMStates.waiting_base_url)
async def process_base_url(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода Base URL"""
    if not message.text.startswith(('http://', 'https://')):
        await message.answer("❌ URL должен начинаться с http:// или https://")
        return
        
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    await provider.llm_settings_repo.update_settings(llm_settings.id, base_url=message.text)
    await message.answer("✅ Base URL сохранен!")
    await state.clear()
    await _show_llm_settings_message(message, provider)



@router.message(LLMStates.waiting_temperature)
async def process_temperature(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода температуры"""
    try:
        temperature = float(message.text)
        if not 0.0 <= temperature <= 1.0:
            await message.answer("❌ Temperature должен быть между 0.0 и 1.0")
            return
    except ValueError:
        await message.answer("❌ Введите число (например: 0.7)")
        return
        
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    await provider.llm_settings_repo.update_settings(llm_settings.id, temperature=temperature)
    await message.answer("✅ Temperature сохранен!")
    await state.clear()
    await _show_llm_settings_message(message, provider)

async def _show_llm_settings_message(message: Message, provider: DependencyProvider):
    """Вспомогательная функция для показа настроек LLM (для использования из message)"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    api_key_status = "❌ Не установлен"
    if llm_settings.api_key:
        api_key_status = "✅ Установлен"
    
    settings_text = (
        "🤖 <b>Настройки LLM</b>\n\n"
        f"🌐 <b>Base URL:</b> {llm_settings.base_url or 'Не установлен'}\n"
        f"🔑 <b>API Key:</b> {api_key_status}\n"
        f"⚙️ <b>Model:</b> {llm_settings.model_name or 'Не установлена'}\n"
        f"🌡️ <b>Temperature:</b> {llm_settings.temperature}\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 Настроить", callback_data="menu_llm_settings"),
            InlineKeyboardButton(text="📊 Главное меню", callback_data="menu_main")
        ]
    ])
    
    await message.answer(settings_text, reply_markup=keyboard, parse_mode="HTML")