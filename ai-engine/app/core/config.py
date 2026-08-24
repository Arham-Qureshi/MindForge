from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "openai/gpt-oss-120b"
    PYTHON_ENGINE_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()
