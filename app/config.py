from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    chroma_path: str = "chroma_data"
    embedding_model: str = "text-embedding-3-small"
    
    class Config:
        env_file = ".env"
        
    
settings = Settings()