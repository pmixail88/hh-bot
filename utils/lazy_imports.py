# utils/lazy_imports.py
"""
Ленивые импорты для избежания циклических зависимостей
"""

class LazyImport:
    """Ленивый импорт для избежания циклических зависимостей"""
    
    def __init__(self, module_name, class_name=None):
        self.module_name = module_name
        self.class_name = class_name
        self._module = None
        self._class = None
    
    def _import(self):
        if self._module is None:
            module = __import__(self.module_name, fromlist=[''])
            self._module = module
            
            if self.class_name:
                self._class = getattr(module, self.class_name)
    
    @property
    def module(self):
        self._import()
        return self._module
    
    @property
    def klass(self):
        self._import()
        return self._class

# Ленивые импорты для проблемных модулей
LLMService = LazyImport('services.llm_service', 'LLMService')
SecureConfigService = LazyImport('services.secure_config', 'SecureConfigService')
HHService = LazyImport('services.hh_service', 'HHService')
VacancyScheduler = LazyImport('utils.scheduler', 'VacancyScheduler')