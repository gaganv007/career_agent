import pytest
from setup import agent_functions


def test_get_db_connection_success(monkeypatch):
    """
    Happy path: get_db_connection() reads env vars and calls psy.connect.
    We monkeypatch os.getenv and psy.connect so no real DB is needed.
    """

    captured = {}

    # Fake environment variables
    def fake_getenv(name):
        mapping = {
            "DB_HOST": "localhost",
            "DB_NAME": "met_db",
            "DB_USER": "met_user",
            "DB_PASSWORD": "met_pass",
        }
        return mapping.get(name)

    # Fake psycopg2.connect
    def fake_connect(database, user, password, host, port):
        captured["database"] = database
        captured["user"] = user
        captured["password"] = password
        captured["host"] = host
        captured["port"] = port
        return "FAKE_CONN"

    # Patch inside setup.agent_functions
    monkeypatch.setattr(agent_functions.os, "getenv", fake_getenv)
    monkeypatch.setattr(agent_functions.psy, "connect", fake_connect)

    conn = agent_functions.get_db_connection()

    assert conn == "FAKE_CONN"
    assert captured["database"] == "met_db"
    assert captured["user"] == "met_user"
    assert captured["host"] == "localhost"
    assert captured["port"] == 5432  # fixed in your code


def test_get_db_connection_logs_and_raises_on_error(monkeypatch, caplog):
    """
    Error path: psy.connect raises, function logs an error and re-raises.
    This covers the exception branch and the logger.error call.
    """

    # make psy.connect raise
    def fake_connect(*_args, **_kwargs):
        raise RuntimeError("connection failed")

    monkeypatch.setattr(agent_functions.psy, "connect", fake_connect)

    with caplog.at_level("ERROR"):
        with pytest.raises(RuntimeError):
            agent_functions.get_db_connection()

    # verify that error message from your function was logged
    assert "Failed to Connect to Cloud SQL" in caplog.text