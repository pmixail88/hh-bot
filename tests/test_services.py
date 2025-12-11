import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from bot.services.hh_service import HHService

class TestHHService(unittest.TestCase):
    def setUp(self):
        self.hh_service = HHService()
    
    def test_init_service(self):
        self.assertEqual(self.hh_service.base_url, "https://api.hh.ru")
        self.assertIsNotNone(self.hh_service.session)
        
    @patch('bot.services.hh_service.requests.Session.get')
    def test_get_area_id_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'id': '1', 'text': 'Москва'},
                {'id': '2', 'text': 'Санкт-Петербург'}
            ]
        }
        mock_get.return_value = mock_response
        
        result = self.hh_service.get_area_id("Москва")
        
        self.assertEqual(result, '1')
        mock_get.assert_called_once_with(
            "https://api.hh.ru/suggests/areas", 
            params={'text': 'Москва'}
        )
    
    @patch('bot.services.hh_service.requests.Session.get')
    def test_get_area_id_not_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'items': []}
        mock_get.return_value = mock_response
        
        result = self.hh_service.get_area_id("НеизвестныйГород")
        
        self.assertIsNone(result)
    
    def test_parse_vacancy_success(self):
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
        
        result = self.hh_service.parse_vacancy(raw_vacancy)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], '123456')
        self.assertEqual(result['title'], 'Python разработчик')
        self.assertEqual(result['city'], 'Москва')
        self.assertEqual(result['salary_from'], 150000)
        self.assertEqual(result['salary_to'], 200000)
        self.assertEqual(result['salary_currency'], 'RUR')