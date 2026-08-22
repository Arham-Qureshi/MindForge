import pytest
from app.pipelines.chunker import (
    _structural_split,
    _semantic_split,
    _cosine_distance,
    _estimate_tokens,
    chunk_text,
    MAX_CHUNK_TOKENS,
)
import numpy as np


def test_structural_split_by_heading():
    text = "Module 1: Introduction\nSome content here.\nModule 2: Advanced Topics\nMore content."
    chunks = _structural_split(text)
    assert len(chunks) >= 2
    assert any("Module 1" in c for c in chunks)
    assert any("Module 2" in c for c in chunks)


def test_structural_split_by_newlines():
    text = "First paragraph about algorithms.\n\nSecond paragraph about data structures."
    chunks = _structural_split(text)
    assert len(chunks) == 2


def test_structural_split_no_split_needed():
    text = "Short text with no headings or double newlines."
    chunks = _structural_split(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_structural_split_empty():
    chunks = _structural_split("")
    assert chunks == []


def test_estimate_tokens():
    text = "one two three four five"
    tokens = _estimate_tokens(text)
    assert tokens == pytest.approx(5 * 1.33, rel=0.1)


def test_cosine_distance_identical():
    v = np.array([1.0, 0.0, 0.0])
    assert _cosine_distance(v, v) == pytest.approx(0.0)


def test_cosine_distance_orthogonal():
    v1 = np.array([1.0, 0.0])
    v2 = np.array([0.0, 1.0])
    assert _cosine_distance(v1, v2) == pytest.approx(1.0)


def test_semantic_split_short_text():
    chunks = _semantic_split("Short text.", MAX_CHUNK_TOKENS)
    assert len(chunks) == 1
    assert chunks[0] == "Short text."


def test_semantic_split_returns_list():
    text = "Sentence one. Sentence two. Sentence three. " * 100
    chunks = _semantic_split(text, MAX_CHUNK_TOKENS)
    assert isinstance(chunks, list)
    assert len(chunks) >= 1


def test_chunk_text_returns_list():
    text = "Module 1: Intro\n\n" + "Word " * 200 + "\n\nModule 2: Advanced\n\n" + "Word " * 200
    chunks = chunk_text(text)
    assert isinstance(chunks, list)
    assert len(chunks) >= 2


def test_chunk_text_max_tokens():
    text = "word " * 5000
    chunks = chunk_text(text)
    for chunk in chunks:
        assert _estimate_tokens(chunk) <= MAX_CHUNK_TOKENS + 100
