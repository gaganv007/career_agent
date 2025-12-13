# src/tests/test_guardrails_unit.py

import pytest
from setup.guardrails import QueryGuard, TokenGuard, RateLimiter, FunctionGuard


# --- Simple helpers / fakes used in tests ---


class FakeCallbackContext:
    def __init__(self, agent_name: str = "TestAgent"):
        self.agent_name = agent_name


class FakePart:
    def __init__(self, text: str):
        self.text = text


class FakeContent:
    def __init__(self, role: str, text: str):
        self.role = role
        self.parts = [FakePart(text)]


class FakeLlmRequest:
    def __init__(self, last_user_message: str):
        # Only the attributes used by the guardrails are needed
        self.contents = [FakeContent(role="user", text=last_user_message)]


# --- QueryGuard tests ---


@pytest.mark.asyncio
async def test_query_guard_blocks_blocked_keyword():
    guard = QueryGuard(blocked_words=["classified"])

    ctx = FakeCallbackContext()
    req = FakeLlmRequest("Can you share classified information?")

    response = await guard(ctx, req)

    # Should return an LlmResponse (not None) with explanation text
    assert response is not None
    text = response.content.parts[0].text
    assert "blocked keyword" in text.lower()
    assert "classified" in text.lower()


@pytest.mark.asyncio
async def test_query_guard_allows_safe_text():
    guard = QueryGuard(blocked_words=["classified"])

    ctx = FakeCallbackContext()
    req = FakeLlmRequest("I want to learn Python programming.")

    response = await guard(ctx, req)

    # Safe message → no blocking
    assert response is None


# --- TokenGuard tests ---


@pytest.mark.asyncio
async def test_token_guard_allows_short_message():
    guard = TokenGuard(max_tokens=10)  # small limit, but message is short

    ctx = FakeCallbackContext()
    req = FakeLlmRequest("short")

    response = await guard(ctx, req)

    # Should NOT block
    assert response is None


@pytest.mark.asyncio
async def test_token_guard_blocks_long_message():
    # Very small limit so it's easy to exceed
    guard = TokenGuard(max_tokens=5)

    ctx = FakeCallbackContext()
    long_text = "x" * 200  # 200 chars → ~50 tokens with chars_per_token=4
    req = FakeLlmRequest(long_text)

    response = await guard(ctx, req)

    # Should block and return an LlmResponse
    assert response is not None
    text = response.content.parts[0].text.lower()
    assert "cannot process" in text
    assert "token limit" in text


# --- RateLimiter tests ---


@pytest.mark.asyncio
async def test_rate_limiter_allows_first_request_and_blocks_second():
    limiter = RateLimiter(max_requests=1, time_window=60)

    ctx = FakeCallbackContext()
    req = FakeLlmRequest("test")

    # First request: allowed
    resp1 = await limiter(ctx, req)
    assert resp1 is None

    # Second immediate request: should be blocked
    resp2 = await limiter(ctx, req)
    assert resp2 is not None
    text = resp2.content.parts[0].text.lower()
    assert "too many requests" in text


# --- FunctionGuard tests ---


@pytest.mark.asyncio
async def test_function_guard_blocks_blocked_param_value():
    guard = FunctionGuard(
        blocked_params={
            "search_web": {
                "query": ["classified", "confidential"],
            }
        }
    )

    function_call = {
        "name": "search_web",
        "arguments": {"query": "classified"},
    }

    allowed = await guard(function_call)

    assert allowed is False


@pytest.mark.asyncio
async def test_function_guard_allows_safe_function_call():
    guard = FunctionGuard(
        blocked_params={
            "search_web": {
                "query": ["classified", "confidential"],
            }
        }
    )

    function_call = {
        "name": "search_web",
        "arguments": {"query": "public article"},
    }

    allowed = await guard(function_call)

    assert allowed is True