# src/tests/test_api_endpoints.py

import asyncio
import io
import pytest
from fastapi.testclient import TestClient

import api  # this imports your api.py and its FastAPI app


client = TestClient(api.app)


# ---------- Basic endpoints ----------


def test_root_serves_index_html():
    resp = client.get("/")
    # Just verify the request succeeds
    assert resp.status_code == 200


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


# ---------- /chat endpoint ----------


@pytest.mark.asyncio
async def _fake_query_agent_ok(query, runner, user_id, session_id):
    return "This is a fake successful response."


@pytest.mark.asyncio
async def _fake_query_agent_generic_error(query, runner, user_id, session_id):
    raise RuntimeError("generic failure")


@pytest.mark.asyncio
async def _fake_query_agent_client_error(query, runner, user_id, session_id):
    # We'll monkeypatch api.ClientError to a local class in that test
    raise api.ClientError("client failure")  # will be patched to our fake


class FakeRunner:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def run_async(self, *args, **kwargs):
        # Not used when we mock query_agent, but method must exist
        if False:  # pragma: no cover - never executes
            yield  # keeps this an async generator


class FakeService:
    async def create_session(self, *args, **kwargs):
        return {}  # simple placeholder


def _reset_sessions(monkeypatch):
    # Replace global sessions dict with a fresh one for each test
    monkeypatch.setattr(api, "sessions", {})


def _patch_common_chat_dependencies(monkeypatch):
    """
    Common patches so /chat doesn't touch real Google ADK objects.
    """
    monkeypatch.setattr(api, "Runner", FakeRunner)
    monkeypatch.setattr(api, "service", FakeService())


def test_chat_success(monkeypatch):
    _reset_sessions(monkeypatch)
    _patch_common_chat_dependencies(monkeypatch)

    # Use fake query_agent that returns a normal response
    monkeypatch.setattr(api, "query_agent", _fake_query_agent_ok)

    payload = {
        "user_id": "test_user",
        "message": "Hello agent",
        # session_id omitted so code generates one
    }

    resp = client.post("/chat", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["user_id"] == "test_user"
    assert data["response"] == "This is a fake successful response."
    assert data["session_id"]  # non-empty


def test_chat_client_error_branch(monkeypatch):
    _reset_sessions(monkeypatch)
    _patch_common_chat_dependencies(monkeypatch)

    # Create a fake ClientError type and patch api.ClientError to it
    class FakeClientError(Exception):
        pass

    monkeypatch.setattr(api, "ClientError", FakeClientError)

    async def fake_query_agent(*args, **kwargs):
        raise FakeClientError("LLM issue")

    monkeypatch.setattr(api, "query_agent", fake_query_agent)

    payload = {
        "user_id": "user_ce",
        "message": "trigger client error",
    }

    resp = client.post("/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Should return the fallback subscription error message
    assert "Apologies, but my current subscription access" in data["response"]


def test_chat_generic_exception_branch(monkeypatch):
    _reset_sessions(monkeypatch)
    _patch_common_chat_dependencies(monkeypatch)

    async def fake_query_agent(*args, **kwargs):
        raise RuntimeError("something bad")

    monkeypatch.setattr(api, "query_agent", fake_query_agent)

    payload = {
        "user_id": "user_gen",
        "message": "trigger generic error",
    }

    resp = client.post("/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "I'm sorry, but I'm having trouble processing that request." in data["response"]


# ---------- query_agent function ----------


class FakePart:
    def __init__(self, text):
        self.text = text


class FakeContent:
    def __init__(self, text):
        self.parts = [FakePart(text)]


class FakeEvent:
    def __init__(self, text):
        self.content = FakeContent(text)
        self.actions = None
        self.error_message = None
        self.author = "agent"

    def is_final_response(self):
        return True


class FakeRunnerForQueryAgent:
    async def run_async(self, user_id, session_id, new_message):
        # Simulate a single final event
        yield FakeEvent(f"Final answer for {user_id}/{session_id}")


@pytest.mark.asyncio
async def test_query_agent_returns_final_text():
    runner = FakeRunnerForQueryAgent()
    text = await api.query_agent(
        query="Hello",
        runner=runner,
        user_id="alice",
        session_id="s1",
    )
    assert "Final answer for alice/s1" in text


# ---------- /sessions and /session delete ----------


def test_list_sessions(monkeypatch):
    monkeypatch.setattr(
        api,
        "sessions",
        {"u1_s1": object(), "u2_s2": object()},
    )

    resp = client.get("/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_sessions"] == 2
    assert set(data["sessions"]) == {"u1_s1", "u2_s2"}


def test_delete_session_existing(monkeypatch):
    # Patch service so delete_session doesn't touch real ADK
    monkeypatch.setattr(api, "service", FakeService())
    monkeypatch.setattr(api, "sessions", {"user_session": object()})

    resp = client.delete("/session/user/session")
    assert resp.status_code == 200
    data = resp.json()
    assert "cleared" in data["message"]


def test_delete_session_not_found(monkeypatch):
    monkeypatch.setattr(api, "sessions", {})

    resp = client.delete("/session/user/missing")
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Session not found"


# ---------- /upload-document ----------


def test_upload_document_success(monkeypatch):
    # Make parse_document return known text
    def fake_parse_document(content, doc_type):
        return "Hello from document"

    monkeypatch.setattr(api, "parse_document", fake_parse_document)

    file_content = b"dummy"
    files = {
        "file": ("test.txt", io.BytesIO(file_content), "text/plain"),
    }
    data = {"document_type": "txt"}

    resp = client.post("/upload-document", files=files, data=data)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["character_count"] == len("Hello from document")
    assert data["extracted_text"] == "Hello from document"


def test_upload_document_unsupported_type(monkeypatch):
    # parse_document should never be called
    def fake_parse_document(*args, **kwargs):
        raise AssertionError("parse_document should not be called")

    monkeypatch.setattr(api, "parse_document", fake_parse_document)

    files = {
        "file": ("test.exe", io.BytesIO(b"dummy"), "application/octet-stream"),
    }
    # document_type is unsupported
    data = {"document_type": "exe"}

    resp = client.post("/upload-document", files=files, data=data)
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


def test_upload_document_empty_after_parsing(monkeypatch):
    def fake_parse_document(*args, **kwargs):
        return "   "  # only spaces → treated as empty

    monkeypatch.setattr(api, "parse_document", fake_parse_document)

    files = {
        "file": ("empty.txt", io.BytesIO(b"dummy"), "text/plain"),
    }
    data = {"document_type": "txt"}

    resp = client.post("/upload-document", files=files, data=data)
    assert resp.status_code == 400
    assert "Document appears to be empty" in resp.json()["detail"]


def test_upload_document_internal_error(monkeypatch):
    def fake_parse_document(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(api, "parse_document", fake_parse_document)

    files = {
        "file": ("err.txt", io.BytesIO(b"dummy"), "text/plain"),
    }
    data = {"document_type": "txt"}

    resp = client.post("/upload-document", files=files, data=data)
    assert resp.status_code == 500
    assert "Error processing document" in resp.json()["detail"]