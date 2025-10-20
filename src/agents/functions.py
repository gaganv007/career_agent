import logging

logger = logging.getLogger("AgentLogger")
import inspect

from typing import Optional  # Make sure to import Optional


def say_hello(name: Optional[str] = None) -> str:
    if name:
        greeting = f"Hello, {name}!"
    else:
        greeting = "Hello there!"

    logger.info(
        f"'{inspect.stack()[0][3]}': Called with: key='{name}',Returning '{greeting}'"
    )
    return greeting


def say_goodbye() -> str:
    say_goodbyeing = "Goodbye! Have a great day."
    logger.info(f"'{inspect.stack()[0][3]}': Called, Returning '{say_goodbyeing}'")
    return say_goodbyeing
