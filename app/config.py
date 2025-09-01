from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # локально по умолчанию SQLite, в Docker/проде переопределим на Postgres
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./app.db")
    # любые прочие настройки
    SECRET_KEY: str = Field(default="change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",        # читать переменные из .env
        case_sensitive=True,    # имена переменных чувствительны к регистру
    )


settings = Settings()
