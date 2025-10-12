import asyncio
from setup.session import runner, USER_ID, SESSION_ID, create_session_and_runner
from agents.interactions import call_agent_async

# @title Run the Initial Conversation

# We need an async function to await our interaction helper
async def run_conversation():

    await call_agent_async("What is the weather like in London?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

    await call_agent_async("How about Paris?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID) # Expecting the tool's error message

    await call_agent_async("Tell me the weather in New York",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

# Uncomment the following lines if running as a standard Python script (.py file):
if __name__ == "__main__":
    try:
        asyncio.run(create_session_and_runner())
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")