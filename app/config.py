from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # локально по умолчанию SQLite, в Docker/проде переопределим на Postgres
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./app.db")
    # любые прочие настройки по желанию:
    SECRET_KEY: str = Field(default="change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"      # читаем переменные из файла .env при наличии
        case_sensitive = True

settings = Settings()
