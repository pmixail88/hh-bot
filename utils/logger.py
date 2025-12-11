# utils/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os

class ColoredFormatter(logging.Formatter):
    """Форматирование логов с цветами для терминала"""
    
    # Цвета ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Сохраняем оригинальный уровень
        original_levelname = record.levelname
        
        # Добавляем цвет для терминала
        if sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        
        # Форматируем сообщение
        result = super().format(record)
        
        # Восстанавливаем оригинальный уровень
        record.levelname = original_levelname
        
        return result

def setup_colored_logger(name='hh_bot', log_dir='logs'):
    """
    Настраивает логгер с цветным выводом и записью в файл
    
    Args:
        name: Имя логгера
        log_dir: Директория для логов
        
    Returns:
        Настроенный логгер
    """
    # Создаем директорию для логов если ее нет
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Создаем логгер
    logger = logging.getLogger(name)
    
    # Устанавливаем уровень логирования
    logger.setLevel(logging.DEBUG)
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Формат для логов
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_format = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 1. Обработчик для записи в файл (все уровни)
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'{today}.log')
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_format)
    file_handler.addFilter(lambda record: record.levelno >= logging.DEBUG)
    
    # 2. Обработчик для ошибок в отдельный файл
    error_file = os.path.join(log_dir, f'{today}_errors.log')
    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    
    # 3. Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_format)
    
    # Добавляем все обработчики
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

# Глобальный логгер для использования во всем проекте
logger = setup_colored_logger()

def get_logger(name):
    """Получить именованный логгер"""
    return logging.getLogger(f'hh_bot.{name}')

# Экспортируем основной логгер и функцию настройки
__all__ = ['logger', 'setup_colored_logger', 'get_logger']