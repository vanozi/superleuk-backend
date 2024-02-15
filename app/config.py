import logging
import os
from functools import lru_cache
from pathlib import Path
from pydantic import AnyUrl, SecretStr
from pydantic_settings import BaseSettings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

log = logging.getLogger("uvicorn")


class Settings(BaseSettings):
    app_name: str = "TEST APP"
    environment: str = "dev"
    testing: bool = False
    database_url: AnyUrl = "postgres://postgres:postgres@database:5432/test"
    token_algorithm: str = "HS256"
    secret_key: SecretStr = "erruggeheim"
    registration_token_lifetime: int = 10080
    login_token_lifetime: int = 1440
    refresh_token_lifetime: int = 43800
    reset_password_token_lifetime: int = 10080


@lru_cache()
def get_settings() -> BaseSettings:
    log.info("Loading config settings from the environment...")
    return Settings()


@lru_cache
def get_fastapi_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM"),
        MAIL_PORT=os.getenv("MAIL_PORT"),
        MAIL_SERVER=os.getenv("MAIL_SERVER"),
        MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
        MAIL_STARTTLS=os.getenv("MAIL_STARTTLS"),
        MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS"),
        TEMPLATE_FOLDER=Path(__file__).parent / "templates",
    )
