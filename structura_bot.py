import os
import json
from pathlib import Path

class ProjectLoader:
    def __init__(self):
        self.supported_formats = ['.json', '.txt']
    
    def show_available_files(self):
        """Показывает доступные файлы со структурами"""
        print("\n📁 Доступные файлы со структурами:")
        found_files = []
        
        for file_format in self.supported_formats:
            for file_path in Path('.').glob(f'*{file_format}'):
                if file_path.is_file() and file_path.stat().st_size > 0:
                    found_files.append(file_path)
                    print(f"  📄 {file_path.name}")
        
        if not found_files:
            print("  ❌ Файлы со структурами не найдены")
            self._create_sample_json()
            return self.show_available_files()
            
        return found_files
    
    def _create_sample_json(self):
        """Создает пример JSON файла"""
        print("\n🛠️ Создаю пример структуры...")
        
        structure = {
            "project_name": "telegram_bot",
            "structure": {
                "handlers": {
                    "user_handlers.py": "def handle_start():\n    print('Start command')\n",
                    "admin_handlers.py": "def handle_admin():\n    print('Admin command')\n"
                },
                "utils": {
                    "keyboards.py": "from telegram import ReplyKeyboardMarkup\n\ndef main_menu():\n    return ReplyKeyboardMarkup([['Option 1'], ['Option 2']])\n",
                    "states.py": "class UserState:\n    MAIN_MENU = 1\n    SETTINGS = 2\n",
                    "validators.py": "def validate_email(email):\n    return '@' in email\n",
                    "scheduler.py": "def schedule_task():\n    print('Task scheduled')\n"
                },
                "config": {
                    "settings.py": "BOT_TOKEN = 'your_token_here'\nDEBUG = True\n"
                },
                "main.py": "print('Hello Bot!')\n",
                "requirements.txt": "python-telegram-bot==20.0\n"
            }
        }
        
        with open("bot_structure.json", "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print("  ✅ Создан bot_structure.json")
    
    def load_structure_from_file(self, file_path):
        """Загружает структуру только из JSON"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ Файл {file_path} не найден!")
            return None
        
        if file_path.stat().st_size == 0:
            print(f"❌ Файл {file_path} пустой!")
            return None
        
        if file_path.suffix.lower() != '.json':
            print(f"❌ Поддерживается только JSON формат!")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ JSON файл загружен успешно")
            return data
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка в JSON файле: {e}")
            return None
    
    def find_main_folder(self):
        """Ищет существующую главную папку проекта"""
        print("\n🔍 Поиск существующих папок проектов...")
        folders = [f for f in Path('.').iterdir() if f.is_dir() and not f.name.startswith('.')]
        
        if folders:
            print("📁 Найдены папки:")
            for i, folder in enumerate(folders, 1):
                print(f"  {i}. {folder.name}")
            
            choice = input("\nВыберите папку для создания структуры (номер) или Enter для новой: ").strip()
            if choice and choice.isdigit():
                selected_index = int(choice) - 1
                if 0 <= selected_index < len(folders):
                    return folders[selected_index]
        
        return None
    
    def create_project_structure(self, project_data, main_folder=None):
        """Создает структуру проекта"""
        if not project_data:
            print("❌ Нет данных для создания структуры!")
            return None
            
        if main_folder:
            project_name = main_folder.name
            base_path = main_folder
            print(f"🎯 Используем существующую папку: {project_name}")
        else:
            project_name = project_data.get("project_name", "new_project")
            base_path = Path(project_name)
            base_path.mkdir(exist_ok=True)
            print(f"🎯 Создана новая папка: {project_name}")
        
        structure = project_data.get("structure", {})
        
        if not structure:
            print("❌ Структура пустая!")
            return base_path
        
        print(f"\n📋 СОЗДАЕМ СТРУКТУРУ:")
        self._build_structure_simple(base_path, structure)
        
        return base_path
    
    def _build_structure_simple(self, base_path, structure):
        """ПРОСТОЙ и надежный метод создания структуры"""
        for name, content in structure.items():
            item_path = base_path / name
            
            if isinstance(content, dict):
                # Это ПАПКА - создаем папку и её содержимое
                item_path.mkdir(exist_ok=True)
                print(f"📁 Создана папка: {item_path}")
                self._build_structure_simple(item_path, content)
            else:
                # Это ФАЙЛ - создаем файл с содержимым
                item_path.parent.mkdir(parents=True, exist_ok=True)
                item_path.write_text(content, encoding='utf-8')
                print(f"📄 Создан файл: {item_path}")

def main():
    """Основная функция программы"""
    print("🚀 Программа загрузки структуры проекта")
    print("=" * 50)
    
    loader = ProjectLoader()
    
    # Шаг 1: Показываем доступные файлы
    available_files = loader.show_available_files()
    
    if not available_files:
        print("❌ Нет доступных файлов со структурами")
        return
    
    # Шаг 2: Выбор файла со структурой
    print("\n📂 Выберите файл со структурой:")
    for i, file_path in enumerate(available_files, 1):
        print(f"  {i}. {file_path.name}")
    
    try:
        choice = input("\nВведите номер файла: ").strip()
        if not choice:
            print("❌ Не выбран файл")
            return
            
        selected_index = int(choice) - 1
        if 0 <= selected_index < len(available_files):
            selected_file = available_files[selected_index]
            print(f"🎯 Выбран файл: {selected_file}")
        else:
            print("❌ Неверный номер файла")
            return
    except ValueError:
        print("❌ Введите корректный номер")
        return
    
    # Шаг 3: Загрузка структуры (ТОЛЬКО JSON)
    project_data = loader.load_structure_from_file(selected_file)
    
    if not project_data:
        print("❌ Не удалось загрузить структуру")
        return
    
    # Шаг 4: Поиск существующей папки
    main_folder = loader.find_main_folder()
    
    # Шаг 5: Создание структуры
    project_path = loader.create_project_structure(project_data, main_folder)
    
    if project_path:
        print(f"\n✅ СТРУКТУРА СОЗДАНА В: {project_path}")
        
        # Показываем что создалось
        print(f"\n📊 СОЗДАННЫЕ ФАЙЛЫ:")
        for root, dirs, files in os.walk(project_path):
            for file in files:
                file_path = Path(root) / file
                print(f"📄 {file_path}")

if __name__ == "__main__":
    main()