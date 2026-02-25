from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
print("Base dir", BASE_DIR)

class Settings(BaseSettings):
    # ---- FastAPI ----
    APP_NAME: str
    APP_ENV: str

    # ---- Database ----
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    DATABASE_URL: str
    ALEMBIC_URL: str

    # ---- Redis ----
    REDIS_URL: str

    # ---- JWT ----
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # ---- SMTP ----
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str

    # ---- Elastic Search ----
    ELASTIC_SEARCH_HOST: str

    # ---- OTP ----
    OTP_TTL: int

    # ---- OpenAI ----
    OPENAI_API_KEY: str


    @property
    def db_url(self) -> str:
        return self.DATABASE_URL or f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = BASE_DIR / ".env"
        extra = "ignore"