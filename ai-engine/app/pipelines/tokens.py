import threading

_enc = None
_lock = threading.Lock()
SAFETY_MARGIN = 1.05
CHUNK_TOKEN_BUDGET = 2000


def _get_encoding():
    global _enc
    if _enc is None:
        with _lock:
            if _enc is None:
                import tiktoken
                _enc = tiktoken.get_encoding("o200k_base")
    return _enc


def count_tokens(text: str) -> int:
    if not text:
        return 0
    try:
        n = len(_get_encoding().encode(text))
    except Exception:
        n = int(len(text.split()) * 1.5)
    return int(n * SAFETY_MARGIN) + 1
