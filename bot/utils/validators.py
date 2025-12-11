# Input validators
import re

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    pattern = r'^[+]?[\d\s\-\(\)]{10,}$'
    return bool(re.match(pattern, phone))

def validate_salary(salary: str) -> bool:
    """Validate salary input"""
    return salary.isdigit() and int(salary) > 0