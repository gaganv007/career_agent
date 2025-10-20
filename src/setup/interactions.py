# pylint: disable=import-error
import logging
import inspect
from google.adk.sessions import InMemorySessionService
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from google.adk.tools.tool_context import ToolContext

logging.getLogger("google_genai.types").setLevel(logging.ERROR)
logger = logging.getLogger("AgentLogger")


async def query_agent(query: str, runner, user_id, session_id) -> str:
    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response_text = "Agent did not produce a final response."
    
    print(f"\n🔍 DEBUG: Starting query_agent with message: '{query}'")

    # Key Concept: run_async executes the agent logic and yields Events.
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        print(f"📊 DEBUG: Got event type: {type(event).__name__}")
        
        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            print(f"✅ DEBUG: Got final response event")
            
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
                print(f"📝 DEBUG: Response text: '{final_response_text[:100]}...'")
            elif (
                event.actions and event.actions.escalate
            ):  # Handle potential errors/escalations
                final_response_text = (
                    f"Agent escalated: {event.error_message or 'No specific message.'}"
                )
                print(f"⚠️ DEBUG: Agent escalated: {final_response_text}")
            else:
                print(f"❌ DEBUG: Final response has no content!")
            # Add more checks here if needed (e.g., specific error codes)
            break

    log_line = []
    log_line.append(f"User_ID: {user_id}, Session_ID: {session_id}")
    log_line.append(f"Event_Author: {event.author}, Event_Type: {type(event).__name__}")  # type: ignore
    log_line.append(f"Query: {query}, Response: {final_response_text}")  # type: ignore
    logger.info("%s", [line for line in log_line])
    
    print(f"🔚 DEBUG: Returning response: '{final_response_text[:100]}...'")
    return f"{final_response_text}"


async def update_session_state(
    service: InMemorySessionService, app_name, user_id, session_id, **kwargs
):
    stored_session = service.sessions[app_name][user_id][session_id]
    for key, value in kwargs.items():
        stored_session.state[key] = value
        logger.info(
            f"'{inspect.stack()[0][3]}': Called with: key='{key}', value='{value}', Updated InMemmory state."
        )


async def update_callback_state(callback_context: CallbackContext, **kwargs):
    for key, value in kwargs.items():
        callback_context.state[key] = value
        logger.info(
            f"'{inspect.stack()[0][3]}': Called with: key='{key}', value='{value}', Updated callback state."
        )


async def update_tool_context_state(tool_context: ToolContext, key: str, value) -> str:
    tool_context.state[key] = value
    confirmation_message = f"State updated: {key} = {value}"
    logger.info(
        f"'{inspect.stack()[0][3]}': Called with: key='{key}', value='{value}', Returning '{confirmation_message}'"
    )
    return confirmation_message