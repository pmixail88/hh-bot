# services/local_oauth_server.py
import asyncio
import webbrowser
from aiohttp import web
from typing import Tuple, Optional

class LocalOAuthServer:
    """Простой HTTP-сервер для перехвата OAuth кода авторизации."""

    def __init__(self, host: str = '127.0.0.1', port: int = 8080, callback_path: str = '/callback'):
        self.host = host
        self.port = port
        self.callback_path = callback_path
        self._authorization_code = None
        self._server_ready = asyncio.Event()

    async def _handle_callback(self, request):
        """Обработчик запроса на callback-адресе."""
        # Извлекаем код авторизации из параметров запроса
        auth_code = request.query.get('code')
        state = request.query.get('state', 'default')
        error = request.query.get('error')

        if error:
            html_response = f"""
            <html><body>
            <h2>Ошибка авторизации</h2>
            <p>HH.ru вернул ошибку: {error}</p>
            <p>Описание: {request.query.get('error_description', 'Нет описания')}</p>
            <p>Закройте это окно и попробуйте снова в боте.</p>
            </body></html>
            """
            return web.Response(text=html_response, content_type='text/html')

        if auth_code:
            self._authorization_code = (auth_code, state)
            self._server_ready.set()
            html_response = """
            <html><body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h2 style="color: green;">✅ Авторизация успешна!</h2>
            <p>Вы получили код авторизации. Это окно можно закрыть.</p>
            <p>Вернитесь в Telegram-бот для продолжения.</p>
            </body></html>
            """
        else:
            html_response = """
            <html><body>
            <h2 style="color: orange;">⚠️ Код авторизации не найден</h2>
            <p>Вернитесь в бот и начните процесс заново.</p>
            </body></html>
            """

        return web.Response(text=html_response, content_type='text/html')

    async def wait_for_code(self, auth_url: str) -> Optional[Tuple[str, str]]:
        """
        Запускает сервер, открывает браузер с auth_url и ждет код.
        Возвращает кортеж (code, state) или None в случае таймаута.
        """
        runner = None
        try:
            # Создаем и настраиваем приложение aiohttp
            app = web.Application()
            app.router.add_get(self.callback_path, self._handle_callback)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()

            print(f"🌐 Сервер OAuth запущен на http://{self.host}:{self.port}")
            print(f"🔄 Открываю браузер для авторизации...")

            # Открываем браузер для пользователя
            webbrowser.open(auth_url)

            # Ждем получения кода с таймаутом (например, 180 секунд)
            await asyncio.wait_for(self._server_ready.wait(), timeout=300.0)

            print(f"✅ Код авторизации получен.")
            return self._authorization_code

        except asyncio.TimeoutError:
            print("⏱️  Время ожидания авторизации истекло.")
            return None
        except Exception as e:
            print(f"❌ Ошибка сервера: {e}")
            return None
        finally:
            # Останавливаем сервер в любом случае
            if runner:
                await runner.cleanup()
            print("🌐 Сервер OAuth остановлен.")
            self._server_ready.clear()
            self._authorization_code = None