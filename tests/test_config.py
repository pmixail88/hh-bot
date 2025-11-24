import unittest
from unittest.mock import patch
from bot.config import Settings, get_settings


class TestConfig(unittest.TestCase):
    """
    Тесты для конфигурации бота
    """
    
    def test_settings_creation(self):
        """
        Тест создания настроек
        """
        with patch.dict('os.environ', {
            'BOT_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test'
        }):
            settings = get_settings()
            
            self.assertIsInstance(settings, Settings)
            self.assertEqual(settings.bot_token, 'test_token')
            self.assertEqual(settings.database_url, 'postgresql://test:test@localhost:5432/test')
    
    def test_settings_with_defaults(self):
        """
        Тест значений по умолчанию
        """
        with patch.dict('os.environ', {
            'BOT_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test'
        }):
            settings = get_settings()
            
            self.assertEqual(settings.llm_base_url, "https://api.openai.com/v1")
            self.assertEqual(settings.llm_model_name, "gpt-4o")
            self.assertEqual(settings.hh_client_id, "")
            self.assertEqual(settings.hh_client_secret, "")