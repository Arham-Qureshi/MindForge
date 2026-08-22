import re

import numpy as np
from fastembed import TextEmbedding

HEADING_SPLITTER = re.compile(
    r'\n{2,}|(?=(?:Module|Unit|Chapter|Section)\s+[0-9IVX]+)',
    re.IGNORECASE
)

MAX_CHUNK_TOKENS = 1500
CHUNK_OVERLAP = 250
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
SENTENCE_SPLITTER = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+')

_embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)


def _estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.33)


def _cosine_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return 1.0 - (dot / norm) if norm > 0 else 1.0


def _structural_split(text: str) -> list[str]:
    if not text.strip():
        return []
    chunks = HEADING_SPLITTER.split(text)
    return [c.strip() for c in chunks if c.strip()]


def _semantic_split(text: str, max_tokens: int = MAX_CHUNK_TOKENS) -> list[str]:
    sentences = [s.strip() for s in SENTENCE_SPLITTER.split(text) if s.strip()]
    if len(sentences) <= 1:
        words = text.split()
        chunk_size = max(1, max_tokens // 2)
        sentences = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        if len(sentences) <= 1:
            return [text]

    embeddings = list(_embedding_model.embed(sentences))
    distances = [
        _cosine_distance(embeddings[i], embeddings[i + 1])
        for i in range(len(embeddings) - 1)
    ]
    threshold = float(np.percentile(distances, 85)) if distances else 0.5

    chunks, current, current_tokens = [], [sentences[0]], _estimate_tokens(sentences[0])

    for i, dist in enumerate(distances):
        next_tokens = _estimate_tokens(sentences[i + 1])
        if dist > threshold or (current_tokens + next_tokens) > max_tokens:
            chunks.append(" ".join(current))
            current, current_tokens = [sentences[i + 1]], next_tokens
        else:
            current.append(sentences[i + 1])
            current_tokens += next_tokens

    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_text(text: str) -> list[str]:
    blocks = _structural_split(text)
    final = []
    for block in blocks:
        if _estimate_tokens(block) > MAX_CHUNK_TOKENS:
            final.extend(_semantic_split(block))
        else:
            final.append(block)
    return final
