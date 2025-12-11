from aiogram.fsm.state import State, StatesGroup

class SearchStates(StatesGroup):
    waiting_keywords = State()
    waiting_region = State()
    waiting_salary_from = State()
    waiting_salary_to = State()
    waiting_experience = State()
    waiting_employment = State()
    waiting_schedule = State()
    waiting_period = State()

class ProfileStates(StatesGroup):
    waiting_name = State()
    waiting_city = State()
    waiting_position = State()
    waiting_skills = State()
    waiting_resume = State()
    waiting_schedule = State()
    waiting_email = State()  # ДОБАВИТЬ
    waiting_phone = State()  # Добавить

class LLMStates(StatesGroup):
    waiting_api_key = State()
    waiting_base_url = State()
    waiting_model = State()
    waiting_temperature = State()  # ДОБАВЛЕНО недостающее состояние

    
# ДОБАВИТЬ новый класс для откликов
class ResponseStates(StatesGroup):
    waiting_contact_email = State()
    waiting_contact_phone = State()
    waiting_hh_resume_id = State()
    waiting_hh_auth = State()  # ДОБАВЛЕНО
    waiting_contact = State()  # Ожидаем контактные данные
    waiting_schedule = State()  # Ожидаем выбор графика работы
    

class HHAPIStates(StatesGroup):
    waiting_client_id = State()
    waiting_client_secret = State()
    waiting_hh_email = State()
    waiting_hh_password = State()

__all__ = [
    'SearchStates',
    'ProfileStates', 
    'LLMStates',
    'ResponseStates'
]