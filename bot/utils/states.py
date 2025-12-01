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

class LLMStates(StatesGroup):
    waiting_api_key = State()
    waiting_base_url = State()
    waiting_model = State()
    waiting_temperature = State()  # ДОБАВЛЕНО недостающее состояние

class VacancyStates(StatesGroup):
    browsing = State()
    viewing_details = State()
    saving_notes = State()