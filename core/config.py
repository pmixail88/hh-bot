import os
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

#from services.llm_service import LLMService

load_dotenv()

@dataclass
class DatabaseConfig:
    def __init__(self):
        self.driver = "postgresql+asyncpg"
        self.host = "ep-solitary-brook-agmztrhf-pooler.c-2.eu-central-1.aws.neon.tech" 
        self.port = 5432
        self.username = "neondb_owner"
        self.password = "npg_X2MjE8RsNdDH"
        self.database = "neondb"
        self.echo = False  # Добавляем атрибут echo
        self.pool_size = 100  # Добавляем другие возможные атрибуты
        self.max_overflow = 200  # Добавляем другие возможные атрибуты
        
    @property
    def url(self) -> str:
        return (
            f"{self.driver}://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}?"
            f"ssl=require"
        )
    
    @property
    def sync_url(self) -> str:
        # Для psycopg2 (Alembic) - используем sslmode вместо ssl
        return (
            f"postgresql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}?"
            f"sslmode=require"
        )

@dataclass
class HHConfig:
    client_id: str = os.getenv("HH_CLIENT_ID", "")
    client_secret: str = os.getenv("HH_CLIENT_SECRET", "")
    access_token: Optional[str] = None  # Добавьте это
    refresh_token: Optional[str] = None  # Добавьте это
    timeout: int = int(os.getenv("HH_API_TIMEOUT", "30"))
    max_results: int = int(os.getenv("HH_MAX_RESULTS", "100"))
    
@dataclass
class LLMConfig:
    # Используем OpenRouter
    base_url: str = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    api_key: str = os.getenv("LLM_API_KEY", "")
    model_name: str = os.getenv("LLM_MODEL_NAME", "mistralai/mistral-7b-instruct:free")
    timeout: int = int(os.getenv("LLM_TIMEOUT", "60"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
@dataclass
class SchedulerConfig:
    enabled: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    default_times: str = os.getenv("SCHEDULER_TIMES", "09:00,18:00")
    check_interval_hours: int = int(os.getenv("CHECK_INTERVAL_HOURS", "24"))

@dataclass
class BotConfig:
    token: str = os.getenv("BOT_TOKEN", "")
    app_name: str = "HH Work Day Bot"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: str = os.getenv("REDIS_PASSWORD", "")
    decode_responses: bool = True
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

@dataclass
class Config:
    bot: BotConfig
    database: DatabaseConfig
    hh: HHConfig
    llm: LLMConfig
    scheduler: SchedulerConfig
    redis: RedisConfig

@lru_cache()
def get_config() -> Config:
    return Config(
        bot=BotConfig(),
        database=DatabaseConfig(),
        hh=HHConfig(),
        llm=LLMConfig(),
        scheduler=SchedulerConfig(),
        redis=RedisConfig()
    )