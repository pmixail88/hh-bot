import json
import requests
from typing import Dict, Optional
from bot.config import get_settings


class LLMService:
    """
    Сервис для работы с LLM API
    """
    def __init__(self):
        self.settings = get_settings()

    def generate_resume(self, user_profile: Dict, vacancy_info: Dict) -> Optional[str]:
        """
        Генерация адаптированного резюме
        
        :param user_profile: Профиль пользователя (навыки, опыт и т.д.)
        :param vacancy_info: Информация о вакансии
        :return: Сгенерированное резюме
        """
        prompt = self._create_resume_prompt(user_profile, vacancy_info)
        return self._call_llm_api(prompt)

    def generate_cover_letter(self, user_profile: Dict, vacancy_info: Dict) -> Optional[str]:
        """
        Генерация сопроводительного письма
        
        :param user_profile: Профиль пользователя (навыки, опыт и т.д.)
        :param vacancy_info: Информация о вакансии
        :return: Сгенерированное сопроводительное письмо
        """
        prompt = self._create_cover_letter_prompt(user_profile, vacancy_info)
        return self._call_llm_api(prompt)

    def _create_resume_prompt(self, user_profile: Dict, vacancy_info: Dict) -> str:
        """
        Создание промпта для генерации резюме
        """
        return f"""
Создай профессиональное резюме на русском языке, адаптированное под следующую вакансию:

ВАКАНСИЯ:
- Должность: {vacancy_info.get('title', 'Не указана')}
- Компания: {vacancy_info.get('company', 'Не указана')}
- Город: {vacancy_info.get('city', 'Не указан')}
- Зарплата: {vacancy_info.get('salary_from', 'Не указана')} - {vacancy_info.get('salary_to', 'Не указана')} {vacancy_info.get('salary_currency', '')}
- Описание: {vacancy_info.get('description', 'Не указано')}

ПРОФИЛЬ КАНДИДАТА:
- Имя: {user_profile.get('full_name', 'Не указано')}
- Навыки: {user_profile.get('skills', 'Не указаны')}
- Базовое резюме: {user_profile.get('base_resume', 'Не указано')}

Создай структурированное резюме, которое подчеркивает релевантные навыки и опыт кандидата для этой конкретной вакансии.
Резюме должно быть профессиональным, кратким и убедительным.
"""

    def _create_cover_letter_prompt(self, user_profile: Dict, vacancy_info: Dict) -> str:
        """
        Создание промпта для генерации сопроводительного письма
        """
        return f"""
Создай сопроводительное письмо на русском языке для следующей вакансии:

ВАКАНСИЯ:
- Должность: {vacancy_info.get('title', 'Не указана')}
- Компания: {vacancy_info.get('company', 'Не указана')}
- Город: {vacancy_info.get('city', 'Не указан')}
- Описание: {vacancy_info.get('description', 'Не указано')}

ПРОФИЛЬ КАНДИДАТА:
- Имя: {user_profile.get('full_name', 'Не указано')}
- Навыки: {user_profile.get('skills', 'Не указаны')}
- Опыт: {user_profile.get('base_resume', 'Не указано')}

Сопроводительное письмо должно быть персонализированным, демонстрировать интерес к вакансии и компании,
а также подчеркивать, как опыт и навыки кандидата соответствуют требованиям вакансии.
"""

    def _call_llm_api(self, prompt: str) -> Optional[str]:
        """
        Вызов LLM API
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.llm_api_key}"
            }

            data = {
                "model": self.settings.llm_model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }

            response = requests.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"Ошибка при вызове LLM API: {response.status_code}, {response.text}")
                return None

        except Exception as e:
            print(f"Исключение при вызове LLM API: {e}")
            return None