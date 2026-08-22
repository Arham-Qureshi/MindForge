import json
import pytest
from unittest.mock import patch, MagicMock
from app.pipelines.llm_client import LLMClient
from app.pipelines.base_pipeline import execute_chunks, _deduplicate


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
        results = execute_chunks(mock_chunks, system_prompt="test")
        assert len(results) == 2
        assert mock_client.complete.call_count == 2


def test_llm_client_complete():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "ok"}'))]

    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value = mock_response
        client = LLMClient()
        result = client.complete(system="test", user="hello")
        assert result == '{"result": "ok"}'


def test_llm_client_wraps_prompt():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"ok": true}'))]

    with patch("app.pipelines.llm_client.Groq") as MockGroq:
        client = LLMClient()
        client.complete(system="test", user="sensitive text")
        call_args = MockGroq.return_value.chat.completions.create.call_args
        user_msg = call_args[1]["messages"][1]["content"]
        assert "<user_document_content>" in user_msg
        assert "CRITICAL" in user_msg
        assert "sensitive text" in user_msg
