from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    groq_api_key: str = ""
    gemini_api_key: str = ""
    llm_provider: str = "groq"
    
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-1.5-flash"
    
    eval_threshold_hallucination: float = 0.05
    eval_threshold_latency_p95: float = 5.0
    
    dataset_path: str = "dataset/golden.json"
    reports_dir: str = "reports"
    
    app_name: str = "LLM Eval Pipeline"
    version: str = "1.0.0"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()