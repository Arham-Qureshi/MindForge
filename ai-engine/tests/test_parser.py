import fitz
import pytest
from app.parsers.pdf_extractor import (
    EncryptedPDFError,
    InsufficientTextError,
    _check_encryption,
    _extract_text,
    _validate_word_count,
    MAX_PAGES,
    MIN_WORDS,
)


def _make_pdf(text: str = "", pages: int = 1, encrypt: bool = False) -> fitz.Document:
    doc = fitz.open()
    for i in range(pages):
        doc.new_page()
        if i == 0 and text:
            doc[-1].insert_text((72, 72), text)
    return doc


def test_check_encryption_passes_on_normal_pdf():
    doc = _make_pdf("hello world")
    _check_encryption(doc)  # should not raise


def test_check_encryption_raises_on_encrypted():
    doc = _make_pdf()
    doc.save("/tmp/test_enc.pdf", encryption=fitz.PDF_ENCRYPT_AES_128, user_pw="secret")
    encrypted = fitz.open("/tmp/test_enc.pdf")
    with pytest.raises(EncryptedPDFError):
        _check_encryption(encrypted)


def test_extract_text_returns_content():
    doc = _make_pdf("Introduction to Algorithms and Data Structures")
    text = _extract_text(doc)
    assert "Introduction" in text


def test_extract_text_truncates_at_max_pages():
    doc = _make_pdf("word " * 20, pages=MAX_PAGES + 5)
    text = _extract_text(doc)
    assert len(text) > 0


def test_validate_word_count_passes():
    text = " ".join(["word"] * MIN_WORDS)
    _validate_word_count(text)  # should not raise


def test_validate_word_count_raises_on_short_text():
    with pytest.raises(InsufficientTextError):
        _validate_word_count("short")


def _make_pdf_bytes(text: str = "", pages: int = 1, encrypt: bool = False) -> bytes:
    doc = fitz.open()
    for i in range(pages):
        doc.new_page()
        if text:
            for y in range(72, 720, 20):
                doc[-1].insert_text((72, y), text)
    if encrypt:
        doc.save("/tmp/test_enc_bytes.pdf", encryption=fitz.PDF_ENCRYPT_AES_128, user_pw="secret")
        doc.close()
        with open("/tmp/test_enc_bytes.pdf", "rb") as f:
            return f.read()
    raw = doc.tobytes()
    doc.close()
    return raw


def test_extract_text_from_pdf_bytes_valid():
    from app.parsers.pdf_extractor import extract_text_from_pdf_bytes
    raw = _make_pdf_bytes("Introduction to Algorithms Analysis and Design patterns")
    result = extract_text_from_pdf_bytes(raw)
    assert "Introduction" in result
    assert len(result.split()) >= MIN_WORDS


def test_extract_text_from_pdf_bytes_encrypted():
    from app.parsers.pdf_extractor import extract_text_from_pdf_bytes
    raw = _make_pdf_bytes("text", encrypt=True)
    with pytest.raises(EncryptedPDFError):
        extract_text_from_pdf_bytes(raw)


def test_extract_text_from_pdf_bytes_insufficient():
    from app.parsers.pdf_extractor import extract_text_from_pdf_bytes
    raw = _make_pdf_bytes("short")
    with pytest.raises(InsufficientTextError):
        extract_text_from_pdf_bytes(raw)


def test_extract_text_from_pdf_bytes_large():
    from app.parsers.pdf_extractor import extract_text_from_pdf_bytes
    raw = _make_pdf_bytes("word " * 20, pages=MAX_PAGES + 10)
    result = extract_text_from_pdf_bytes(raw)
    assert len(result) > 0
