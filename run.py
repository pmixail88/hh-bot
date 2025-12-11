#!/usr/bin/env python3
"""
Главный файл для запуска бота
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем путь к папке bot в Python path
bot_path = Path(__file__).parent / 'bot'
sys.path.insert(0, str(bot_path))

async def main():
    """Основная функция запуска"""
    try:
        # Импортируем и запускаем бота
        from main import main as bot_main
        print("🚀 Запуск HH Bot...")
        await bot_main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("💡 Создайте файл .env на основе .env.example")
        sys.exit(1)
    
    asyncio.run(main())