# update_logging.py
"""
Скрипт для автоматического обновления импортов логирования во всех файлах
"""

import os
import re
from pathlib import Path

# Файлы для обновления (относительные пути)
FILES_TO_UPDATE = [
    "services/hh_service.py",
    "services/secure_storage.py", 
    "services/llm_service.py",
    "services/hh_auth_manager.py",
    "services/hh_response.py",
    "handlers/base.py",
    "handlers/profile.py",
    "handlers/responses.py",
    "handlers/search2.py",
    "handlers/vacancies.py",
    "handlers/llm.py",
    "handlers/hh_api.py",
    "middleware/dependency.py",
    "middleware/error_handler.py",
    "database/repository.py",
]

def update_file(filepath):
    """Обновить импорты логирования в одном файле"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем импорт logging на наш логгер
        old_content = content
        
        # Паттерн 1: import logging в начале файла
        pattern1 = r'^import logging\s*\n'
        replacement1 = ''
        
        # Паттерн 2: logger = logging.getLogger(__name__)
        pattern2 = r'logger\s*=\s*logging\.getLogger\(__name__\)'
        replacement2 = 'from utils.logger import get_logger\nlogger = get_logger(__name__)'
        
        # Применяем замены
        content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
        content = re.sub(pattern2, replacement2, content)
        
        # Если изменения произошли, сохраняем файл
        if content != old_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Обновлен: {filepath}")
            return True
        else:
            print(f"ℹ️  Без изменений: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в {filepath}: {e}")
        return False

def check_existing_logger_import(filepath):
    """Проверить, есть ли уже импорт нашего логгера"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие нашего импорта
        if 'from utils.logger import' in content or 'import utils.logger' in content:
            return True
        return False
    except:
        return False

def main():
    print("🔄 Начинаю обновление импортов логирования...")
    print("=" * 60)
    
    updated_count = 0
    skipped_count = 0
    
    for file_rel_path in FILES_TO_UPDATE:
        filepath = Path(file_rel_path)
        
        if not filepath.exists():
            print(f"⚠️  Файл не найден: {file_rel_path}")
            continue
            
        # Проверяем, не обновлен ли уже файл
        if check_existing_logger_import(filepath):
            print(f"⏭️  Пропущен (уже обновлен): {file_rel_path}")
            skipped_count += 1
            continue
            
        if update_file(filepath):
            updated_count += 1
    
    print("=" * 60)
    print(f"📊 Результат:")
    print(f"   Обновлено файлов: {updated_count}")
    print(f"   Пропущено файлов: {skipped_count}")
    print(f"   Всего обработано: {updated_count + skipped_count}")
    
    if updated_count > 0:
        print("\n✅ Обновление завершено!")
        print("📝 Не забудьте проверить файлы вручную.")
    else:
        print("\nℹ️  Все файлы уже обновлены или не требуют изменений.")

if __name__ == "__main__":
    main()