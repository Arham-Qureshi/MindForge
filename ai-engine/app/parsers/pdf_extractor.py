import fitz

MAX_PAGES = 100
MIN_WORDS = 50


class EncryptedPDFError(Exception):
    """Raised when PDF is password-protected or encrypted."""


class InsufficientTextError(Exception):
    """Raised when extracted text has fewer than MIN_WORDS words."""


def _check_encryption(doc: fitz.Document) -> None:
    if doc.is_encrypted:
        raise EncryptedPDFError("PDF is password-protected or encrypted")


def _extract_text(doc: fitz.Document) -> str:
    pages = doc[:MAX_PAGES]
    return "\n".join(page.get_text() for page in pages)


def _validate_word_count(text: str) -> None:
    if len(text.split()) < MIN_WORDS:
        raise InsufficientTextError(
            f"Extracted only {len(text.split())} words (minimum {MIN_WORDS})"
        )


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        _check_encryption(doc)
        text = _extract_text(doc)
        _validate_word_count(text)
        return text.strip()
    finally:
        doc.close()
