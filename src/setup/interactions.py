import logging

logging.getLogger("google_genai.types").setLevel(logging.ERROR)
logger = logging.getLogger("AgentLogger")

from google.adk.sessions import InMemorySessionService
from google.adk.agents.callback_context import CallbackContext

from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types  # For creating response content
from typing import Optional, Dict, Any  # For type hints

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext


async def call_agent_async(query: str, runner, user_id, session_id) -> str:
    """Sends a query to the agent and prints the final response."""

    # Prepare the user's message in ADK format
    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."  # Default

    # Key Concept: run_async executes the agent logic and yields Events.
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif (
                event.actions and event.actions.escalate
            ):  # Handle potential errors/escalations
                final_response_text = (
                    f"Agent escalated: {event.error_message or 'No specific message.'}"
                )
            # Add more checks here if needed (e.g., specific error codes)
            break  # Stop processing events once the final response is found

    logger.info(
        f"User_ID: {user_id}, Session_ID: {session_id}\nEvent_Author: {event.author}, Event_Type: {type(event).__name__}, Is_Final_Response: {event.is_final_response()}\nEvent_Content: {event.content.parts[0].text}, Query: {query}, Response: {final_response_text}"
    )
    return f"{final_response_text}"


async def update_session_state(
    service: InMemorySessionService, app_name, user_id, session_id, **kwargs
):
    stored_session = service.sessions[app_name][user_id][session_id]
    for key, value in kwargs.items():
        stored_session.state[key] = value
        logging.info(f"Updated state: {key} = {value}")


def block_keyword_guardrail(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Inspects the latest user message for 'BLOCK'. If found, blocks the LLM call
    and returns a predefined LlmResponse. Otherwise, returns None to proceed.
    """
    agent_name = (
        callback_context.agent_name
    )  # Get the name of the agent whose model call is being intercepted
    logging.info(
        f"--- Callback: block_keyword_guardrail running for agent: {agent_name} ---"
    )

    # Extract the text from the latest user message in the request history
    last_user_message_text = ""
    if llm_request.contents:
        # Find the most recent message with role 'user'
        for content in reversed(llm_request.contents):
            if content.role == "user" and content.parts:
                # Assuming text is in the first part for simplicity
                if content.parts[0].text:
                    last_user_message_text = content.parts[0].text
                    break  # Found the last user message text

    logging.info(
        f"--- Callback: Inspecting last user message: '{last_user_message_text[:100]}...' ---"
    )

    # --- Guardrail Logic ---
    keyword_to_block = "BLOCK"

    if keyword_to_block in last_user_message_text.upper():  # Case-insensitive check
        logging.info(
            f"--- Callback: Found '{keyword_to_block}'. Blocking LLM call! ---"
        )

        # Optionally, set a flag in state to record the block event
        callback_context.state["guardrail_block_keyword_triggered"] = True
        logging.info(
            f"--- Callback: Set state 'guardrail_block_keyword_triggered': True ---"
        )

        # Construct and return an LlmResponse to stop the flow and send this back instead
        return LlmResponse(
            content=types.Content(
                role="model",  # Mimic a response from the agent's perspective
                parts=[
                    types.Part(
                        text=f"I cannot process this request because it contains the blocked keyword '{keyword_to_block}'."
                    )
                ],
            )
            # Note: You could also set an error_message field here if needed
        )
    else:
        return None  # Returning None signals ADK to continue normally


def block_paris_tool_guardrail(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    Checks if 'get_weather_stateful' is called for 'Paris'.
    If so, blocks the tool execution and returns a specific error dictionary.
    Otherwise, allows the tool call to proceed by returning None.
    """
    tool_name = tool.name
    agent_name = tool_context.agent_name  # Agent attempting the tool call
    logger.info(
        f"--- Callback: block_paris_tool_guardrail running for tool '{tool_name}' in agent '{agent_name}' ---"
    )
    logger.info(f"--- Callback: Inspecting args: {args} ---")

    # --- Guardrail Logic ---
    target_tool_name = "get_weather"
    blocked_city = "paris"

    # Check if it's the correct tool and the city argument matches the blocked city
    if tool_name == target_tool_name:
        city_argument = args.get("city", "")  # Safely get the 'city' argument
        if city_argument and city_argument.lower() == blocked_city:
            logger.info(
                f"--- Callback: Detected blocked city '{city_argument}'. Blocking tool execution! ---"
            )
            # Optionally update state
            tool_context.state["guardrail_tool_block_triggered"] = True
            logging.info(
                f"--- Callback: Set state 'guardrail_tool_block_triggered': True ---"
            )

            # Return a dictionary matching the tool's expected output format for errors
            # This dictionary becomes the tool's result, skipping the actual tool run.
            return {
                "status": "error",
                "error_message": f"Policy restriction: Weather checks for '{city_argument.capitalize()}' are currently disabled by a tool guardrail.",
            }
        else:
            logger.info(
                f"--- Callback: City '{city_argument}' is allowed for tool '{tool_name}'. ---"
            )
    else:
        logger.info(
            f"--- Callback: Tool '{tool_name}' is not the target tool. Allowing. ---"
        )

    # If the checks above didn't return a dictionary, allow the tool to execute
    logger.info(f"--- Callback: Allowing tool '{tool_name}' to proceed. ---")
    return None  # Returning None allows the actual tool function to run
