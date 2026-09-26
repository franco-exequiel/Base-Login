from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Portfolio API"
    database_url: str = "sqlite:///./portfolio.db"
    jwt_secret: str = Field(default="local-development-secret-change-me-32", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"

    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    mail_host: str = "smtp.gmail.com"
    mail_port: int = 587
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    email_verification_minutes: int = 30
    password_reset_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    @property
    def clean_mail_password(self) -> str:
        return self.mail_password.replace(" ", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
