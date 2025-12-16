from fastapi.testclient import TestClient
from api import app, sessions

client = TestClient(app)


def test_delete_non_existing_session():
    """Covers the 'Session not found' branch in delete_session()."""

    response = client.delete("/session/user_x/no_such_session")
    assert response.status_code == 200
    assert response.json()["message"] == "Session not found"


def test_delete_existing_session(monkeypatch):
    """Covers the existing-session branch that resets the session."""
    
    # Fake a session
    sessions["u1_s1"] = "OLD_SESSION"

    # Mock service.create_session so it doesn’t hit Google ADK
    class FakeSession:
        pass

    async def fake_create_session(*args, **kwargs):
        return FakeSession()

    from api import service
    monkeypatch.setattr(service, "create_session", fake_create_session)

    response = client.delete("/session/u1/s1")

    assert response.status_code == 200
    assert response.json()["message"] == "Session u1_s1 cleared"