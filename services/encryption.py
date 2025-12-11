import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class EncryptionService:
    """Служба шифрования для хранения чувствительных данных"""
    
    def __init__(self, master_key_salt: bytes = None):
        # Соль для генерации мастер-ключа из пароля (в продакшене брать из env)
        self.master_key_salt = master_key_salt or b'hh_bot_salt_2025'
        self._cipher_cache = {}
    
    def generate_master_key(self, password: str) -> bytes:
        """Генерация мастер-ключа из пароля"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.master_key_salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """Генерация пары ключ-соль для пользователя"""
        # Генерируем случайную соль для пользователя
        user_salt = os.urandom(16)
        # Генерируем ключ для пользователя
        user_key = base64.urlsafe_b64encode(os.urandom(32))
        return user_key, user_salt
    
    def encrypt_data(self, data: str, encryption_key: bytes) -> str:
        """Шифрование данных с использованием ключа"""
        try:
            cipher = Fernet(encryption_key)
            encrypted = cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Ошибка шифрования: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str, encryption_key: bytes) -> str:
        """Расшифровка данных с использованием ключа"""
        try:
            cipher = Fernet(encryption_key)
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Ошибка расшифровки: {e}")
            raise
    
    def secure_hash(self, data: str) -> str:
        """Создание безопасного хеша для проверки целостности"""
        import hashlib
        salt = os.urandom(16)
        data_to_hash = salt + data.encode()
        hash_obj = hashlib.sha256(data_to_hash)
        return f"{salt.hex()}:{hash_obj.hexdigest()}"
    
    def verify_hash(self, data: str, hash_string: str) -> bool:
        """Проверка хеша"""
        try:
            salt_hex, stored_hash = hash_string.split(":")
            salt = bytes.fromhex(salt_hex)
            data_to_hash = salt + data.encode()
            hash_obj = hashlib.sha256(data_to_hash)
            return hash_obj.hexdigest() == stored_hash
        except:
            return False

# Синглтон для использования в приложении
encryption_service = EncryptionService()