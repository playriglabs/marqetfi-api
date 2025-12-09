from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    port: int = 8000
    environment: str = "development"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()