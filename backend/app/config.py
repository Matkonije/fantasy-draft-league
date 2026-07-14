from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://fantasy:fantasy_dev_password@localhost:5433/fantasy_draft"
    secret_key: str = "dev-secret-do-not-use-in-production"
    access_token_expire_minutes: int = 10080
    jwt_algorithm: str = "HS256"


settings = Settings()
