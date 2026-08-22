from app.core.config import settings


def test_settings_loads_default_model():
    assert settings.DEFAULT_LLM_MODEL == "llama-3.1-70b-versatile"


def test_settings_loads_cors_origins():
    assert "http://localhost:5173" in settings.CORS_ORIGINS


def test_settings_has_port():
    assert settings.PYTHON_ENGINE_PORT == 8000
