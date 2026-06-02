from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    DATABASE_URL: SecretStr
    DATABASE_USER: str
    DATABASE_PASSWORD: SecretStr
    DATABASE_NAME: str

    REDIS_URL: SecretStr

    ACCESS_SECRET_KEY: SecretStr
    ACCESS_MINUTES_EXPIRES: int

    REFRESH_SECRET_KEY: SecretStr
    REFRESH_DAYS_EXPIRES: int

    ALGORITHM: str

    AUTO_CREATE_TABLES: bool = False


settings = Settings()  # type: ignore
