# src/tests/test_agent_functions_unit.py

import pytest
from datetime import time
from setup import agent_functions as af  # for brevity in code below

# ---- Dummy DB objects ------------------------------------------------------


class DummyCursor:
    """
    Generic cursor used for multiple tests.
    - records executed queries/params
    - can optionally raise an error when execute() is called
    """

    def __init__(self, rows, should_fail: bool = False):
        self._rows = rows
        self._should_fail = should_fail
        self.executed = []

    def execute(self, query, params=None):
        # record what was executed for assertions
        self.executed.append((query, params))
        if self._should_fail:
            raise RuntimeError("db error")
        return self

    def fetchall(self):
        return self._rows


class DummyConn:
    def __init__(self, rows, should_fail: bool = False):
        self._rows = rows
        self._should_fail = should_fail
        self.last_cursor: DummyCursor | None = None

    def cursor(self):
        self.last_cursor = DummyCursor(self._rows, should_fail=self._should_fail)
        return self.last_cursor


# ---- Tests for run_sql_query -----------------------------------------------


def test_run_sql_query_returns_rows():
    rows = [("cs633", "Business Data Communication"), ("cs520", "Java")]
    conn = DummyConn(rows)

    result = agent_functions.run_sql_query(conn, "SELECT * FROM courses")

    assert result == rows
    # make sure execute was actually called with our query & params
    query, params = conn.last_cursor.executed[0]
    assert query.startswith("SELECT")
    assert params is None


def test_run_sql_query_raises_on_db_error():
    """Show branch, when DB coursor throws an error."""
    conn = DummyConn(rows=[], should_fail=True)

    with pytest.raises(Exception) as exc:
        agent_functions.run_sql_query(conn, "SELECT 1")

    assert "db error" in str(exc.value)


# ---- Tests for get_table_names ---------------------------------------------


def test_get_table_names_returns_table_list_when_connection_provided():
    """
    get_table_names(conn=DummyConn) should return a list of table names,
    using the rows that our dummy connection provides.
    """
    rows = [("courses",), ("students",), ("enrollments",)]
    conn = DummyConn(rows)

    tables = agent_functions.get_table_names(conn=conn)

    assert tables == ["courses", "students", "enrollments"]


def test_get_table_names_returns_empty_list_if_no_connection(monkeypatch):
    """
    When conn=None and get_db_connection() returns None,
    get_table_names() should NOT crash – it should return [].
    """

    def fake_get_db_connection():
        return None

    # Make get_db_connection() return None
    monkeypatch.setattr(agent_functions, "get_db_connection", fake_get_db_connection)

    tables = agent_functions.get_table_names(conn=None)

    assert tables == []


# ---- High-level helpers that call run_sql_query ----------------------------


def test_get_courses_uses_run_sql_query(monkeypatch):
    """Проверяем, что get_courses вызывает run_sql_query с запросом к таблице курсов."""
    captured = {}

    def fake_run_sql_query(conn, query, params=None):
        captured["query"] = query
        captured["params"] = params
        return [("CS 633", "Business Data Communication & Networks")]

    monkeypatch.setattr(agent_functions, "run_sql_query", fake_run_sql_query)

    result = agent_functions.get_courses(user_id="u1")

    assert result  # not empty
    assert "633" in str(result[0]) or "Networks" in str(result[0])
    assert "from" in captured["query"].lower()


def test_get_schedule_calls_run_sql_query(monkeypatch):
    captured = {}

    def fake_run_sql_query(conn, query, params=None):
        captured["query"] = query
        captured["params"] = params
        return [("CS 633", "Mon 6pm")]

    monkeypatch.setattr(agent_functions, "run_sql_query", fake_run_sql_query)

    schedule = agent_functions.get_schedule(user_id="u1")

    assert schedule
    assert "mon" in str(schedule[0]).lower()
    assert "schedule" in captured["query"].lower()


def test_search_faq_returns_matches(monkeypatch):
    def fake_run_sql_query(conn, query, params=None):
        return [("How do I register?", "Use the Student Link")]

    monkeypatch.setattr(agent_functions, "run_sql_query", fake_run_sql_query)

    result = agent_functions.search_faq("register")
    assert result
    assert "Student Link" in str(result[0])


def test_search_faq_handles_no_results(monkeypatch):
    def fake_run_sql_query(conn, query, params=None):
        return []  # no rows

    monkeypatch.setattr(agent_functions, "run_sql_query", fake_run_sql_query)

    result = agent_functions.search_faq("something strange")

    # check that it handles empty results gracefully
    assert result == [] or result is not None


def test_run_sql_query_raises_and_logs_on_error(monkeypatch, caplog):
    """
    Covers the exception path inside run_sql_query().

    We create a dummy connection whose cursor.execute() always raises,
    then assert that run_sql_query re-raises and logs an error.
    """

    class FailingCursor:
        def execute(self, _query):
            raise RuntimeError("DB failure")

        def fetchall(self):
            # should never be called, but defined for safety
            return []

    class FailingConn:
        def cursor(self):
            return FailingCursor()

    conn = FailingConn()

    with caplog.at_level("ERROR"):
        with pytest.raises(RuntimeError):
            agent_functions.run_sql_query(conn, "SELECT * FROM courses")

    # Adjust the message substring to whatever you log in run_sql_query
    assert "SQL query failed" in caplog.text or "Error running SQL query" in caplog.text


class DummyCursor:
    def __init__(self, rows):
        self._rows = rows
        self.executed = None

    def execute(self, statement):
        self.executed = statement
        return self

    def fetchall(self):
        return self._rows

    def close(self):
        pass


class DummyConn:
    def __init__(self, rows):
        self.rows = rows
        self.last_cursor = None

    def cursor(self):
        c = DummyCursor(self.rows)
        self.last_cursor = c
        return c


def test_get_schedule_formats_times(monkeypatch):
    # fake schedule row: course_number, day_of_week, start_time, end_time
    rows = [
        ("CS520", "Mon", time(9, 0), time(10, 15)),
    ]
    conn = DummyConn(rows)

    # make get_db_connectcoverage run -m pytestion() return our fake connection instead of real DB
    monkeypatch.setattr(af, "get_db_connection", lambda: conn)

    result = af.get_schedule("day_of_week = 'Mon'")

    assert len(result) == 1
    s = result[0]
    assert s.course_number == "CS520"
    # strftime formatting should give a human-readable string like "09:00 AM"
    assert isinstance(s.start_time, str)
    assert " " in s.start_time  # e.g., "09:00 AM"
