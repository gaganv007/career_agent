import asyncio

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from agents.team import AGENTS

from setup.logger_config import AgentLogger
from setup.interactions import call_agent_async, update_session_state

APP_NAME = "weather_tutorial_agent_team"
USER_ID = "user_1_agent_team"
SESSION_ID = "session_001_agent_team"


def build_session_state(**kwargs):
    state = {}
    for key, value in kwargs.items():
        state[key] = value
    return state


async def run_conversation(
    head_agent=AGENTS["weather_agent"],
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
    **kwargs,
):

    logger = AgentLogger()

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

    query_agent = lambda query: call_agent_async(
        query=prompt,
        runner=head_runner,
        user_id=user_id,
        session_id=session_id,
    )

    prompts = [
        "Howdy! I am Inigo Montoya. You killed my Father. Prepare to Die!!",
        "But first...what is the weather in New York?",
        "What BLOCKs the request for weather in Tokyo",
        "What is the weather in Paris?",
        "What is the weather in London?",
        "Thanks, bye!",
    ]
    for prompt in prompts:
        if "new york" in prompt.lower():
            await update_session_state(
                service,
                app_name,
                user_id,
                session_id,
                user_preference_temperature_unit="Fahrenheit",
            )
        else:
            await update_session_state(
                service,
                app_name,
                user_id,
                session_id,
                user_preference_temperature_unit="Celcius",
            )

        response = await query_agent(prompt)
        print(response)


if __name__ == "__main__":
    try:
        asyncio.run(run_conversation(user_preference_temperature_unit="Celsius"))
    except Exception as e:
        print(f"An error occurred: {e}")
