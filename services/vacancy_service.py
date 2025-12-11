# Vacancy processing service
from .hh_service import HHService

class VacancyService:
    def __init__(self):
        self.hh_service = HHService()
    
    async def process_vacancies(self, query: str):
        """Process and filter vacancies"""
        vacancies = await self.hh_service.search_vacancies(query)
        return self._filter_relevant_vacancies(vacancies)
    
    def _filter_relevant_vacancies(self, vacancies):
        """Filter vacancies based on criteria"""
        return vacancies[:10]  # Return top 10