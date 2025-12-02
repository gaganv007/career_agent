# pylint: disable=import-error
import logging
import asyncio
import time

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

from typing import Optional
from google.genai import types
from collections import deque

logger = logging.getLogger("AgentLogger")


class QueryGuard:
    """Guards against queries containing blocked keywords.

    This class implements a content filter that checks user messages against a list
    of blocked words. If a blocked word is found, the query is rejected before reaching
    the LLM.

    Attributes:
        blocked_words (list): List of case-insensitive keywords that will trigger rejection.

    Example:
        ```python
        # Initialize guard with blocked words
        guard = QueryGuard(blocked_words=["classified", "confidential"])

        # Add to agent configuration
        agent = build_agent(
            before_model_callback=guard,
            ...
        )
        ```
    """

    def __init__(self, blocked_words: list = []):
        """Initializes the QueryGuard with a list of blocked words.

        Args:
            blocked_words (list, optional): List of words to block. Defaults to empty list.
        """
        self.name = "QueryGuard"
        self.blocked_words = blocked_words

    async def __call__(
        self, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Inspects the latest user message for blocked keywords.

        Checks the most recent user message in the conversation for any blocked keywords.
        The check is case-insensitive.

        Args:
            callback_context (CallbackContext): Context of the current callback,
                containing agent information.
            llm_request (LlmRequest): The request to be sent to the LLM,
                containing conversation history.

        Returns:
            Optional[LlmResponse]: If a blocked word is found, returns a blocking
                response with an explanation. Otherwise, returns None to allow
                the request to proceed.

        Logs:
            INFO: When guard runs and which agent triggered it
            INFO: When a blocked keyword is found (includes truncated message)
        """
        agent_name = callback_context.agent_name
        logger.info(f"\t🛡️ {agent_name} running Query Guardrail")

        last_user_message_text = ""
        if llm_request.contents:
            for content in reversed(llm_request.contents):
                if content.role == "user" and content.parts:
                    if content.parts[0].text:
                        last_user_message_text = content.parts[0].text
                        break

        if len(self.blocked_words) > 0:
            for kw in self.blocked_words:
                if kw.upper() in last_user_message_text.upper():
                    logger.info(
                        f"'{kw}' in last user message '{last_user_message_text[:100]}...'\nBlocking"
                    )
                    return LlmResponse(
                        content=types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    text=f"I cannot process this request because it contains the blocked keyword '{kw}'."
                                )
                            ],
                        )
                    )
        return None


class TokenGuard:
    """
    Guards against queries that would exceed a specified token limit.
    Uses a simple estimation method of ~4 chars per token.
    Supports dynamic limits based on query source (document upload vs direct user message).
    """

    def __init__(self, max_tokens: int = 200, document_upload_max_tokens: int = 5000):
        """
        Initialize with maximum allowed tokens.

        Args:
            max_tokens (int): Maximum number of tokens for direct user messages. Defaults to 200.
            document_upload_max_tokens (int): Maximum tokens for document uploads. Defaults to 5000.
        """
        self.name = "TokenGuard"
        self.max_tokens = max_tokens
        self.document_upload_max_tokens = document_upload_max_tokens
        self.chars_per_token = 4  # Approximate ratio for English text
        self.is_document_upload = False

    def set_document_mode(self, is_document: bool):
        """
        Set whether the current query is from a document upload.

        Args:
            is_document (bool): True if query stems from document upload, False for direct user input
        """
        self.is_document_upload = is_document

    async def __call__(
        self, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """
        Estimates token count of the latest user message and blocks if it exceeds limit.

        Args:
            callback_context (CallbackContext): Current callback context
            llm_request (LlmRequest): The LLM request to inspect

        Returns:
            Optional[LlmResponse]: Blocking response if token limit exceeded, None otherwise
        """
        agent_name = callback_context.agent_name
        logger.info(f"\t🟡 {agent_name} running Token Limit Guardrail")

        # Get last user message
        last_user_message_text = ""
        if llm_request.contents:
            for content in reversed(llm_request.contents):
                if content.role == "user" and content.parts:
                    if content.parts[0].text:
                        last_user_message_text = content.parts[0].text
                        break

        # Determine which token limit to use
        token_limit = (
            self.document_upload_max_tokens
            if self.is_document_upload
            else self.max_tokens
        )

        # Estimate tokens (length / 4 is a rough approximation)
        estimated_tokens = len(last_user_message_text) // self.chars_per_token

        if estimated_tokens > token_limit:
            logger.warning(
                f"Query exceeded token limit: {estimated_tokens} tokens (limit: {token_limit})"
            )
            query_type = (
                "document upload" if self.is_document_upload else "direct message"
            )
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=f"I cannot process this {query_type} as it exceeds the token limit of {token_limit}. Please try a shorter input."
                        )
                    ],
                )
            )

        logger.info(f"\t🔎 Estimated Tokens: ({estimated_tokens}) (limit: {token_limit})")
        return None


# Rate limiting configuration
class RateLimiter:
    """
    Guards against exceeding a specified rate limit of requests.

    This class implements a rate limiting mechanism that tracks requests within a
    sliding time window. If the rate limit is exceeded, requests are blocked until
    the rate drops below the limit.

    Attributes:
        max_requests (int): Maximum number of requests allowed in the time window
        time_window (int): Time window in seconds
        requests (deque): Queue to track request timestamps
        lock (asyncio.Lock): Lock for thread-safe operations

    Example:
        ```python
        # Initialize limiter with max 10 requests per minute
        limiter = RateLimiter(max_requests=10, time_window=60)

        # Add to agent configuration
        agent = build_agent(
            before_model_callback=limiter,
            ...
        )
        ```
    """

    def __init__(self, max_requests=10, time_window=60):
        """
        Initialize the RateLimiter with request limits and time window.

        Args:
            max_requests (int, optional): Maximum requests allowed. Defaults to 10.
            time_window (int, optional): Time window in seconds. Defaults to 60.
        """
        self.name = "RateLimiter"
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.requests = deque()
        self.lock = asyncio.Lock()

    async def __call__(
        self, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """
        Checks if the current request would exceed the rate limit.

        Args:
            callback_context (CallbackContext): Context of the current callback,
                containing agent information.
            llm_request (LlmRequest): The request to be sent to the LLM.

        Returns:
            Optional[LlmResponse]: If rate limit is exceeded, returns a blocking
                response with wait time information. Otherwise, returns None to
                allow the request to proceed.

        Logs:
            INFO: When guard runs and which agent triggered it
            WARNING: When rate limit is exceeded
        """
        agent_name = callback_context.agent_name
        logger.info(f"\t🤖 {agent_name} running RateLimiter Guardrail")

        async with self.lock:
            now = time.time()
            # Remove old requests outside the time window
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()

            # Check if we can make a new request
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = self.requests[0]
                wait_time = int(self.time_window - (now - oldest_request) + 1)
                logger.warning(
                    f"Rate limit exceeded for agent {agent_name}. Need to wait {wait_time} seconds."
                )
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                text=f"I'm receiving too many requests right now. Please wait {wait_time} seconds before trying again."
                            )
                        ],
                    )
                )
            # Add current request
            self.requests.append(now)
            return None


class FunctionGuard:
    """
    Guards function calls by blocking specified parameter values.

    Example usage:
    guard = FunctionGuard({
        'get_weather': {
            'location': ['Area51', 'North Korea']
        },
        'search_web': {
            'query': ['classified', 'confidential']
        }
    })
    """

    def __init__(self, blocked_params: dict):
        """
        Initialize with a dictionary of functions and their blocked parameters.

        Args:
            blocked_params (dict): Dictionary structure:
                {
                    'function_name': {
                        'parameter_name': [blocked_values],
                    }
                }
        """
        self.name = "FunctionGuard"
        self.blocked_params = blocked_params

    async def __call__(self, function_call: dict) -> bool:
        """
        Check if the function call should be allowed.

        Args:
            function_call (dict): The function call details including name and arguments

        Returns:
            bool: True if call is allowed, False if blocked
        """
        function_name = function_call.get("name")
        arguments = function_call.get("arguments", {})
        logger.info(f"\t🔑 Running Function Guardrail")

        if function_name in self.blocked_params:
            param_rules = self.blocked_params[function_name]

            for param, blocked_values in param_rules.items():
                if param in arguments:
                    param_value = arguments[param]
                    if isinstance(param_value, str) and param_value.lower() in [
                        v.lower() for v in blocked_values
                    ]:
                        logging.warning(
                            f"Blocked function call: {function_name} with {param}={param_value}"
                        )
                        return False

        return True
