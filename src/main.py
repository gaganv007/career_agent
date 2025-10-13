import asyncio
import logging

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from agents.team import AGENTS
from setup.interactions import call_agent_async

APP_NAME = "weather_tutorial_agent_team"
USER_ID = "user_1_agent_team"
SESSION_ID = "session_001_agent_team"


def build_session_state(**kwargs):
    state = {}
    for key, value in kwargs.items():
        state[key] = value
    return state


async def update_session_state(service: InMemorySessionService, app_name, user_id, session_id, **kwargs):
    stored_session = service.sessions[app_name][user_id][session_id]
    for key, value in kwargs.items():
        stored_session.state[key] = value

async def run_conversation(
    head_agent=AGENTS["weather_agent"],
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
    **kwargs,
):

    service = InMemorySessionService()
    state = build_session_state(**kwargs) if kwargs else None

    # The 'await' keywords INSIDE this function are necessary for async operations.
    # Create the specific session where the conversation will happen
    await service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id, state=state
    )

    head_runner = Runner(
        agent=head_agent,  # The agent we want to run
        app_name=app_name,  # Associates runs with our app
        session_service=service,  # Uses our session manager
    )

    prompts = [
        "Hello there!",
        "What is the weather in New York?",
        "What is the weather in Paris?",
        "What is the weather in London?",
        "Thanks, bye!",
    ]
    for prompt in prompts:
        if "new york" in prompt.lower():
            await update_session_state(service, app_name, user_id, session_id, user_preference_temperature_unit="Fahrenheit")
        else:
            await update_session_state(service, app_name, user_id, session_id, user_preference_temperature_unit="Celcius")

        response = await call_agent_async(
            query=prompt,
            runner=head_runner,
            user_id=user_id,
            session_id=session_id,
        )
        print(response)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    try:
        asyncio.run(run_conversation(user_preference_temperature_unit="Celsius"))
    except Exception as e:
        print(f"An error occurred: {e}")
