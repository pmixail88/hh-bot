# test_all_loggers.py
#!/usr/bin/env python3
"""
Тестирование всех обновленных логгеров
"""

import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger

async def test_all_modules():
    """Имитируем вызовы из разных модулей"""
    
    print("🧪 Тестирование логгеров всех модулей")
    print("=" * 60)
    
    # Тестируем основной логгер
    logger.info("🔍 Начинаю тестирование...")
    
    # Имитация разных модулей
    modules = [
        ("HH Service", "services.hh_service"),
        ("Secure Storage", "services.secure_storage"),
        ("LLM Service", "services.llm_service"),
        ("Handlers Base", "handlers.base"),
        ("Profile Handler", "handlers.profile"),
        ("Responses Handler", "handlers.responses"),
        ("Middleware", "middleware.dependency"),
        ("Database", "database.repository"),
    ]
    
    for module_name, module_path in modules:
        try:
            # Создаем логгер для каждого модуля
            from utils.logger import get_logger
            module_logger = get_logger(module_path)
            
            # Тестовые сообщения
            module_logger.debug(f"{module_name}: Debug сообщение")
            module_logger.info(f"{module_name}: Info сообщение")
            module_logger.warning(f"{module_name}: Warning сообщение")
            
            print(f"✅ {module_name} - логгер работает")
            
        except Exception as e:
            print(f"❌ {module_name} - ошибка: {e}")
    
    print("=" * 60)
    logger.info("✅ Тестирование завершено")
    
    # Проверяем запись в файлы
    print("\n📁 Проверьте файлы в папке logs/:")
    print("   - Все логи: logs/<дата>.log")
    print("   - Ошибки: logs/<дата>_errors.log")

def check_imports():
    """Проверка импортов в ключевых файлах"""
    print("\n🔍 Проверка импортов...")
    
    files_to_check = [
        "main.py",
        "handlers/base.py",
        "services/hh_service.py",
        "middleware/dependency.py",
    ]
    
    for filename in files_to_check:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'from utils.logger import' in content or 'import utils.logger' in content:
                print(f"✅ {filename}: импорт логгера найден")
            else:
                print(f"⚠️  {filename}: импорт логгера НЕ найден")
                
        except Exception as e:
            print(f"❌ {filename}: ошибка чтения - {e}")

async def main():
    print("🚀 ТЕСТИРОВАНИЕ СИСТЕМЫ ЛОГИРОВАНИЯ")
    print("=" * 60)
    
    # Проверяем импорты
    check_imports()
    
    # Тестируем логгеры
    await test_all_modules()
    
    print("\n" + "=" * 60)
    print("🎉 Все тесты завершены!")
    print("\nСледующие шаги:")
    print("1. Запустите бота: python main.py")
    print("2. Проверьте логи в папке logs/")
    print("3. Отправьте боту команду /start для тестирования")

if __name__ == "__main__":
    asyncio.run(main())