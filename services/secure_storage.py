# services/secure_storage.py
import base64
import hashlib
import logging
import os
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from utils.logger import get_logger  # Добавить

logger = get_logger(__name__)  # Добавить

#logger = logging.getLogger(__name__)


class EncryptionService:
    """Служба шифрования для генерации ключей и хешей"""
    
    @staticmethod
    def generate_key_pair() -> tuple:
        """Генерация пары ключ-соль"""
        # Генерируем случайную соль
        salt = os.urandom(16)
        
        # Генерируем пароль
        import secrets
        password = secrets.token_urlsafe(32).encode()
        
        # Создаем ключ из пароля и соли
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return key, salt
    
    @staticmethod
    def secure_hash(data: str) -> str:
        """Создание безопасного хеша данных"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def verify_hash(data: str, hash_value: str) -> bool:
        """Проверка хеша данных"""
        return hashlib.sha256(data.encode()).hexdigest() == hash_value


# Глобальный экземпляр службы шифрования
encryption_service = EncryptionService()


class SecureStorageService:
    """Служба безопасного хранения чувствительных данных"""
    encrypted_fields = [
        'llm_api_key',
        'openai_api_key',
        'anthropic_api_key',
        'google_api_key'
    ]
    
    def __init__(self, user_repo, llm_settings_repo=None):
        self.user_repo = user_repo
        self.llm_settings_repo = llm_settings_repo  # Добавьте этот параметр
        self._user_keys_cache: Dict[str, Fernet] = {}
        self._env_config_cache: Dict[str, str] = {}
        
        # Загружаем конфигурацию из .env при инициализации
        self._load_env_config()
    
    def _load_env_config(self):
        """Загрузка конфигурации из .env файла"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            # Читаем LLM настройки из .env
            self._env_config_cache = {
                'llm_api_key': os.getenv('LLM_API_KEY', ''),
                'llm_base_url': os.getenv('LLM_BASE_URL', ''),
                'llm_model_name': os.getenv('LLM_MODEL_NAME', ''),
                'hh_client_id': os.getenv('HH_CLIENT_ID', ''),
                'hh_client_secret': os.getenv('HH_CLIENT_SECRET', '')
            }
            
            logger.info("Конфигурация из .env загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации из .env: {e}")
    
    def _has_env_config(self, field_name: str) -> bool:
        """Проверяет, есть ли значение в .env конфигурации"""
        value = self._env_config_cache.get(field_name, '')
        return bool(value and value.strip())
    
    def get_env_config_value(self, field_name: str) -> Optional[str]:
        """Получить значение из .env конфигурации"""
        return self._env_config_cache.get(field_name)
    
    async def should_ask_for_llm_key(self, user_id: int, new_model_name: str = None) -> bool:
        """
        Определяет, нужно ли запрашивать ключ LLM у пользователя.
        
        Правила:
        1. Если ключ есть в .env и пользователь НЕ меняет модель -> НЕ запрашивать
        2. Если ключа нет в .env -> запрашивать
        3. Если пользователь меняет модель -> запрашивать все (ключ, URL, модель)
        4. Если у пользователя уже есть сохраненный ключ -> НЕ запрашивать
        """
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                return True
            
            # Проверяем наличие ключа в .env
            has_env_key = self._has_env_config('llm_api_key')
            
            # Проверяем, есть ли у пользователя сохраненный ключ
            user_has_key = False
            if hasattr(user, 'llm_api_key_encrypted') and user.llm_api_key_encrypted:
                user_has_key = True
            elif hasattr(user, 'llm_api_key') and user.llm_api_key:
                user_has_key = True
            
            # Проверяем, меняет ли пользователь модель
            if new_model_name and hasattr(self, 'llm_settings_repo'):
                # Используем provider для получения LLM настроек
                llm_settings = await self.llm_settings_repo.get_by_user_id(user_id)
                current_model = llm_settings.model_name if llm_settings else None
                
                # Если модель меняется, нужно запросить все заново
                if current_model and current_model != new_model_name:
                    logger.info(f"Пользователь меняет модель с {current_model} на {new_model_name} - запрашиваем все данные")
                    return True
            
            # Логика принятия решения
            if has_env_key and not new_model_name:
                # Ключ в .env и модель не меняется - не запрашиваем
                logger.info("Ключ есть в .env, модель не меняется - не запрашиваем ключ")
                return False
            elif user_has_key and not new_model_name:
                # У пользователя уже есть ключ и модель не меняется
                logger.info("У пользователя уже есть ключ - не запрашиваем")
                return False
            else:
                # Во всех остальных случаях запрашиваем
                logger.info("Требуется ввод ключа LLM")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка проверки необходимости ключа: {e}")
            return True
    
    async def get_llm_config_for_user(self, user_id: int) -> Dict[str, Any]:
        """
        Получить конфигурацию LLM для пользователя с приоритетом:
        1. Данные из .env (если есть)
        2. Зашифрованные данные пользователя
        3. Открытые данные пользователя
        4. Значения по умолчанию
        """
        config = {
            'api_key': '',
            'base_url': '',
            'model_name': 'gpt-4o-mini',
            'requires_user_input': False,
            'source': 'not_found'
        }
        
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                return config
            
            # 1. Проверяем .env конфигурацию
            env_key = self.get_env_config_value('llm_api_key')
            env_url = self.get_env_config_value('llm_base_url')
            env_model = self.get_env_config_value('llm_model_name')
            
            if env_key:
                config['api_key'] = env_key
                config['base_url'] = env_url or 'https://api.openai.com/v1'
                config['model_name'] = env_model or 'gpt-4o-mini'
                config['source'] = 'env'
                logger.info("Используется конфигурация из .env")
                return config
            
            # 2. Пробуем получить зашифрованные данные
            encrypted_key = await self.decrypt_and_get(user_id, 'llm_api_key')
            encrypted_url = await self.decrypt_and_get(user_id, 'llm_base_url')
            
            if encrypted_key:
                config['api_key'] = encrypted_key
                config['base_url'] = encrypted_url or 'https://api.openai.com/v1'
                config['source'] = 'encrypted_storage'
                
                # Получаем модель из настроек LLM
                if hasattr(self, 'llm_settings_repo'):
                    llm_settings = await self.llm_settings_repo.get_by_user_id(user_id)
                    if llm_settings and llm_settings.model_name:
                        config['model_name'] = llm_settings.model_name
                
                logger.info("Используются зашифрованные данные пользователя")
                return config
            
            # 3. Пробуем получить открытые данные
            if hasattr(user, 'llm_api_key') and user.llm_api_key:
                # Нужно расшифровать!
                config['api_key'] = user.llm_api_key
                config['source'] = 'plain_storage'

                if hasattr(user, 'llm_base_url') and user.llm_base_url:
                    config['base_url'] = user.llm_base_url
                else:
                    config['base_url'] = 'https://api.openai.com/v1'
                
                # Получаем модель из настроек LLM
                if hasattr(self, 'llm_settings_repo'):
                    llm_settings = await self.llm_settings_repo.get_by_user_id(user_id)
                    if llm_settings and llm_settings.model_name:
                        config['model_name'] = llm_settings.model_name
                
                logger.info("Используются открытые данные пользователя")
                return config
            
            # 4. Если данных нет, отмечаем что нужен ввод
            config['requires_user_input'] = True
            logger.info("Данные LLM не найдены, требуется ввод пользователя")
            
        except Exception as e:
            logger.error(f"Ошибка получения конфигурации LLM: {e}")
            config['requires_user_input'] = True
        
        return config
    
    async def save_llm_config(self, user_id: int, api_key: str, base_url: str, model_name: str = None) -> bool:
        """Сохранить конфигурацию LLM для пользователя"""
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                return False
            
            # Сохраняем API ключ (шифруем если не из .env)
            env_key = self.get_env_config_value('llm_api_key')
            if api_key != env_key:  # Сохраняем только если отличается от .env
                success = await self.encrypt_and_save(user_id, 'llm_api_key', api_key)
                if not success:
                    logger.warning("Не удалось сохранить API ключ")
            
            # Сохраняем base URL (шифруем если не из .env)
            env_url = self.get_env_config_value('llm_base_url')
            if base_url != env_url:
                success = await self.encrypt_and_save(user_id, 'llm_base_url', base_url)
                if not success:
                    logger.warning("Не удалось сохранить base URL")
            
            # Сохраняем модель в LLM настройках
            if model_name and hasattr(self, 'llm_settings_repo'):
                llm_settings = await self.llm_settings_repo.get_by_user_id(user_id)
                if llm_settings:
                    await self.llm_settings_repo.update_settings(
                        llm_settings.id, 
                        model_name=model_name
                    )
        
            await self.user_repo.session.commit()
            logger.info(f"Конфигурация LLM сохранена для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации LLM: {e}")
            return False
    
    async def initialize_user_encryption(self, user_id: int) -> bool:
        """Инициализация шифрования для пользователя (если еще нет)"""
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                return False
            
            # Если у пользователя уже есть ключ, не пересоздаем
            if user.encryption_key and hasattr(user, 'hh_encryption_salt') and user.hh_encryption_salt:
                return True
            
            # Генерируем новую пару ключ-соль
            user_key, user_salt = encryption_service.generate_key_pair()
            
            # Сохраняем
            user.encryption_key = user_key.decode()
            if hasattr(user, 'hh_encryption_salt'):
                user.hh_encryption_salt = base64.urlsafe_b64encode(user_salt).decode()
            
            await self.user_repo.session.commit()
            logger.info(f"Инициализировано шифрование для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации шифрования: {e}")
            return False
    
    def _get_user_cipher(self, user) -> Optional[Fernet]:
        """Получение объекта шифрования для пользователя"""
        if not user.encryption_key:
            return None
        
        # Кэшируем объект cipher для производительности
        cache_key = f"{user.id}_{user.encryption_key[:10]}"
        if cache_key in self._user_keys_cache:
            return self._user_keys_cache[cache_key]
        
        try:
            key = user.encryption_key.encode()
            cipher = Fernet(key)
            self._user_keys_cache[cache_key] = cipher
            return cipher
        except Exception as e:
            logger.error(f"Ошибка создания cipher: {e}")
            return None
    
    async def encrypt_and_save(self, user_id: int, field_name: str, value: str) -> bool:
        """Шифрование и сохранение значения"""
        try:
            # Инициализируем шифрование если нужно
            await self.initialize_user_encryption(user_id)
            
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                return False
            
            cipher = self._get_user_cipher(user)
            if not cipher:
                return False
            
            # Шифруем данные
            encrypted = cipher.encrypt(value.encode())
            encrypted_b64 = base64.urlsafe_b64encode(encrypted).decode()
            
            # Сохраняем в соответствующее поле
            encrypted_field = f"{field_name}_encrypted"
            if hasattr(user, encrypted_field):
                setattr(user, encrypted_field, encrypted_b64)
                
                # Обновляем хеш целостности
                await self._update_integrity_hash(user)
                
                await self.user_repo.session.commit()
                logger.info(f"Зашифровано поле {field_name} для пользователя {user_id}")
                return True
            
            logger.error(f"Поле {encrypted_field} не найдено у пользователя")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка шифрования {field_name}: {e}")
            return False
    
    async def decrypt_and_get(self, user_id: int, field_name: str) -> Optional[str]:
        """Получение и расшифровка значения"""
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                return None
            
            # Сначала пробуем получить зашифрованные данные
            encrypted_field = f"{field_name}_encrypted"
            if hasattr(user, encrypted_field):
                encrypted_b64 = getattr(user, encrypted_field)
                if encrypted_b64:
                    # Проверяем целостность данных
                    if not await self._verify_integrity_hash(user):
                        logger.warning(f"Нарушена целостность данных пользователя {user_id}")
                    
                    # Инициализируем шифрование если нужно
                    #await self.initialize_user_encryption(user_id)
                    
                    cipher = self._get_user_cipher(user)
                    if not cipher:
                        return None
                    
                    # Расшифровываем
                    try:
                        encrypted = base64.urlsafe_b64decode(encrypted_b64.encode())
                        decrypted = cipher.decrypt(encrypted)
                        return decrypted.decode()
                    except InvalidToken:
                        #logger.error(f"Неверный токен для расшифровки {field_name}")
                        logger.info(f"⚠️  Данные поля {field_name} зашифрованы старым ключом. Возвращаю None.")
                        return None
            
            # Если нет зашифрованных данных, пробуем получить открытые
            if hasattr(user, field_name):
                value = getattr(user, field_name)
                if value:
                    logger.info(f"Использованы открытые данные для поля {field_name}")
                    return value
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения поля {field_name}: {e}")
            return None
    
    async def get_user_secrets(self, user_id: int) -> Dict[str, Optional[str]]:
        """Получение всех зашифрованных данных пользователя"""
        secrets = {}
        
        fields_to_decrypt = [
            'hh_client_id',
            'hh_client_secret', 
            'hh_access_token',
            'hh_refresh_token',
            'llm_api_key',
            'llm_base_url',
            'contact_email',
            'contact_phone'
        ]
        
        for field in fields_to_decrypt:
            # Сначала пробуем получить зашифрованные данные
            decrypted = await self.decrypt_and_get(user_id, field)
            if decrypted:
                secrets[field] = decrypted
            else:
                # Если нет зашифрованных данных, пробуем получить открытые
                try:
                    user = await self.user_repo.get_user_by_id(user_id)
                    if user and hasattr(user, field):
                        value = getattr(user, field)
                        if value:
                            secrets[field] = value
                except Exception as e:
                    logger.error(f"Ошибка получения поля {field}: {e}")
        
        return secrets
    
    async def _update_integrity_hash(self, user) -> None:
        """Обновление хеша целостности данных"""
        try:
            # Собираем все зашифрованные поля для хеширования
            data_to_hash = []
            self.encryption_fields = [
                'encryption_key',
                'encryption_salt',
                'hh_client_id_encrypted',
                'hh_client_secret_encrypted',
                'hh_access_token_encrypted',
                'hh_refresh_token_encrypted',
                'llm_api_key_encrypted',
                'llm_base_url_encrypted',
                'contact_email_encrypted',
                'contact_phone_encrypted',
                'data_integrity_hash'
            ]
            
            for field in self.encrypted_fields:
                value = getattr(user, field, '')
                if value:
                    data_to_hash.append(value)
            
            # Создаем хеш
            if data_to_hash:
                data_string = '|'.join(data_to_hash)
                user.data_integrity_hash = encryption_service.secure_hash(data_string)
        
        except Exception as e:
            logger.error(f"Ошибка обновления хеша целостности: {e}")
    
    async def _verify_integrity_hash(self, user) -> bool:
        """Проверка целостности данных"""
        try:
            if not hasattr(user, 'data_integrity_hash') or not user.data_integrity_hash:
                return True
            
            # Собираем данные как при создании хеша
            data_to_hash = []
            self.encryption_fields = [
                'encryption_key',
                'encryption_salt',
                'hh_client_id_encrypted',
                'hh_client_secret_encrypted',
                'hh_access_token_encrypted',
                'hh_refresh_token_encrypted',
                'llm_api_key_encrypted',
                'llm_base_url_encrypted',
                'contact_email_encrypted',
                'contact_phone_encrypted',
                'data_integrity_hash'
            ]
            
            for field in self.encrypted_fields:
                if hasattr(user, field):
                    value = getattr(user, field, '')
                    if value:
                        data_to_hash.append(value)
            
            if not data_to_hash:
                return True
            
            data_string = '|'.join(data_to_hash)
            return encryption_service.verify_hash(data_string, user.data_integrity_hash)
        
        except Exception as e:
            logger.error(f"Ошибка проверки целостности: {e}")
            return False
    
    async def rotate_encryption_key(self, user_id: int) -> bool:
        """Смена ключа шифрования (ротация)"""
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                return False
            
            # Расшифровываем все данные старым ключом
            old_secrets = await self.get_user_secrets(user_id)
            
            # Генерируем новый ключ
            new_key, new_salt = encryption_service.generate_key_pair()
            
            # Сохраняем новый ключ
            user.encryption_key = new_key.decode()
            # Сохраняем новую соль
            if hasattr(user, 'hh_encryption_salt'):
                user.hh_encryption_salt = base64.urlsafe_b64encode(new_salt).decode()
            
            # Очищаем кэш
            cache_key = f"{user.id}_{user.encryption_key[:10]}"
            self._user_keys_cache.pop(cache_key, None)
            
            # Перешифровываем все данные новым ключом
            for field_name, value in old_secrets.items():
                if value:
                    await self.encrypt_and_save(user_id, field_name, value)
            
            logger.info(f"Произведена ротация ключа для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка ротации ключа: {e}")
            return False