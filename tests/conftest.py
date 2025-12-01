import pytest
from unittest.mock import Mock, AsyncMock
from services.hh_service import HHService
from services.llm_service import LLMService
from core.config import HHConfig, LLMConfig

class TestHHService:
    @pytest.fixture
    def hh_service(self):
        config = HHConfig()
        return HHService(config)
    
    @pytest.mark.asyncio
    async def test_search_vacancies(self, hh_service):
        mock_filter = Mock()
        mock_filter.keywords = "python"
        mock_filter.region = "Москва"
        
        vacancies = await hh_service.search_vacancies(mock_filter)
        assert isinstance(vacancies, list)

class TestLLMService:
    @pytest.fixture
    def llm_service(self):
        config = LLMConfig()
        return LLMService(config)
    
    def test_create_resume_prompt(self, llm_service):
        user_profile = {
            "full_name": "Иван Иванов",
            "skills": "Python, SQL"
        }
        vacancy_info = {
            "name": "Python разработчик",
            "company_name": "Тест компания"
        }
        
        prompt = llm_service._create_resume_prompt(user_profile, vacancy_info)
        assert "Python разработчик" in prompt
        assert "Иван Иванов" in prompt