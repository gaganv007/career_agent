import pytest
import time
from dotenv import find_dotenv, load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    env_file = find_dotenv(".env")
    load_dotenv(env_file)


@pytest.fixture(autouse=True)
def slow_down_tests():
    yield
    # Prevent hittinrg rate limits with API
    # Pause for 10 seconds after each test
    time.sleep(10)


def pytest_collection_modifyitems(items):
    """Modify collected test in place to ensure test modules run in a specific order."""
    MODULE_ORDER = ["tests.test_agent"]
    module_mapping = {item: item.module.__name__ for item in items}

    sorted_items = items.copy()
    for module in MODULE_ORDER:
        sorted_items = [it for it in sorted_items if module_mapping[it] != module] + [
            it for it in sorted_items if module_mapping[it] == module
        ]
    items[:] = sorted_items
