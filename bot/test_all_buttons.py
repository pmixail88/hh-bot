# test_all_buttons.py - исправленный скрипт
import asyncio
import os
import re

def test_all_buttons():
    """Тестирование всех callback_data"""
    print("🔍 Проверяем все callback_data в проекте...")
    
    # Все callback_data из keyboards.py и других мест
    callbacks = {
        "menu_main": {"type": "точное", "desc": "Главное меню"},
        "menu_vacancies": {"type": "точное", "desc": "Поиск вакансий"},
        "menu_search_settings": {"type": "точное", "desc": "Настройки поиска"},
        "menu_profile": {"type": "точное", "desc": "Мой профиль"},
        "menu_my_vacancies": {"type": "точное", "desc": "Мои вакансии"},
        "menu_llm_settings": {"type": "точное", "desc": "AI Помощник"},
        "menu_stats": {"type": "точное", "desc": "Статистика"},
        "menu_help": {"type": "точное", "desc": "Помощь"},
        
        "settings_keywords": {"type": "префикс", "desc": "Ключевые слова"},
        "settings_region": {"type": "префикс", "desc": "Регион"},
        "settings_salary_from": {"type": "префикс", "desc": "Зарплата от"},
        "settings_salary_to": {"type": "префикс", "desc": "Зарплата до"},
        "settings_experience": {"type": "префикс", "desc": "Опыт"},
        "settings_schedule": {"type": "префикс", "desc": "График"},
        "settings_period": {"type": "префикс", "desc": "Период"},
        "settings_reset_all": {"type": "точное", "desc": "Сбросить все"},
        "settings_save": {"type": "точное", "desc": "Сохранить"},
        "menu_search_vacancies": {"type": "точное", "desc": "Начать поиск"},
        
        "page_": {"type": "префикс", "desc": "Пагинация"},
        "show_current_page": {"type": "точное", "desc": "Инфо о странице"},
        
        "vacancy_favorite_": {"type": "префикс", "desc": "В избранное"},
        "vacancy_apply_": {"type": "префикс", "desc": "Откликнуться"},
        "vacancy_view_": {"type": "префикс", "desc": "Просмотрено"},
        "vacancy_notes_": {"type": "префикс", "desc": "Заметки"},
        "vacancy_back_to_list": {"type": "точное", "desc": "Назад к списку"},
        
        "profile_edit_": {"type": "префикс", "desc": "Редактирование профиля"},
        "llm_edit_": {"type": "префикс", "desc": "Редактирование AI"},
        
        # Проблемные кнопки (проверим отдельно)
        "menu_back": {"type": "точное", "desc": "Назад (проблемная)"},
    }
    
    print(f"✅ Всего {len(callbacks)} callback_data для проверки")
    
    # Словарь для найденных обработчиков
    found_handlers = {cb: {"files": [], "count": 0} for cb in callbacks}
    
    # Проходим по всем файлам проекта
    python_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py") and "venv" not in root and "__pycache__" not in root:
                python_files.append(os.path.join(root, file))
    
    print(f"📁 Найдено {len(python_files)} Python файлов")
    
    for filepath in python_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Ищем обработчики callback_query
            lines = content.split("\n")
            for i, line in enumerate(lines):
                # Ищем декоратор @router.callback_query
                if "@router.callback_query" in line:
                    # Ищем следующую строку с async def
                    handler_start = i + 1
                    while handler_start < len(lines) and not lines[handler_start].strip().startswith("async def"):
                        handler_start += 1
                    
                    if handler_start >= len(lines):
                        continue
                    
                    # Смотрим на следующие строки после async def (макс 10 строк)
                    handler_lines = lines[handler_start:handler_start+10]
                    handler_text = "\n".join(handler_lines)
                    
                    # Теперь ищем F.data в этом обработчике
                    for callback_name, callback_info in callbacks.items():
                        pattern_type = callback_info["type"]
                        
                        if pattern_type == "точное":
                            # Проверяем точное совпадение
                            patterns = [
                                f"F.data == \"{callback_name}\"",
                                f"F.data == '{callback_name}'",
                                f"callback.data == \"{callback_name}\"",
                                f"callback.data == '{callback_name}'",
                                f"data == \"{callback_name}\"",
                                f"data == '{callback_name}'",
                            ]
                            
                            for pattern in patterns:
                                if pattern in handler_text:
                                    found_handlers[callback_name]["files"].append(filepath)
                                    found_handlers[callback_name]["count"] += 1
                                    break
                        
                        elif pattern_type == "префикс":
                            # Проверяем startswith
                            patterns = [
                                f"F.data.startswith(\"{callback_name}\")",
                                f"F.data.startswith('{callback_name}')",
                                f".startswith(\"{callback_name}\")",
                                f".startswith('{callback_name}')",
                            ]
                            
                            for pattern in patterns:
                                if pattern in handler_text:
                                    found_handlers[callback_name]["files"].append(filepath)
                                    found_handlers[callback_name]["count"] += 1
                                    break
        
        except Exception as e:
            print(f"❌ Ошибка при чтении файла {filepath}: {e}")
            continue
    
    # Выводим результаты
    print("\n" + "="*80)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ ОБРАБОТЧИКОВ:")
    print("="*80)
    
    # Группируем по статусу
    handled = []
    not_handled = []
    
    for callback_name, callback_info in callbacks.items():
        if found_handlers[callback_name]["count"] > 0:
            handled.append(callback_name)
        else:
            not_handled.append(callback_name)
    
    print(f"\n✅ ОБРАБАТЫВАЮТСЯ ({len(handled)}):")
    for cb in sorted(handled):
        files = found_handlers[cb]["files"]
        print(f"  • {cb} - {callbacks[cb]['desc']}")
        for file in files[:2]:  # Показываем первые 2 файла
            print(f"    📄 {os.path.basename(file)}")
        if len(files) > 2:
            print(f"    ... и еще {len(files)-2} файлов")
    
    print(f"\n❌ НЕ ОБРАБАТЫВАЮТСЯ ({len(not_handled)}):")
    for cb in sorted(not_handled):
        print(f"  • {cb} - {callbacks[cb]['desc']}")
    
    # Проблемные callback_data
    print(f"\n⚠️ ПРОБЛЕМНЫЕ КНОПКИ:")
    problematic = ["menu_back"]  # Кнопки, которые есть в клавиатурах, но нет обработчиков
    for cb in problematic:
        if cb in not_handled:
            print(f"  • {cb} - есть в клавиатуре, но нет обработчика!")
    
    # Проверяем конкретные файлы
    print(f"\n🔍 ПРОВЕРКА КЛЮЧЕВЫХ ФАЙЛОВ:")
    
    key_files = [
        "bot/handlers/base.py",
        "bot/handlers/search2.py", 
        "bot/handlers/vacancies.py",
        "bot/handlers/profile.py",
        "bot/handlers/llm.py",
        "bot/utils/keyboards.py"
    ]
    
    for key_file in key_files:
        if os.path.exists(key_file):
            print(f"\n📁 {key_file}:")
            with open(key_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Ищем все callback_data в файле
            import re
            callback_pattern = r'callback_data=["\']([^"\']+)["\']'
            matches = re.findall(callback_pattern, content)
            
            if matches:
                unique_matches = set(matches)
                print(f"  Найдено callback_data: {len(unique_matches)}")
                for cb in sorted(unique_matches)[:10]:  # Показываем первые 10
                    status = "✅" if cb in handled else "❌"
                    print(f"    {status} {cb}")
                if len(unique_matches) > 10:
                    print(f"    ... и еще {len(unique_matches)-10}")
            else:
                print("  ❌ Не найдено callback_data")

def check_button_consistency():
    """Проверка согласованности кнопок"""
    print("\n" + "="*80)
    print("🔄 ПРОВЕРКА СОГЛАСОВАННОСТИ КНОПОК:")
    print("="*80)
    
    # Читаем keyboards.py
    keyboards_file = "bot/utils/keyboards.py"
    if os.path.exists(keyboards_file):
        with open(keyboards_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Ищем все callback_data
        import re
        callback_pattern = r'callback_data=["\']([^"\']+)["\']'
        all_callbacks = re.findall(callback_pattern, content)
        unique_callbacks = set(all_callbacks)
        
        print(f"\n📋 Все callback_data из keyboards.py ({len(unique_callbacks)}):")
        for cb in sorted(unique_callbacks):
            print(f"  • {cb}")
        
        # Проверяем обработчики для каждого
        handlers_file = "bot/handlers/__init__.py"
        if os.path.exists(handlers_file):
            with open(handlers_file, "r", encoding="utf-8") as f:
                handlers_content = f.read()
            
            print(f"\n🔗 Проверка роутеров в handlers/__init__.py:")
            router_pattern = r'router\.include_router\((\w+)_router\)'
            routers = re.findall(router_pattern, handlers_content)
            print(f"  Загруженные роутеры: {', '.join(routers)}")

def main():
    """Основная функция"""
    print("🚀 ЗАПУСК ПРОВЕРКИ КНОПОК БОТА")
    print("="*80)
    
    # Проверяем существование папки bot
    if not os.path.exists("bot"):
        print("❌ Папка 'bot' не найдена!")
        print("💡 Запустите скрипт из корневой директории проекта")
        return
    
    # Запускаем проверки
    test_all_buttons()
    check_button_consistency()
    
    print("\n" + "="*80)
    print("🎯 РЕКОМЕНДАЦИИ:")
    print("="*80)
    print("1. Исправьте callback_data='menu_back' на callback_data='menu_main'")
    print("2. Проверьте обработчики для всех префиксных callback_data (с _)")
    print("3. Убедитесь, что все callback_data из keyboards.py имеют обработчики")
    print("4. Запустите бота и протестируйте все кнопки вручную")

if __name__ == "__main__":
    main()