from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str
    openai_base_url: str = "https://openrouter.ai/api/v1"
    chroma_path: str = "chroma_data"
    embedding_model: str = "openai/text-embedding-3-small"
    summary_model: str = "openai/gpt-4o-mini"
    database_url: str = "postgresql://localhost/meridian"
    min_messages_for_auto_summarize: int = 5


settings = Settings()
