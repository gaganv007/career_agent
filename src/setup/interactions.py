import logging
from setup.agent_logs import *

logging.getLogger("google_genai.types").setLevel(logging.ERROR)

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types  # For creating response content
from typing import Optional


async def call_agent_async(query: str, runner, user_id, session_id) -> str:
    """Sends a query to the agent and prints the final response."""
    logging.info(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."  # Default

    # Key Concept: run_async executes the agent logic and yields Events.
    # We iterate through events to find the final answer.
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        logging.info(
            f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}"
        )

        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif (
                event.actions and event.actions.escalate
            ):  # Handle potential errors/escalations
                final_response_text = (
                    f"Agent escalated: {event.error_message or 'No specific message.'}"
                )
            # Add more checks here if needed (e.g., specific error codes)
            break  # Stop processing events once the final response is found

        new_log_entry = prepare_entry(data=[user_id, session_id, query, final_response_text, event.author, type(event).__name__, event.is_final_response(), event.content.parts[0].text],
                        columns=["User_ID", "Session_ID", "User_Query", "Response", "Event_Author", "Event_Type", "Is_Final_Response", "Event_Content"])
        append_df_to_excel(new_log_entry, sheet_name="Query Log")
    return f"{final_response_text}"


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
    )  # Log first 100 chars

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
