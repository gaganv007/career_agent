# pylint: disable=import-error
import logging
import inspect
from typing import Optional

logger = logging.getLogger("AgentLogger")


def say_hello(name: Optional[str] = None) -> str:
    if name:
        greeting = f"Hello, {name}! Pleasure to meet you. \
            What can I assist you with today?"
    else:
        greeting = "Hello there! What can I assist you with today?"

    logger.info(
        f"'{inspect.stack()[0][3]}': Called with: key='{name}',Returning '{greeting}'"
    )
    return greeting


def say_warning() -> str:
    say_warning = "I am a bot that runs entirely in memory, \
                  so this conversation will not be saved once  \
                  you leave or refresh the page."
    logger.info(f"'{inspect.stack()[0][3]}': Called, Returning '{say_warning}'")
    return say_warning


def say_goodbye() -> str:
    say_goodbyeing = "Goodbye! I hope you this conversation was insightful. \
                     If you would like to speak again, you'll need to provide  \
                     me with all your background information again."
    logger.info(f"'{inspect.stack()[0][3]}': Called, Returning '{say_goodbyeing}'")
    return say_goodbyeing