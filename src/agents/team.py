import logging

logger = logging.getLogger("AgentLogger")

from agents.build import build_agent
from agents.functions import *
from setup.Guardrails import QueryGuard, FunctionGuard, TokenGuard


def load_instructions():
    # Placeholder for loading instructions from external file or SQL Database
    pass


# --- Agent Configuration ---
SUB_AGENTS = {
    "career": build_agent(
        _name="career_agent_v1",
        _model="gemini",
        _description="Provides career advice.",
        _instruction=[
            "You are a career advisor.",
            "When the user asks for career advice, ask what their desired title is."
            "Review web articles that give advice about achieving that tile.",
            "If the tool returns an error, inform the user politely. "
            "If the tool is successful, pass along information.",
        ],
    ),
    "schedule": build_agent(
        _name="schedcule_agent_v1",
        _model="gemini",
        _description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
        _instruction=[
            "You are a helpful scheduling assistant.",
            "When the user asks for schedule recommendations,"
            "use the 'load_schedule' function to find class schedule information.",
        ],
        tools=[say_goodbye],
    ),
    "greeting": build_agent(
        _name="greeting_agent_v1",
        _model="gemini",
        _description="Handles simple greetings and hellos using the 'say_hello' tool",
        _instruction=[
            "You are the Greeting Agent. Your ONLY task is to provide a friendly greeting using the 'say_hello' tool. Do nothing else."
        ],
    ),
    "farewell": build_agent(
        _name="farewell_agent_v1",
        _model="gemini",
        _description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
        _instruction=[
            "You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message using the 'say_goodbye' tool. Do not perform any other actions."
        ],
    ),
}

# Function Guardrail Example
function_rules = {
    "get_weather": {
        "location": ["Area51", "Restricted Zone"],
    },
    "search_web": {"query": ["classified", "confidential"]},
}
function_guard = FunctionGuard(function_rules)

query_guard = QueryGuard(blocked_words=["classified", "confidential"])
token_guard = TokenGuard(max_tokens=125)

AGENT = build_agent(
    _name="generic_agent_v1",
    _model="gemini",
    _description="A general-purpose assistant to answer basic questions.",
    _instruction=[
        "You are a helpful assistant.",
        "You will answer the user to the best your abilities.",
        "You will query Gemini for information",
        "You will not store any private or sensitive information.",
    ],
    tools=[],
    sub_agents=list(SUB_AGENTS.values()),
    before_model_callback=[query_guard, token_guard],
    before_tool_callback=None,
    after_tool_callback=None,
    after_model_callback=None,
)
