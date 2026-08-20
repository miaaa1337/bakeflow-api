from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(
      env_file=".env", env_file_encoding="utf-8", extra="ignore"
  )
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()

# ⚠️ ВАЖНО: эта строчка должна быть САМОЙ ПОСЛЕДНЕЙ и ТЕКСТОМ С САМОГО НАЧАЛА СТРОКИ (без отступов/табов)!
DATABASE_URL = settings.DATABASE_URL