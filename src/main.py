import asyncio
from datetime import datetime
from google.adk.sessions import InMemorySessionService  # pylint: disable=import-error
from google.adk.runners import Runner  # pylint: disable=import-error

from setup.logger_config import AgentLogger
from setup.interactions import query_agent, update_session_state, update_callback_state
from agents.team import orchestrator

start_time = datetime.now()
APP_NAME = "BU MET 633 Fall 2025 Term Project"
USER_ID = f"test_user_{start_time.strftime('%Y%m%d__%H%M%S')}"
SESSION_ID = f"{USER_ID}_{start_time.strftime('%Y%m%d__%H%M%S')}"

async def build_session_state(**kwargs):
    state = {}
    for key, value in kwargs.items():
        state[key] = value
    return state

async def run_conversation(
    head_agent=orchestrator,
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
    **kwargs,
):

    logger = AgentLogger()
    service = InMemorySessionService()
    state = await build_session_state(**kwargs) if kwargs else None

    await service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id, state=state
    )

    head_runner = Runner(
        agent=head_agent,
        app_name=app_name,
        session_service=service,
    )

    #Set words to end session
    exit_words = ['exit', 'quit', 'end session', 'goodbye']
    print("Chat with the agent (type 'exit' or 'quit' to end)")
    print("-" * 50)

    # Add initial greeting from the agent
    greeting = await query_agent(
        query="Please greet the user and briefly explain what you can help with.",
        runner=head_runner,
        user_id=user_id,
        session_id=session_id,
    )
    print(f"\n{head_agent.name.replace("_", " ")}: {greeting}")

    while True:
        if 'last_response' not in locals():
            prompt = input("\nYou: ").strip()
        else:
            if '?' in last_response.strip(): #type: ignore
                prompt = input("\nYou: ").strip()
            else:
                prompt = "Please continue."

        if prompt.lower() in exit_words:
            print("\nGoodbye!")
            break

        if not prompt:
            continue

        session = await service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
        response = await query_agent(
                query=prompt,
                runner=head_runner,
                user_id=user_id,
                session_id=session_id,
        )
        print(f"\n{head_agent.name.replace("_", " ")}: {response}")
        last_response = response


if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")