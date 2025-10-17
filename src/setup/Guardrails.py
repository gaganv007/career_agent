from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

from typing import Optional
from google.genai import types
import logging

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
        self.blocked_words = blocked_words

    def __call__(
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
        logger.info(
            f"--- Callback: block_keyword_guardrail running for agent: {agent_name} ---"
        )

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
                        f"--- Callback: Found '{kw}' in last user message '{last_user_message_text[:100]}...'\nBlocking LLM call! ---"
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


class TokenGuard:
    """
    Guards against queries that would exceed a specified token limit.
    Uses a simple estimation method of ~4 chars per token.
    """

    def __init__(self, max_tokens: int = 125):
        """
        Initialize with maximum allowed tokens.

        Args:
            max_tokens (int): Maximum number of tokens allowed per query
        """
        self.max_tokens = max_tokens
        self.chars_per_token = 4  # Approximate ratio for English text

    def __call__(
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
        logger.info(
            f"--- Callback: token_limit_guardrail running for agent: {agent_name} ---"
        )

        # Get last user message
        last_user_message_text = ""
        if llm_request.contents:
            for content in reversed(llm_request.contents):
                if content.role == "user" and content.parts:
                    if content.parts[0].text:
                        last_user_message_text = content.parts[0].text
                        break

        # Estimate tokens (length / 4 is a rough approximation)
        estimated_tokens = len(last_user_message_text) // self.chars_per_token

        if estimated_tokens > self.max_tokens:
            logger.warning(
                f"Query exceeded token limit: {estimated_tokens} tokens (limit: {self.max_tokens})"
            )
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=f"I cannot process this request as it exceeds the token limit of {self.max_tokens}. Please try a shorter query."
                        )
                    ],
                )
            )

        logger.info(f"Estimated token count: {estimated_tokens}")
        return None
