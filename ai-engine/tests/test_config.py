from app.core.config import settings


def test_settings_loads_default_model():
    assert settings.DEFAULT_LLM_MODEL == "openai/gpt-oss-120b"


def test_settings_loads_gemini_model():
    assert settings.GEMINI_MODEL == "gemini-3.5-flash-lite"


def test_settings_loads_cors_origins():
    assert "http://localhost:5173" in settings.CORS_ORIGINS


def test_settings_has_port():
    assert settings.PYTHON_ENGINE_PORT == 8000
