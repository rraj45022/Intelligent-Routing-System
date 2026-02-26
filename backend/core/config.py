from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Ticket Router"
    database_url: str  # expect postgresql+asyncpg://...
    env: str = "local"

    # Auth
    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Demo data feed
    demo_ticket_feed_enabled: bool = True
    demo_ticket_feed_interval_seconds: float = 10.0

    # Optional LLM scoring
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_provider: str = "openai"  # openai | grok | custom
    llm_base_url: str | None = None  # e.g., https://api.x.ai/v1 for Grok
    llm_weight: float = 0.4  # blending weight with ML score

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
