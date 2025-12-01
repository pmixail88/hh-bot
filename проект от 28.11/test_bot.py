import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

# Включаем ВСЕ логи
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    logging.info(f"🎯 /start от пользователя {message.from_user.id} ({message.from_user.username})")
    await message.answer("🎉 Бот работает! Команда /start получена!")

@router.message(Command("test"))
async def cmd_test(message: Message):
    logging.info(f"🧪 /test от пользователя {message.from_user.id}")
    await message.answer("✅ Тестовая команда работает!")

@router.message(Command("ping"))
async def cmd_ping(message: Message):
    logging.info(f"🏓 /ping от пользователя {message.from_user.id}")
    await message.answer("🏓 PONG! Бот жив!")

@router.message()
async def echo(message: Message):
    logging.info(f"📨 Сообщение от {message.from_user.id}: {message.text}")
    await message.answer(f"🔊 Эхо: {message.text}")

async def main():
    # Твой токен
    bot = Bot(token="8439133667:AAH6KFseFP0kvo_8s1XYeBoCsgwrdURfULs")
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    logging.info("🤖 Бот запускается...")
    
    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logging.info(f"✅ Бот: {bot_info.full_name} (@{bot_info.username})")
        
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"💥 Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())