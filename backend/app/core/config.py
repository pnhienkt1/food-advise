from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./foodadvise.db"
    redis_url: str = "redis://localhost:6379/0"
    off_api_url: str = "https://world.openfoodfacts.org"
    usda_api_key: str = ""
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    cors_allow_cloudflare: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
