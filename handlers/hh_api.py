from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from core.dependencies import DependencyProvider
from utils.states import HHAPIStates
from utils.keyboards import get_back_to_menu_keyboard

from utils.logger import get_logger
logger = get_logger(__name__)
router = Router()

@router.callback_query(F.data == "hh_api_settings")
async def show_hh_api_settings(callback: CallbackQuery, provider: DependencyProvider):
    """Показать настройки HH API"""
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    
    # Маскируем чувствительные данные
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    client_id_status = "✅ Установлен (зашифрован)" if user.hh_client_id_encrypted else "❌ Не настроено"
    client_secret_status = "✅ Установлен (зашифрован)" if user.hh_client_secret_encrypted else "❌ Не настроено"
    
    settings_text = (
        "🔐 <b>Настройки HH API</b>\n\n"
        f"🆔 <b>Client ID:</b> {client_id_status}\n"
        f"🔒 <b>Client Secret:</b> {client_secret_status}\n\n"
        "💡 <i>Для работы с HH API необходимо создать OAuth приложение на dev.hh.ru</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🆔 Установить Client ID", callback_data="hh_set_client_id"),
            InlineKeyboardButton(text="🔒 Установить Client Secret", callback_data="hh_set_client_secret")
        ],
        [
            InlineKeyboardButton(text="📝 Инструкция по получению ключей", callback_data="hh_api_guide")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main")
        ]
    ])
    
    await callback.message.edit_text(settings_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "hh_set_client_id")
async def set_client_id(callback: CallbackQuery, state: FSMContext):
    """Запрос Client ID с шифрованием"""
    await state.set_state(HHAPIStates.waiting_client_id)
    await callback.message.edit_text(
        "🆔 <b>Введите Client ID:</b>\n\n"
        "<i>Получите Client ID на https://dev.hh.ru/admin</i>\n"
        "<i>Ключ будет зашифрован и сохранен безопасно</i>",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "hh_set_client_secret")
async def set_client_secret(callback: CallbackQuery, state: FSMContext):
    """Запрос Client Secret с шифрованием"""
    await state.set_state(HHAPIStates.waiting_client_secret)
    await callback.message.edit_text(
        "🔒 <b>Введите Client Secret:</b>\n\n"
        "<i>Получите Client Secret на https://dev.hh.ru/admin</i>\n"
        "<i>Этот ключ будет зашифрован и сохранен максимально безопасно</i>",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )

@router.message(HHAPIStates.waiting_client_id)
async def process_client_id(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка Client ID с шифрованием"""
    client_id = message.text.strip()
    
    if len(client_id) < 10:
        await message.answer("❌ Client ID слишком короткий. Проверьте правильность.")
        return
    
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    # ПРЕОБРАЗОВАНИЕ ID как в profile.py
    user_id = int(user.id) if hasattr(user.id, '__int__') else user.id
    # Сохраняем с шифрованием
    success = await provider.secure_storage.encrypt_and_save(user_id, 'hh_client_id', client_id)
    
    if success:
        # Также обновляем конфиг для текущей сессии
        provider.config.hh.client_id = client_id
        
        await message.answer("✅ Client ID сохранен и зашифрован!")
        await state.clear()
        await show_hh_api_settings(message, provider)
    else:
        await message.answer("❌ Ошибка при сохранении Client ID. Попробуйте еще раз.")

@router.message(HHAPIStates.waiting_client_secret)
async def process_client_secret(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка Client Secret с шифрованием"""
    client_secret = message.text.strip()
    
    if len(client_secret) < 20:
        await message.answer("❌ Client Secret слишком короткий. Проверьте правильность.")
        return
    
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    # ПРЕОБРАЗОВАНИЕ ID как в profile.py
    user_id = int(user.id) if hasattr(user.id, '__int__') else user.id
    # Сохраняем с шифрованием
    success = await provider.secure_storage.encrypt_and_save(user_id, 'hh_client_secret', client_secret)
    
    if success:
        # Также обновляем конфиг для текущей сессии
        provider.config.hh.client_secret = client_secret
        
        await message.answer("✅ Client Secret сохранен и зашифрован!")
        await state.clear()
        await show_hh_api_settings(message, provider)
    else:
        await message.answer("❌ Ошибка при сохранении Client Secret. Попробуйте еще раз.")

@router.callback_query(F.data == "hh_api_guide")
async def show_hh_api_guide(callback: CallbackQuery):
    """Показать инструкцию по получению HH API ключей"""
    guide_text = """
📋 <b>Инструкция по получению HH API ключей</b>

1. <b>Перейдите на страницу разработчика:</b>
   🔗 https://dev.hh.ru/admin

2. <b>Авторизуйтесь</b> или создайте аккаунт

3. <b>Создайте OAuth приложение:</b>
   • Нажмите "Создать приложение"
   • Выберите тип "OAuth"
   • Заполните обязательные поля

4. <b>Получите ключи:</b>
   • <b>Client ID</b> - публичный идентификатор
   • <b>Client Secret</b> - секретный ключ (храните в тайне!)

5. <b>Настройте redirect URI:</b>
   • В настройках приложения укажите:
   • https://hh.ru (для тестирования)

6. <b>Введите ключи в бота</b> в соответствующие поля

⚠️ <b>Внимание:</b>
• Никогда не делитесь Client Secret
• Ключи сохраняются в зашифрованном виде
• Для продакшена используйте безопасный redirect URI
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Открыть dev.hh.ru", url="https://dev.hh.ru/admin")],
        [InlineKeyboardButton(text="⚙️ Настройка HH API", callback_data="hh_api_settings")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main")]
    ])
    
    await callback.message.edit_text(guide_text, reply_markup=keyboard, parse_mode="HTML")

async def show_hh_api_settings(message: Message, provider: DependencyProvider):
    """Вспомогательная функция"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    client_id = provider.config.hh.client_id or "❌ Не настроено"
    client_secret = provider.config.hh.client_secret or "❌ Не настроено"
    
    if client_id != "❌ Не настроено" and len(client_id) > 8:
        client_id = f"{client_id[:4]}...{client_id[-4:]}"
    if client_secret != "❌ Не настроено" and len(client_secret) > 8:
        client_secret = f"{client_secret[:4]}...{client_secret[-4:]}"
    
    settings_text = (
        "🔐 <b>Настройки HH API</b>\n\n"
        f"🆔 <b>Client ID:</b> {client_id}\n"
        f"🔒 <b>Client Secret:</b> {client_secret}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚙️ Настройка HH API", callback_data="hh_api_settings"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main")
        ]
    ])
    
    await message.answer(settings_text, reply_markup=keyboard, parse_mode="HTML")
    
