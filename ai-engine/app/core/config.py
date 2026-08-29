from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    PYTHON_ENGINE_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    FLASHCARD_MIN: int = 5
    FLASHCARD_MAX: int = 15


settings = Settings()
