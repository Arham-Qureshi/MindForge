import json
import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from app.pipelines.llm_client import (
    LLMClient,
    LLMError,
    LLMResult,
    MAX_OUTPUT_TOKENS,
)
from app.pipelines.base_pipeline import execute_chunks, _deduplicate
from app.prompts import INJECTION_GUARD


class MockSchema(BaseModel):
    result: str


def make_groq_response(content='{"result": "ok"}', total_tokens=42):
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    response.usage.total_tokens = total_tokens
    return response


def test_deduplicate_removes_duplicates():
    items = [{"question": "What is X?", "answer": "A"}, {"question": "What is X?", "answer": "B"}]
    assert len(_deduplicate(items, key="question")) == 1


def test_deduplicate_keeps_unique():
    items = [{"question": "What is X?", "answer": "A"}, {"question": "What is Y?", "answer": "B"}]
    assert len(_deduplicate(items, key="question")) == 2


def test_execute_chunks_calls_llm():
    with patch("app.pipelines.base_pipeline.llm_client") as mock_client:
        mock_client.complete.return_value = LLMResult(json.dumps({"result": "ok"}), 10)
        results = execute_chunks(["chunk1", "chunk2"], task="chunker")
        assert len(results) == 2
        assert mock_client.complete.call_count == 2


def test_max_output_tokens_all_below_tpm():
    for reserve in MAX_OUTPUT_TOKENS.values():
        assert reserve < 6000


def test_complete_returns_llm_result_with_usage():
    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value = make_groq_response(
            total_tokens=123
        )
        result = LLMClient().complete(task="chunker", user="hello")
    assert isinstance(result, LLMResult)
    assert result.content == '{"result": "ok"}'
    assert result.total_tokens == 123


def test_groq_uses_task_output_reserve():
    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value = make_groq_response()
        LLMClient().complete(task="notes_flashcards", user="u")
    assert MockGroq.return_value.chat.completions.create.call_args[1]["max_tokens"] == 2000


def test_llm_client_guard_in_system_message():
    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value = make_groq_response()
        LLMClient().complete(task="chunker", user="sensitive text")
        call_args = MockGroq.return_value.chat.completions.create.call_args
        system_msg = call_args[1]["messages"][0]["content"]
        user_msg = call_args[1]["messages"][1]["content"]
        assert "security_policy" in system_msg
        assert "UNTRUSTED INPUT" in system_msg
        assert "<user_document_content>" in user_msg
        assert "sensitive text" in user_msg


def test_llm_client_json_mode():
    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value = make_groq_response()
        LLMClient().complete(task="chunker", user="test", json_mode=True)
        call_args = MockGroq.return_value.chat.completions.create.call_args
        assert call_args[1]["response_format"] == {"type": "json_object"}


def test_llm_client_no_json_mode():
    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value = make_groq_response()
        LLMClient().complete(task="chunker", user="test", json_mode=False)
        call_args = MockGroq.return_value.chat.completions.create.call_args
        assert "response_format" not in call_args[1]


def test_execute_chunks_validates_with_schema():
    with patch("app.pipelines.base_pipeline.llm_client") as mock_client:
        mock_client.complete.return_value = LLMResult(json.dumps({"result": "ok"}), 10)
        results = execute_chunks(["chunk1"], task="chunker", schema=MockSchema)
        assert results == [{"result": "ok"}]


def test_execute_chunks_retries_on_failure():
    with patch("app.pipelines.base_pipeline.llm_client") as mock_client, \
         patch("app.pipelines.base_pipeline.time.sleep"):
        mock_client.complete.side_effect = [
            Exception("API error"),
            LLMResult(json.dumps({"result": "ok"}), 10),
        ]
        results = execute_chunks(["chunk1"], task="chunker", max_retries=2)
        assert results == [{"result": "ok"}]
        assert mock_client.complete.call_count == 2


def test_llm_client_routes_pyq_to_gemini():
    mock_response = MagicMock()
    mock_response.text = '{"result": "ok"}'
    mock_response.usage_metadata.total_token_count = 55
    with patch("app.pipelines.llm_client.Groq") as MockGroq, \
         patch("app.pipelines.llm_client.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        result = LLMClient().complete(task="pyq", user="test", json_mode=True)
        assert result.content == '{"result": "ok"}'
        assert result.total_tokens == 55
        MockGroq.return_value.chat.completions.create.assert_not_called()


def test_llm_client_routes_notes_to_groq():
    with patch("app.pipelines.llm_client.Groq") as MockGroq, \
         patch("app.pipelines.llm_client.genai") as mock_genai:
        MockGroq.return_value.chat.completions.create.return_value = make_groq_response()
        LLMClient().complete(task="notes_flashcards", user="test")
        MockGroq.return_value.chat.completions.create.assert_called_once()
        mock_genai.Client.return_value.models.generate_content.assert_not_called()


def test_llm_client_routes_syllabus_to_groq():
    with patch("app.pipelines.llm_client.Groq") as MockGroq, \
         patch("app.pipelines.llm_client.genai") as mock_genai:
        MockGroq.return_value.chat.completions.create.return_value = make_groq_response()
        LLMClient().complete(task="syllabus", user="test")
        MockGroq.return_value.chat.completions.create.assert_called_once()
        mock_genai.Client.return_value.models.generate_content.assert_not_called()


def test_gemini_json_mode():
    mock_response = MagicMock()
    mock_response.text = '{"result": "ok"}'
    with patch("app.pipelines.llm_client.Groq"), \
         patch("app.pipelines.llm_client.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        LLMClient().complete(task="pyq", user="test", json_mode=True)
        config = mock_genai.Client.return_value.models.generate_content.call_args[1]["config"]
        assert config.response_mime_type == "application/json"


def test_gemini_no_json_mode():
    mock_response = MagicMock()
    mock_response.text = 'plain text'
    with patch("app.pipelines.llm_client.Groq"), \
         patch("app.pipelines.llm_client.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        LLMClient().complete(task="pyq", user="test", json_mode=False)
        config = mock_genai.Client.return_value.models.generate_content.call_args[1]["config"]
        assert config.response_mime_type is None


def test_gemini_uses_task_output_reserve():
    mock_response = MagicMock()
    mock_response.text = "{}"
    with patch("app.pipelines.llm_client.Groq"), \
         patch("app.pipelines.llm_client.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        LLMClient().complete(task="pyq", user="u")
        config = mock_genai.Client.return_value.models.generate_content.call_args[1]["config"]
        assert config.max_output_tokens == 3000


def _raise_groq(exc):
    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.side_effect = exc
        LLMClient().complete(task="syllabus", user="u")


def test_groq_429_maps_to_retryable_error_with_retry_after():
    import groq
    err = groq.RateLimitError(
        message="rate limited",
        response=MagicMock(status_code=429, headers={"retry-after": "7"}),
        body=None,
    )
    with pytest.raises(LLMError) as ei:
        _raise_groq(err)
    assert ei.value.retryable is True
    assert ei.value.retry_after == pytest.approx(7.0)
    assert ei.value.provider == "groq"


def test_groq_413_maps_to_fatal_error():
    import groq
    err = groq.APIStatusError(
        message="too large",
        response=MagicMock(status_code=413, headers={}),
        body=None,
    )
    with pytest.raises(LLMError) as ei:
        _raise_groq(err)
    assert ei.value.retryable is False


def test_groq_5xx_maps_to_retryable_error():
    import groq
    err = groq.InternalServerError(
        message="boom",
        response=MagicMock(status_code=500, headers={}),
        body=None,
    )
    with pytest.raises(LLMError) as ei:
        _raise_groq(err)
    assert ei.value.retryable is True


def _raise_gemini(exc):
    import groq as groq_sdk
    with patch("app.pipelines.llm_client.Groq") as mock_groq, \
         patch("app.pipelines.llm_client.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.side_effect = exc
        # make groq also fail so fallback chain exhausts
        mock_groq.return_value.chat.completions.create.side_effect = groq_sdk.RateLimitError(
            message="fallback also limited",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        )
        LLMClient().complete(task="pyq", user="u")


def test_gemini_429_maps_retryable():
    from google.genai import errors
    err = errors.ClientError(code=429, response_json={"message": "RESOURCE_EXHAUSTED"})
    with pytest.raises(LLMError) as ei:
        _raise_gemini(err)
    assert ei.value.retryable is True
    assert ei.value.provider == "gemini"
    assert ei.value.retry_after is not None


def test_gemini_400_maps_fatal():
    from google.genai import errors
    err = errors.ClientError(code=400, response_json={"message": "bad"})
    with pytest.raises(LLMError) as ei:
        _raise_gemini(err)
    assert ei.value.retryable is False


def test_gemini_5xx_maps_retryable():
    from google.genai import errors
    err = errors.ServerError(code=503, response_json={"message": "overloaded"})
    with pytest.raises(LLMError) as ei:
        _raise_gemini(err)
    assert ei.value.retryable is True


def _groq_400_with(body):
    import groq
    return groq.APIStatusError(
        message="bad",
        response=MagicMock(status_code=400, headers={}, json=lambda: body),
        body=body,
    )


def test_groq_json_validate_failed_is_retryable():
    body = {"error": {"code": "json_validate_failed", "message": "Failed to generate JSON."}}
    with pytest.raises(LLMError) as ei:
        _raise_groq(_groq_400_with(body))
    assert ei.value.retryable is True
    assert ei.value.status == 400


def test_groq_plain_400_stays_fatal():
    body = {"error": {"code": "invalid_api_key", "message": "nope"}}
    with pytest.raises(LLMError) as ei:
        _raise_groq(_groq_400_with(body))
    assert ei.value.retryable is False
