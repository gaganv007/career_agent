from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_upload_document_unsupported_type():
    """Covers unsupported document_type → triggers 400 error."""
    response = client.post(
        "/upload-document?document_type=exe",
        files={"file": ("virus.exe", b"binarydata")}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_document_empty_after_parse(monkeypatch):
    """Covers post-parse empty text error branch."""

    def fake_parse(*args, **kwargs):
        return ""  # simulate empty extraction

    from api import parse_document
    monkeypatch.setattr("api.parse_document", fake_parse)

    response = client.post(
        "/upload-document?document_type=txt",
        files={"file": ("empty.txt", b"")}
    )

    assert response.status_code == 400
    assert "empty or no text" in response.json()["detail"]