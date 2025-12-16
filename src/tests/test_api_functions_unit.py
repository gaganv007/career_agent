# src/tests/test_api_functions_unit.py

import io
import pytest
from starlette.datastructures import UploadFile
from fastapi import HTTPException

from setup import api_functions


def make_upload_file(filename: str, content: str = "dummy text") -> UploadFile:
    """Helper to create an in-memory UploadFile."""
    return UploadFile(filename=filename, file=io.BytesIO(content.encode("utf-8")))


def test_parse_document_accepts_allowed_extension():
    """
    If parse_document is given a file with an allowed extension
    (for example .txt or .pdf depending on your implementation),
    it should NOT raise an exception.
    """
    file = make_upload_file("test_document.txt")  # adjust extension if needed

    result = api_functions.parse_document(file)

    # We don't care about full structure here; just that it succeeds
    assert result is not None


def test_parse_document_rejects_unsupported_extension():
    """
    Files with unsupported extensions (e.g. .exe) should be rejected
    with an HTTPException.
    """
    file = make_upload_file("malware.exe")

    with pytest.raises(HTTPException):
        api_functions.parse_document(file)


# ---------- _parse_text tests ----------


def test_parse_text_invalid_utf8_raises():
    # Invalid UTF-8 bytes → should raise during decode
    bad_bytes = b"\xff\xfe\xfa"

    with pytest.raises(Exception):
        api_functions._parse_text(bad_bytes)


# ---------- _parse_pdf tests (with fakes) ----------


class FakePdfPage:
    def __init__(self, text, should_fail=False):
        self._text = text
        self._should_fail = should_fail

    def extract_text(self):
        if self._should_fail:
            raise RuntimeError("page error")
        return self._text


class FakePdfReader:
    def __init__(self, _file):
        # two pages: one with text, one that fails
        self.pages = [
            FakePdfPage("First page text"),
            FakePdfPage("ignored page", should_fail=True),
        ]


class FakePdfReaderNoText:
    def __init__(self, _file):
        # all pages return empty / whitespace → should trigger ValueError
        self.pages = [FakePdfPage("   "), FakePdfPage("")]


def test_parse_pdf_collects_text_and_ignores_failing_pages(monkeypatch):
    # Monkeypatch PyPDF2.PdfReader used inside api_functions
    monkeypatch.setattr(api_functions.PyPDF2, "PdfReader", FakePdfReader)

    content = b"fake pdf bytes"
    result = api_functions._parse_pdf(content)

    assert "First page text" in result
    # only one non-empty page in our fake reader
    assert result.count("First page text") == 1


def test_parse_pdf_raises_if_no_text(monkeypatch):
    monkeypatch.setattr(api_functions.PyPDF2, "PdfReader", FakePdfReaderNoText)

    with pytest.raises(ValueError) as exc:
        api_functions._parse_pdf(b"fake pdf bytes")

    assert "No text could be extracted from the PDF" in str(exc.value)


# ---------- _parse_docx tests (with fakes) ----------


class FakeParagraph:
    def __init__(self, text):
        self.text = text


class FakeDoc:
    def __init__(self):
        self.paragraphs = [
            FakeParagraph("First paragraph"),
            FakeParagraph(""),  # will be skipped
            FakeParagraph("Second paragraph"),
        ]


class DummyCursorForRun:
    def __init__(self, rows):
        self._rows = rows
        self.executed = []

    def execute(self, query, params=None):
        # record what was executed for assertions
        self.executed.append((query, params))

    def fetchall(self):
        return self._rows


class DummyConnForRun:
    def __init__(self, rows):
        self.rows = rows
        self.last_cursor = None

    def cursor(self):
        self.last_cursor = DummyCursorForRun(self.rows)
        return self.last_cursor


def test_run_sql_query_executes_and_returns_rows():
    rows = [("CS 633", "Networks"), ("CS 520", "Java")]
    conn = DummyConnForRun(rows)

    result = agent_functions.run_sql_query(
        conn,
        "SELECT * FROM courses WHERE dept = %s",
        params=("CS",),
    )

    assert result == rows
    # Make sure execute was actually called with our query & params
    query, params = conn.last_cursor.executed[0]
    assert query.startswith("SELECT")
    assert params == ("CS",)


def fake_docx_document(_file):
    return FakeDoc()


def test_parse_docx_collects_non_empty_paragraphs(monkeypatch):
    # Monkeypatch docx.Document used in api_functions
    monkeypatch.setattr(api_functions.docx, "Document", fake_docx_document)

    result = api_functions._parse_docx(b"fake docx bytes")

    assert "First paragraph" in result
    assert "Second paragraph" in result
    # Ensure paragraphs are joined with newline
    assert "\n" in result


def test_parse_docx_propagates_errors(monkeypatch):
    # Force docx.Document to raise
    def exploding_document(_file):
        raise RuntimeError("docx read error")

    monkeypatch.setattr(api_functions.docx, "Document", exploding_document)

    with pytest.raises(Exception) as exc:
        api_functions._parse_docx(b"whatever")

    assert "docx read error" in str(exc.value)


# ---------- extra coverage for parse_document & _parse_pdf ----------


def test_parse_document_routes_to_pdf(monkeypatch):
    """Ensure parse_document calls _parse_pdf when type is pdf."""
    called = {}

    def fake_parse_pdf(content: bytes) -> str:
        called["called"] = True
        assert content == b"PDF_BYTES"
        return "pdf text"

    monkeypatch.setattr(api_functions, "_parse_pdf", fake_parse_pdf)

    result = api_functions.parse_document(b"PDF_BYTES", "pdf")
    assert result == "pdf text"
    assert called.get("called") is True


def test_parse_document_routes_to_docx(monkeypatch):
    """Ensure parse_document calls _parse_docx when type is docx."""
    called = {}

    def fake_parse_docx(content: bytes) -> str:
        called["called"] = True
        assert content == b"DOCX_BYTES"
        return "docx text"

    monkeypatch.setattr(api_functions, "_parse_docx", fake_parse_docx)

    result = api_functions.parse_document(b"DOCX_BYTES", "docx")
    assert result == "docx text"
    assert called.get("called") is True


def test_parse_pdf_reader_failure(monkeypatch):
    """Hit the outer except in _parse_pdf when PdfReader itself fails."""

    class ExplodingReader:
        def __init__(self, _file):
            raise RuntimeError("reader failed at open")

    # Replace PyPDF2.PdfReader used inside api_functions
    monkeypatch.setattr(api_functions.PyPDF2, "PdfReader", ExplodingReader)

    with pytest.raises(Exception) as exc:
        api_functions._parse_pdf(b"some bytes")

    assert "reader failed at open" in str(exc.value)
