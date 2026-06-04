from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CampusLensAI Backend"
    app_version: str = "1.0.0"

    database_url: str = "sqlite:///./campuslens.db"

    secret_key: str = "campuslensai_dev_secret_key_change_later"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()