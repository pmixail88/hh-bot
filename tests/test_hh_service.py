import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from bot.services.hh_service import HHService


class TestHHService(unittest.TestCase):
    """
    Тесты для сервиса HH.ru
    """
    
    def setUp(self):
        self.hh_service = HHService()
    
    def test_init_service(self):
        """
        Тест инициализации сервиса
        """
        self.assertEqual(self.hh_service.base_url, "https://api.hh.ru")
        self.assertIsNotNone(self.hh_service.session)
        
    @patch('bot.services.hh_service.requests.Session.get')
    def test_get_area_id_success(self, mock_get):
        """
        Тест получения ID региона по названию города
        """
        # Подготовка mock-ответа
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'id': '1', 'text': 'Москва'},
                {'id': '2', 'text': 'Санкт-Петербург'}
            ]
        }
        mock_get.return_value = mock_response
        
        # Вызов тестируемого метода
        result = self.hh_service.get_area_id("Москва")
        
        # Проверка результата
        self.assertEqual(result, '1')
        mock_get.assert_called_once_with(
            "https://api.hh.ru/suggests/area", 
            params={'text': 'Москва'}
        )
    
    @patch('bot.services.hh_service.requests.Session.get')
    def test_get_area_id_not_found(self, mock_get):
        """
        Тест получения ID региона, когда город не найден
        """
        # Подготовка mock-ответа
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'items': []}
        mock_get.return_value = mock_response
        
        # Вызов тестируемого метода
        result = self.hh_service.get_area_id("НеизвестныйГород")
        
        # Проверка результата
        self.assertIsNone(result)
    
    @patch('bot.services.hh_service.requests.Session.get')
    def test_get_area_id_api_error(self, mock_get):
        """
        Тест получения ID региона при ошибке API
        """
        # Подготовка mock-ответа
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Вызов тестируемого метода
        result = self.hh_service.get_area_id("Москва")
        
        # Проверка результата
        self.assertIsNone(result)
    
    def test_parse_vacancy_success(self):
        """
        Тест парсинга вакансии из ответа API
        """
        # Подготовка тестовых данных
        raw_vacancy = {
            'id': '123456',
            'name': 'Python разработчик',
            'area': {'name': 'Москва'},
            'salary': {
                'from': 150000,
                'to': 200000,
                'currency': 'RUR'
            },
            'snippet': {'requirement': 'Опыт работы от 3 лет'},
            'alternate_url': 'https://hh.ru/vacancy/123456',
            'published_at': '2023-10-01T12:00:00+03:00',
            'employer': {'name': 'ОО Рога и Копыта', 'id': '789'},
            'experience': {'name': 'От 3 до 6 лет'},
            'employment': {'name': 'Полная занятость'},
            'schedule': {'name': 'Полный день'}
        }
        
        # Вызов тестируемого метода
        result = self.hh_service.parse_vacancy(raw_vacancy)
        
        # Проверка результата
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], '123456')
        self.assertEqual(result['title'], 'Python разработчик')
        self.assertEqual(result['city'], 'Москва')
        self.assertEqual(result['salary_from'], 150000)
        self.assertEqual(result['salary_to'], 200000)
        self.assertEqual(result['salary_currency'], 'RUR')
        self.assertEqual(result['description'], 'Опыт работы от 3 лет')
        self.assertEqual(result['url'], 'https://hh.ru/vacancy/123456')
        self.assertEqual(result['company'], 'ОО Рога и Копыта')
        self.assertEqual(result['employer_id'], '789')
        self.assertEqual(result['experience'], 'От 3 до 6 лет')
        self.assertEqual(result['employment'], 'Полная занятость')
        self.assertEqual(result['schedule'], 'Полный день')
        self.assertIsInstance(result['published_at'], datetime)
    
    def test_parse_vacancy_with_none_values(self):
        """
        Тест парсинга вакансии с отсутствующими полями
        """
        # Подготовка тестовых данных
        raw_vacancy = {
            'id': '123456',
            'name': 'Python разработчик',
            'area': {},
            'salary': None,
            'snippet': {},
            'alternate_url': 'https://hh.ru/vacancy/123456',
            'published_at': '2023-10-01T12:00:00+03:00',
            'employer': {},
            'experience': {},
            'employment': {},
            'schedule': {}
        }
        
        # Вызов тестируемого метода
        result = self.hh_service.parse_vacancy(raw_vacancy)
        
        # Проверка результата
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], '123456')
        self.assertEqual(result['title'], 'Python разработчик')
        self.assertEqual(result['city'], '')
        self.assertIsNone(result['salary_from'])
        self.assertIsNone(result['salary_to'])
        self.assertIsNone(result['salary_currency'])
        self.assertEqual(result['description'], '')
        self.assertEqual(result['url'], 'https://hh.ru/vacancy/123456')
        self.assertEqual(result['company'], '')
        self.assertEqual(result['employer_id'], '')
        self.assertEqual(result['experience'], '')
        self.assertEqual(result['employment'], '')
        self.assertEqual(result['schedule'], '')
        self.assertIsInstance(result['published_at'], datetime)