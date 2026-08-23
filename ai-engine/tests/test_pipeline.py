import json
import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from app.pipelines.llm_client import LLMClient
from app.pipelines.base_pipeline import execute_chunks, _deduplicate
from app.prompts import INJECTION_GUARD


class MockSchema(BaseModel):
    result: str


def test_deduplicate_removes_duplicates():
    items = [{"question": "What is X?", "answer": "A"}, {"question": "What is X?", "answer": "B"}]
    result = _deduplicate(items, key="question")
    assert len(result) == 1


def test_deduplicate_keeps_unique():
    items = [{"question": "What is X?", "answer": "A"}, {"question": "What is Y?", "answer": "B"}]
    result = _deduplicate(items, key="question")
    assert len(result) == 2


def test_execute_chunks_calls_llm():
    mock_chunks = ["chunk1", "chunk2"]
    with patch("app.pipelines.base_pipeline.llm_client") as mock_client:
        mock_client.complete.return_value = json.dumps({"result": "ok"})
        results = execute_chunks(mock_chunks, task="chunker")
        assert len(results) == 2
        assert mock_client.complete.call_count == 2


def test_llm_client_complete():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "ok"}'))]

    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value = mock_response
        client = LLMClient()
        result = client.complete(task="chunker", user="hello")
        assert result == '{"result": "ok"}'


def test_llm_client_guard_in_system_message():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"ok": true}'))]

    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        client = LLMClient()
        client.complete(task="chunker", user="sensitive text")
        call_args = MockGroq.return_value.chat.completions.create.call_args

        system_msg = call_args[1]["messages"][0]["content"]
        user_msg = call_args[1]["messages"][1]["content"]

        assert "security_policy" in system_msg
        assert "UNTRUSTED INPUT" in system_msg
        assert "<user_document_content>" in user_msg
        assert "sensitive text" in user_msg
        assert "CRITICAL" not in user_msg


def test_llm_client_json_mode():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"key": "value"}'))]

    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        client = LLMClient()
        client.complete(task="chunker", user="test", json_mode=True)
        call_args = MockGroq.return_value.chat.completions.create.call_args
        assert call_args[1]["response_format"] == {"type": "json_object"}


def test_llm_client_no_json_mode():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='plain text'))]

    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        client = LLMClient()
        client.complete(task="chunker", user="test", json_mode=False)
        call_args = MockGroq.return_value.chat.completions.create.call_args
        assert "response_format" not in call_args[1]


def test_execute_chunks_validates_with_schema():
    mock_chunks = ["chunk1"]
    with patch("app.pipelines.base_pipeline.llm_client") as mock_client:
        mock_client.complete.return_value = json.dumps({"result": "ok"})
        results = execute_chunks(mock_chunks, task="chunker", schema=MockSchema)
        assert results == [{"result": "ok"}]


def test_execute_chunks_drops_invalid_json():
    mock_chunks = ["chunk1"]
    with patch("app.pipelines.base_pipeline.llm_client") as mock_client:
        mock_client.complete.return_value = "not valid json {{{"
        results = execute_chunks(mock_chunks, task="chunker")
        assert results == []


def test_execute_chunks_retries_on_failure():
    mock_chunks = ["chunk1"]
    with patch("app.pipelines.base_pipeline.llm_client") as mock_client:
        mock_client.complete.side_effect = [
            Exception("API error"),
            json.dumps({"result": "ok"}),
        ]
        results = execute_chunks(mock_chunks, task="chunker", max_retries=2)
        assert results == [{"result": "ok"}]
        assert mock_client.complete.call_count == 2


def test_execute_chunks_drops_empty_results():
    mock_chunks = ["chunk1", "chunk2"]
    with patch("app.pipelines.base_pipeline.llm_client") as mock_client:
        mock_client.complete.side_effect = [
            json.dumps({"result": "ok"}),
            "bad json",
        ]
        results = execute_chunks(mock_chunks, task="chunker")
        assert len(results) == 1
