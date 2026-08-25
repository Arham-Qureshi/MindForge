import numpy as np
import pytest
from app.pipelines.chunker import (
    _structural_split,
    _semantic_split,
    _cosine_distance,
    chunk_text,
    CHUNK_TOKEN_BUDGET,
)
from app.pipelines.tokens import count_tokens


def test_structural_split_by_heading():
    text = "Module 1: Introduction\nSome content here.\nModule 2: Advanced Topics\nMore content."
    chunks = _structural_split(text)
    assert len(chunks) >= 2


def test_structural_split_by_newlines():
    text = "First paragraph about algorithms.\n\nSecond paragraph about data structures."
    assert len(_structural_split(text)) == 2


def test_structural_split_no_split_needed():
    text = "Short text."
    assert _structural_split(text) == [text]


def test_structural_split_empty():
    assert _structural_split("") == []


def test_cosine_distance_identical():
    v = np.array([1.0, 0.0, 0.0])
    assert _cosine_distance(v, v) == pytest.approx(0.0)


def test_semantic_split_short_text():
    chunks = _semantic_split("Short text.")
    assert chunks == ["Short text."]


def test_chunk_text_returns_list():
    chunks = chunk_text(
        "Module 1: Intro\n\n" + "Word " * 200 + "\n\nModule 2: Adv\n\n" + "Word " * 200
    )
    assert isinstance(chunks, list)
    assert len(chunks) >= 2


def test_every_chunk_within_budget_normal_text():
    text = "Sentence one is here. Sentence two follows. " * 100
    for chunk in chunk_text(text):
        assert count_tokens(chunk) <= CHUNK_TOKEN_BUDGET


def test_no_path_can_emit_oversize_chunk():
    text = "no periods at all just " + "words " * 20000 + " ending without punctuation"
    for chunk in chunk_text(text):
        assert count_tokens(chunk) <= CHUNK_TOKEN_BUDGET


def test_giant_sentence_force_split():
    giant = "word " * 5000
    for chunk in chunk_text(giant):
        assert count_tokens(chunk) <= CHUNK_TOKEN_BUDGET
