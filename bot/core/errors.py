class BotError(Exception):
    """Базовое исключение для ошибок бота"""
    pass

class DatabaseError(BotError):
    """Ошибки базы данных"""
    pass

class ServiceError(BotError):
    """Ошибки сервисов"""
    pass

class ValidationError(BotError):
    """Ошибки валидации данных"""
    pass

class HHAPIError(ServiceError):
    """Ошибки API HH.ru"""
    pass

class LLMAPIError(ServiceError):
    """Ошибки LLM API"""
    pass