import unittest
from unittest.mock import Mock, patch
from bot.services.llm_service import LLMService


class TestLLMService(unittest.TestCase):
    """
    Тесты для LLM-сервиса
    """
    
    def setUp(self):
        self.llm_service = LLMService()
    
    def test_init_service(self):
        """
        Тест инициализации сервиса
        """
        self.assertIsNotNone(self.llm_service.settings)
    
    def test_create_resume_prompt(self):
        """
        Тест создания промпта для резюме
        """
        user_profile = {
            'full_name': 'Иван Иванов',
            'skills': 'Python, SQL, Docker',
            'base_resume': 'Опытный разработчик'
        }
        
        vacancy_info = {
            'title': 'Python разработчик',
            'company': 'Компания X',
            'city': 'Москва',
            'salary_from': 150000,
            'salary_to': 200000,
            'salary_currency': 'RUR',
            'description': 'Требуется Python разработчик'
        }
        
        prompt = self.llm_service._create_resume_prompt(user_profile, vacancy_info)
        
        self.assertIn('Python разработчик', prompt)
        self.assertIn('Компания X', prompt)
        self.assertIn('Москва', prompt)
        self.assertIn('15000 - 200000 RUR', prompt)
        self.assertIn('Требуется Python разработчик', prompt)
        self.assertIn('Иван Иванов', prompt)
        self.assertIn('Python, SQL, Docker', prompt)
        self.assertIn('Опытный разработчик', prompt)
    
    def test_create_cover_letter_prompt(self):
        """
        Тест создания промпта для сопроводительного письма
        """
        user_profile = {
            'full_name': 'Иван Иванов',
            'skills': 'Python, SQL, Docker',
            'base_resume': 'Опытный разработчик'
        }
        
        vacancy_info = {
            'title': 'Python разработчик',
            'company': 'Компания X',
            'city': 'Москва',
            'description': 'Требуется Python разработчик'
        }
        
        prompt = self.llm_service._create_cover_letter_prompt(user_profile, vacancy_info)
        
        self.assertIn('Python разработчик', prompt)
        self.assertIn('Компания X', prompt)
        self.assertIn('Москва', prompt)
        self.assertIn('Требуется Python разработчик', prompt)
        self.assertIn('Иван Иванов', prompt)
        self.assertIn('Python, SQL, Docker', prompt)
    
    @patch('bot.services.llm_service.requests.post')
    def test_call_llm_api_success(self, mock_post):
        """
        Тест вызова LLM API при успешном ответе
        """
        # Подготовка mock-ответа
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': 'Сгенерированное резюме'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Вызов тестируемого метода
        result = self.llm_service._call_llm_api("Тестовый промпт")
        
        # Проверка результата
        self.assertEqual(result, 'Сгенерированное резюме')
        mock_post.assert_called_once()
    
    @patch('bot.services.llm_service.requests.post')
    def test_call_llm_api_error(self, mock_post):
        """
        Тест вызова LLM API при ошибке
        """
        # Подготовка mock-ответа
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        # Вызов тестируемого метода
        result = self.llm_service._call_llm_api("Тестовый промпт")
        
        # Проверка результата
        self.assertIsNone(result)
        mock_post.assert_called_once()
    
    @patch('bot.services.llm_service.LLMService._call_llm_api')
    def test_generate_resume(self, mock_call_api):
        """
        Тест генерации резюме
        """
        mock_call_api.return_value = 'Сгенерированное резюме'
        
        user_profile = {
            'full_name': 'Иван Иванов',
            'skills': 'Python, SQL, Docker',
            'base_resume': 'Опытный разработчик'
        }
        
        vacancy_info = {
            'title': 'Python разработчик',
            'company': 'Компания X',
            'city': 'Москва',
            'salary_from': 150000,
            'salary_to': 200000,
            'salary_currency': 'RUR',
            'description': 'Требуется Python разработчик'
        }
        
        result = self.llm_service.generate_resume(user_profile, vacancy_info)
        
        self.assertEqual(result, 'Сгенерированное резюме')
        mock_call_api.assert_called_once()
        # Проверяем, что был вызван метод создания промпта
        # (проверка косвенная - через вызов _call_llm_api с каким-то промптом)
    
    @patch('bot.services.llm_service.LLMService._call_llm_api')
    def test_generate_cover_letter(self, mock_call_api):
        """
        Тест генерации сопроводительного письма
        """
        mock_call_api.return_value = 'Сгенерированное сопроводительное письмо'
        
        user_profile = {
            'full_name': 'Иван Иванов',
            'skills': 'Python, SQL, Docker',
            'base_resume': 'Опытный разработчик'
        }
        
        vacancy_info = {
            'title': 'Python разработчик',
            'company': 'Компания X',
            'city': 'Москва',
            'salary_from': 150000,
            'salary_to': 200000,
            'salary_currency': 'RUR',
            'description': 'Требуется Python разработчик'
        }
        
        result = self.llm_service.generate_cover_letter(user_profile, vacancy_info)
        
        self.assertEqual(result, 'Сгенерированное сопроводительное письмо')
        mock_call_api.assert_called_once()