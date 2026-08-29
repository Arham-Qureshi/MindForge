import re

import numpy as np

from app.pipelines.tokens import count_tokens

# backward-compatible alias for tests
CHUNK_TOKEN_BUDGET = 2000

HEADING_SPLITTER = re.compile(
    r'\n{2,}|(?=(?:Module|Unit|Chapter|Section)\s+[0-9IVX]+)',
    re.IGNORECASE
)
SENTENCE_SPLITTER = re.compile(r'(?<!\w\w\.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+')

# dynamic chunk sizes based on complexity
CHUNK_BUDGET_SIMPLE = 3000
CHUNK_BUDGET_COMPLEX = 1500
# flashcards-specific tighter budget to keep per-request tokens low enough for 3/min (2→3 goal, minimal shrink)
CHUNK_BUDGET_FLASHCARDS_SIMPLE = 2100
CHUNK_BUDGET_FLASHCARDS_COMPLEX = 1300
OVERLAP_TOKENS = 100

_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from fastembed import TextEmbedding
            _embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except ImportError:
            _embedding_model = None
    return _embedding_model


def _cosine_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return 1.0 - (dot / norm) if norm > 0 else 1.0


def estimate_complexity(text: str) -> float:
    """Returns 0.0 (simple) to 1.0 (complex) based on 4 dimensions."""
    score = 0.0

    # 1. Content density: text-heavy documents
    word_count = len(text.split())
    if word_count > 3000:
        score += 0.25

    # 2. Structural complexity: few headings or many cross-references
    headings = re.findall(r'(?:Module|Unit|Chapter|Section|Part)\s+\d+', text, re.I)
    cross_refs = re.findall(r'(?:see\s+section|refer\s+to|as\s+discussed)', text, re.I)
    if len(headings) < 3 or len(cross_refs) > 5:
        score += 0.25

    # 3. Topic coherence: high vocabulary diversity = multiple topics
    words = text.lower().split()
    unique_ratio = len(set(words)) / max(len(words), 1)
    if unique_ratio > 0.6:
        score += 0.25

    # 4. Visual complexity: tables, equations, code
    tables = len(re.findall(r'\|.*\|.*\|', text))
    equations = len(re.findall(r'[=∑∫∂√π±≈≠≤≥]', text))
    code_blocks = len(re.findall(r'```|def\s+\w+|class\s+\w+', text))
    if tables + equations + code_blocks > 3:
        score += 0.25

    return min(score, 1.0)


def _structural_split(text: str) -> list[str]:
    if not text.strip():
        return []
    return [c.strip() for c in HEADING_SPLITTER.split(text) if c.strip()]


def _force_word_split(text: str, budget: int) -> list[str]:
    force_words = budget // 3
    words = text.split()
    return [
        " ".join(words[i:i + force_words])
        for i in range(0, len(words), force_words)
    ]


def _pack(units: list[str], budget: int, breaks: set[int] | None = None,
          metadata: list[dict] | None = None) -> list[str]:
    """Greedy pack by token budget with optional overlap."""
    chunks, current, current_tokens = [], [], 0
    for i, u in enumerate(units):
        t = count_tokens(u)
        if current and (current_tokens + t > budget or (breaks and i in breaks)):
            chunk_text = " ".join(current)
            chunks.append(chunk_text)
            # overlap: carry last OVERLAP_TOKENS worth of text into next chunk
            if OVERLAP_TOKENS > 0 and current:
                overlap_text = _tail_tokens(current[-1], OVERLAP_TOKENS)
                current = [overlap_text, u] if overlap_text else [u]
                current_tokens = count_tokens(overlap_text) + t
            else:
                current, current_tokens = [u], t
        else:
            current.append(u)
            current_tokens += t
    if current:
        chunks.append(" ".join(current))
    return chunks


def _tail_tokens(text: str, n: int) -> str:
    """Return the last n tokens of text as a string."""
    words = text.split()
    if len(words) <= n:
        return text
    return " ".join(words[-n:])


def _semantic_split(text: str, budget: int = CHUNK_BUDGET_COMPLEX) -> list[str]:
    if count_tokens(text) <= budget:
        return [text]

    sentences = [s.strip() for s in SENTENCE_SPLITTER.split(text) if s.strip()]
    units: list[str] = []
    forced = False
    for s in sentences:
        if count_tokens(s) <= budget:
            units.append(s)
        else:
            units.extend(_force_word_split(s, budget))
            forced = True

    if len(units) <= 1:
        return _force_word_split(text, budget)

    if forced:
        return _pack(units, budget)

    model = _get_embedding_model()
    if model is None:
        # fallback: no embeddings available, use structural packing
        return _pack(units, budget)

    embeddings = list(model.embed(units))
    distances = [
        _cosine_distance(embeddings[i], embeddings[i + 1])
        for i in range(len(embeddings) - 1)
    ]
    threshold = float(np.percentile(distances, 85)) if distances else 0.5
    breaks = {i + 1 for i, d in enumerate(distances) if d > threshold}
    return _pack(units, budget, breaks)


def chunk_text(text: str, task: str | None = None) -> list[str]:
    """Split text into chunks with dynamic sizing based on complexity.

    Flashcard tasks use tighter budgets (2100/1300) to keep per-request
    token count low enough for 3 concurrent within 8000 TPM (2→3).
    """
    complexity = estimate_complexity(text)
    if task and task.startswith("notes"):
        budget = CHUNK_BUDGET_FLASHCARDS_SIMPLE if complexity < 0.4 else CHUNK_BUDGET_FLASHCARDS_COMPLEX
    else:
        budget = CHUNK_BUDGET_SIMPLE if complexity < 0.4 else CHUNK_BUDGET_COMPLEX

    blocks = _structural_split(text)
    final = []
    for block in blocks:
        if count_tokens(block) > budget:
            final.extend(_semantic_split(block, budget))
        else:
            final.append(block)
    return final
