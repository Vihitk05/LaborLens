from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Job Market Analysis API"
    BACKEND_CORS_ORIGINS: list = ["*"]
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    EVENT_BUS_URL: str = "redis://localhost:6379/1"
    TAVILY_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()