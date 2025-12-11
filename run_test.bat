@echo off
echo ==================================================
echo 🧪 ТЕСТ LLM ДЛЯ HH WORK DAY BOT
echo ==================================================
echo.

REM Проверяем, что мы в корневой директории проекта
if not exist "core" (
    echo ❌ ОШИБКА: Запускайте тест из корневой директории проекта!
    echo Текущая папка должна содержать папки: core, services, database
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo ⚠️  ВНИМАНИЕ: .env файл не найден!
    echo.
    echo Создаю шаблон .env файла...
    echo.
    
    echo # LLM настройки для теста > .env
    echo. >> .env
    echo # Вариант 1: OpenAI (нужен API ключ) >> .env
    echo # LLM_API_KEY=sk-your-openai-api-key-here >> .env
    echo # LLM_BASE_URL=https://api.openai.com/v1 >> .env
    echo # LLM_MODEL_NAME=gpt-3.5-turbo >> .env
    echo. >> .env
    echo # Вариант 2: Ollama (локальный, бесплатный) >> .env
    echo LLM_API_KEY=ollama >> .env
    echo LLM_BASE_URL=http://localhost:11434/v1 >> .env
    echo LLM_MODEL_NAME=llama2 >> .env
    echo. >> .env
    echo # Общие настройки >> .env
    echo LLM_TIMEOUT=60 >> .env
    echo LLM_MAX_TOKENS=2000 >> .env
    echo LLM_TEMPERATURE=0.7 >> .env
    
    echo.
    echo ✅ Шаблон .env создан!
    echo ОТКРОЙТЕ ФАЙЛ .env И НАСТРОЙТЕ LLM_API_KEY
    echo.
    pause
    exit /b 1
)

echo ✅ Запускаю тест LLM...
echo ==================================================
python test_llm_working.py

echo.
pause