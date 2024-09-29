import enum
from pathlib import Path
from tempfile import gettempdir
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL
from pydantic import Field

TEMP_DIR = Path(gettempdir())


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8000

    api_version: str = "v1"

    secret_key: str = Field(env="BACKEND_SECRET_KEY")
    algorithm: str = "HS256"

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 180

    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False

    # Current environment
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO
    # Variables for the database
    db_host: str = Field(default="localhost", env="BACKEND_DB_HOST")
    db_port: int = Field(default=5432, env="BACKEND_DB_PORT")
    db_user: str = Field(env="BACKEND_DB_USER")
    db_pass: str = Field(env="BACKEND_DB_PASS")
    db_base: str = Field(env="BACKEND_DB_BASE")
    db_echo: bool = Field(default=False, env="BACKEND_DB_ECHO")
    
    # Variables for Redis
    redis_host: str = "backend-redis"
    redis_port: int = 6379
    redis_user: Optional[str] = None
    redis_pass: Optional[str] = None
    redis_base: Optional[int] = None

    # This variable is used to define
    # multiproc_dir. It's required for [uvi|guni]corn projects.
    prometheus_dir: Path = TEMP_DIR / "prom"

    # Sentry's configuration.
    sentry_dsn: Optional[str] = None
    sentry_sample_rate: float = 1.0

    MAIL_SERVER: str = Field(env="BACKEND_MAIL_SERVER")
    MAIL_PORT: int = Field(default=587, env="BACKEND_MAIL_PORT")
    MAIL_USERNAME: str = Field(env="BACKEND_MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(env="BACKEND_MAIL_PASSWORD")
    EMAIL_FROM: str = Field(env="BACKEND_EMAIL_FROM")

    swagger_cookie: bool = True

    @property
    def db_url(self) -> URL:
        """
        Assemble database URL from settings.

        :return: database URL.
        """
        return URL.build(
            scheme="postgresql+asyncpg",
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_pass,
            path=f"/{self.db_base}",
        )

    @property
    def redis_url(self) -> URL:
        """
        Assemble REDIS URL from settings.

        :return: redis URL.
        """
        path = ""
        if self.redis_base is not None:
            path = f"/{self.redis_base}"
        return URL.build(
            scheme="redis",
            host=self.redis_host,
            port=self.redis_port,
            user=self.redis_user,
            password=self.redis_pass,
            path=path,
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BACKEND_",
        env_file_encoding="utf-8",
    )


settings = Settings()
