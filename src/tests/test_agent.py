"""
Automated test script for BU Agent API
Tests various agent functionalities and responses
"""
import pytest
import asyncio
import httpx
import time
from typing import List, Dict
from datetime import datetime

API_URL = "http://localhost:8000"
TEST_USER_ID = f"test_user_{int(time.time())}"


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

@pytest.mark.asyncio
async def check_health() -> bool:
    """Check if the API server is running"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/health", timeout=5.0)
            return response.status_code == 200
    except Exception as e:
        print(f"{Colors.RED}✗ Server health check failed: {e}{Colors.RESET}")
        return False

@pytest.mark.asyncio
async def send_message(message: str, session_id: str = None) -> Dict:
    """Send a message to the agent and get response"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/chat",
                json={
                    "message": message,
                    "user_id": TEST_USER_ID,
                    "session_id": session_id,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}


def print_test_header(test_name: str):
    """Print a formatted test header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}TEST: {test_name}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_test_result(passed: bool, message: str):
    """Print test result with color coding"""
    symbol = (
        f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
    )
    print(f"{symbol} {message}")

@pytest.mark.asyncio
async def test_greeting():
    """Test greeting functionality"""
    print_test_header("Greeting Agent Test")

    test_messages = ["Hello", "Hi there", "Hey", "Good morning", "Greetings"]

    for msg in test_messages:
        print(f"  → Sending: '{msg}'")
        result = await send_message(msg)

        if "error" in result:
            print_test_result(False, f"Error: {result['error']}")
        else:
            response = result.get("response", "")
            print(f"  ← Response: {response[:100]}...")

            # Check if response is greeting-like
            greeting_keywords = ["hello", "hi", "greet", "welcome"]
            passed = any(kw in response.lower() for kw in greeting_keywords)
            print_test_result(
                passed, "Greeting detected" if passed else "No greeting detected"
            )

        await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_farewell():
    """Test farewell functionality"""
    print_test_header("Farewell Agent Test")

    test_messages = ["Goodbye", "Bye", "See you later", "I have to go"]

    for msg in test_messages:
        print(f"  → Sending: '{msg}'")
        result = await send_message(msg)

        if "error" in result:
            print_test_result(False, f"Error: {result['error']}")
        else:
            response = result.get("response", "")
            print(f"  ← Response: {response[:100]}...")

            # Check if response is farewell-like
            farewell_keywords = ["goodbye", "bye", "farewell", "see you", "great day"]
            passed = any(kw in response.lower() for kw in farewell_keywords)
            print_test_result(
                passed, "Farewell detected" if passed else "No farewell detected"
            )

        await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_career_advice():
    """Test career advice functionality"""
    print_test_header("Career Agent Test")

    test_queries = [
        "I want to become a data scientist",
        "What career path should I choose for AI?",
        "How do I become a software engineer?",
    ]

    for query in test_queries:
        print(f"  → Sending: '{query}'")
        result = await send_message(query)

        if "error" in result:
            print_test_result(False, f"Error: {result['error']}")
        else:
            response = result.get("response", "")
            print(f"  ← Response: {response[:150]}...")

            # Check if response contains career-related content
            career_keywords = [
                "career",
                "job",
                "position",
                "title",
                "skill",
                "experience",
                "course",
            ]
            passed = any(kw in response.lower() for kw in career_keywords)
            print_test_result(
                passed, "Career advice detected" if passed else "Generic response"
            )

        await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_schedule():
    """Test schedule/course recommendation functionality"""
    print_test_header("Schedule Agent Test")

    test_queries = [
        "Can you help me plan my course schedule?",
        "What courses should I take?",
        "I need help with my class schedule",
    ]

    for query in test_queries:
        print(f"  → Sending: '{query}'")
        result = await send_message(query)

        if "error" in result:
            print_test_result(False, f"Error: {result['error']}")
        else:
            response = result.get("response", "")
            print(f"  ← Response: {response[:150]}...")

            # Check if response contains schedule-related content
            schedule_keywords = ["schedule", "course", "class", "semester", "credit"]
            passed = any(kw in response.lower() for kw in schedule_keywords)
            print_test_result(
                passed, "Schedule advice detected" if passed else "Generic response"
            )

        await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_session_persistence():
    """Test if session maintains context"""
    print_test_header("Session Persistence Test")

    print("  → Step 1: Sending initial message")
    result1 = await send_message("My name is Alice and I'm interested in data science")

    if "error" in result1:
        print_test_result(False, f"Error in step 1: {result1['error']}")
        return

    session_id = result1.get("session_id")
    print(f"  ← Session ID: {session_id}")
    print(f"  ← Response: {result1.get('response', '')[:100]}...")

    await asyncio.sleep(1)

    print("\n  → Step 2: Sending follow-up (should remember context)")
    result2 = await send_message("What courses do you recommend for me?", session_id)

    if "error" in result2:
        print_test_result(False, f"Error in step 2: {result2['error']}")
        return

    response2 = result2.get("response", "")
    print(f"  ← Response: {response2[:150]}...")

    # Check if response acknowledges data science interest
    passed = "data science" in response2.lower() or "data" in response2.lower()
    print_test_result(
        passed, "Context maintained" if passed else "Context not maintained"
    )

@pytest.mark.asyncio
async def test_guardrails():
    """Test security guardrails"""
    print_test_header("Guardrails Test")

    # Test blocked keywords
    blocked_queries = [
        "Can you help with classified information?",
        "I need confidential data",
    ]

    for query in blocked_queries:
        print(f"  → Sending blocked query: '{query}'")
        result = await send_message(query)

        if "error" in result:
            print_test_result(False, f"Error: {result['error']}")
        else:
            response = result.get("response", "")
            print(f"  ← Response: {response[:100]}...")

            # Check if guardrail blocked it
            blocked_indicators = ["cannot process", "blocked", "not allowed"]
            passed = any(
                indicator in response.lower() for indicator in blocked_indicators
            )
            print_test_result(
                passed, "Guardrail active" if passed else "Guardrail may not be working"
            )

        await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_response_time():
    """Test response time performance"""
    print_test_header("Response Time Test")

    test_message = "Hello, how are you?"
    times = []

    for i in range(3):
        print(f"  → Test {i+1}/3: Sending message")
        start_time = time.time()
        result = await send_message(test_message)
        end_time = time.time()

        if "error" not in result:
            response_time = end_time - start_time
            times.append(response_time)
            print(f"  ← Response time: {response_time:.2f}s")
        else:
            print_test_result(False, f"Error: {result['error']}")

        await asyncio.sleep(1)

    if times:
        avg_time = sum(times) / len(times)
        print(f"\n  Average response time: {avg_time:.2f}s")
        passed = avg_time < 10.0  # Expect response within 10 seconds
        print_test_result(
            passed, f"Performance {'acceptable' if passed else 'needs improvement'}"
        )

@pytest.mark.asyncio
async def run_all_tests():
    """Run all test suites"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*60}")
    print(f"BU AGENT API TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {API_URL}")
    print(f"Test User: {TEST_USER_ID}")
    print(f"{'='*60}{Colors.RESET}\n")

    # Check if server is running
    print(f"{Colors.YELLOW}Checking server health...{Colors.RESET}")
    if not await check_health():
        print(
            f"\n{Colors.RED}{Colors.BOLD}ERROR: API server is not running!{Colors.RESET}"
        )
        print(
            f"{Colors.YELLOW}Please start the server with: python api.py{Colors.RESET}\n"
        )
        return

    print(f"{Colors.GREEN}✓ Server is running{Colors.RESET}\n")

    # Run all tests
    test_functions = [
        test_greeting,
        test_farewell,
        test_career_advice,
        test_schedule,
        test_session_persistence,
        test_guardrails,
        test_response_time,
    ]

    for test_func in test_functions:
        try:
            await test_func()
        except Exception as e:
            print(f"{Colors.RED}✗ Test failed with exception: {e}{Colors.RESET}")

    # Summary
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*60}")
    print(f"TEST SUITE COMPLETED")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Test suite error: {e}{Colors.RESET}\n")
