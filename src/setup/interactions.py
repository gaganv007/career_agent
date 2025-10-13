import logging
from google.genai import types  # For creating message Content/Parts

logging.getLogger("google_genai.types").setLevel(logging.ERROR)


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

    return f"{final_response_text}"
