from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str = "http://13.40.237.133:4000/v1"
    llm_model: str = "claude-sonnet"
    # Lightweight model for fast intent classification
    # Options: claude-haiku (fast), claude-sonnet (balanced), gpt-4o-mini (if available)
    # Falls back to main model if fast model not specified
    llm_model_fast: str = Field(default="claude-haiku", alias="LLM_MODEL_FAST")
    # Whisper model size: tiny, base, small, medium, large
    # 'base' is default, use 'small' or 'medium' for better Arabic accuracy
    whisper_model_size: str = Field(default="base", alias="WHISPER_MODEL_SIZE")
    database_url: str = "sqlite:///./data/customer_service.db"
    max_retries: int = 3
    request_timeout: int = 10
    escalation_threshold: float = Field(default=0.6, alias="escalation_confidence_threshold")
    max_auto_refund: float = 50.0
    
    # Performance settings
    use_fast_model_for_intent: bool = Field(default=True, alias="USE_FAST_MODEL_FOR_INTENT")
    # Aggressive performance mode - reduces timeouts and token limits
    aggressive_performance: bool = Field(default=True, alias="AGGRESSIVE_PERFORMANCE")
    # Max conversation history to load (lower = faster)
    max_history_context: int = Field(default=4, alias="MAX_HISTORY_CONTEXT")
    
    # LangSmith config
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")
    langsmith_endpoint: str = Field(default="https://eu.api.smith.langchain.com", alias="LANGSMITH_ENDPOINT")
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="customer-service-agent", alias="LANGSMITH_PROJECT")
    
    class Config:
        env_file = ".env"
        populate_by_name = True

settings = Settings()

# Configure LangSmith if enabled
if settings.langsmith_tracing and settings.langsmith_api_key:
    # LangSmith uses LANGCHAIN_* environment variables
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

