import asyncio
from datetime import datetime
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from setup.logger_config import AgentLogger
from setup.interactions import query_agent, update_session_state, update_callback_state
from agents.team import AGENT, SUB_AGENTS

APP_NAME = "BU MET 633 Fall 2025 Term Project"
USER_ID = "test_user_123"
SESSION_ID = f"test_session_001_{datetime.now().strftime('%Y%m%d%H%M%S')}"


def build_session_state(**kwargs):
    state = {}
    for key, value in kwargs.items():
        state[key] = value
    return state


async def run_conversation(
    head_agent=AGENT,
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
    **kwargs,
):

    logger = AgentLogger()
    service = InMemorySessionService()
    state = build_session_state(**kwargs) if kwargs else None

    await service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id, state=state
    )

    head_runner = Runner(
        agent=head_agent,
        app_name=app_name,
        session_service=service,
    )

    print("Chat with the agent (type 'exit' or 'quit' to end)")
    print("-" * 50)

    while True:
        prompt = input("\nYou: ").strip()

        if prompt.lower() in ["exit", "quit"]:
            print("\nGoodbye!")
            break

        if not prompt:
            continue

        response = await query_agent(
            query=prompt,
            runner=head_runner,
            user_id=user_id,
            session_id=session_id,
        )
        print(f"\nAgent: {response}")


if __name__ == "__main__":
    try:
        asyncio.run(run_conversation(user_preference_temperature_unit="Celsius"))
    except Exception as e:
        print(f"An error occurred: {e}")
