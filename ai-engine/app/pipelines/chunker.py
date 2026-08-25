import re

import numpy as np
from fastembed import TextEmbedding

from app.pipelines.tokens import count_tokens, CHUNK_TOKEN_BUDGET

HEADING_SPLITTER = re.compile(
    r'\n{2,}|(?=(?:Module|Unit|Chapter|Section)\s+[0-9IVX]+)',
    re.IGNORECASE
)
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
SENTENCE_SPLITTER = re.compile(r'(?<!\w\w\.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+')
FORCE_SPLIT_WORDS = CHUNK_TOKEN_BUDGET // 3

_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _embedding_model


def _cosine_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return 1.0 - (dot / norm) if norm > 0 else 1.0


def _structural_split(text: str) -> list[str]:
    if not text.strip():
        return []
    return [c.strip() for c in HEADING_SPLITTER.split(text) if c.strip()]


def _force_word_split(text: str) -> list[str]:
    words = text.split()
    return [
        " ".join(words[i:i + FORCE_SPLIT_WORDS])
        for i in range(0, len(words), FORCE_SPLIT_WORDS)
    ]


def _pack(units: list[str], breaks: set[int] | None = None) -> list[str]:
    # greedy pack by token budget; `breaks` forces a boundary before that unit index
    chunks, current, current_tokens = [], [], 0
    for i, u in enumerate(units):
        t = count_tokens(u)
        if current and (current_tokens + t > CHUNK_TOKEN_BUDGET or (breaks and i in breaks)):
            chunks.append(" ".join(current))
            current, current_tokens = [u], t
        else:
            current.append(u)
            current_tokens += t
    if current:
        chunks.append(" ".join(current))
    return chunks


def _semantic_split(text: str) -> list[str]:
    if count_tokens(text) <= CHUNK_TOKEN_BUDGET:
        return [text]

    sentences = [s.strip() for s in SENTENCE_SPLITTER.split(text) if s.strip()]
    units: list[str] = []
    forced = False
    for s in sentences:
        if count_tokens(s) <= CHUNK_TOKEN_BUDGET:
            units.append(s)
        else:
            # arbitrary word windows carry no semantic signal; skip embeddings for them
            units.extend(_force_word_split(s))
            forced = True

    if len(units) <= 1:
        return _force_word_split(text)

    if forced:
        return _pack(units)

    embeddings = list(_get_embedding_model().embed(units))
    distances = [
        _cosine_distance(embeddings[i], embeddings[i + 1])
        for i in range(len(embeddings) - 1)
    ]
    threshold = float(np.percentile(distances, 85)) if distances else 0.5
    breaks = {i + 1 for i, d in enumerate(distances) if d > threshold}
    return _pack(units, breaks)


def chunk_text(text: str) -> list[str]:
    blocks = _structural_split(text)
    final = []
    for block in blocks:
        if count_tokens(block) > CHUNK_TOKEN_BUDGET:
            final.extend(_semantic_split(block))
        else:
            final.append(block)
    return final
