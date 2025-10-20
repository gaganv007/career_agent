# pylint: disable=import-error
import logging
from agents.build import build_agent
from agents.functions import say_goodbye, say_hello, say_warning
from setup.guardrails import QueryGuard, FunctionGuard, TokenGuard


logger = logging.getLogger("AgentLogger")


def load_instructions():
    # Placeholder for loading instructions from external file or SQL Database
    pass


# Tool Guardrails
function_rules = {
    "get_weather": {
        "location": ["Area51", "Restricted Zone"],
    },
    "search_web": {"query": ["classified", "confidential"]},
}
function_guard = FunctionGuard(function_rules)  # Example
query_guard = QueryGuard(
    blocked_words=["sex", "drugs", "murder", "crime", "rape", "exploit", "slave"]
)
token_guard = TokenGuard(max_tokens=125)

# --- Agent Configuration ---
SUB_AGENTS = {
    "career": build_agent(
        _name="Career_Advisor",
        _model="gemini",
        _description="Provides career advice.",
        _instruction=[
            "You are a career advisor.",
            "When the user asks for career advice, ask what their desired title is."
            "Review web articles that give advice about achieving that tile.",
            "If the tool returns an error, inform the user politely. "
            "If the tool is successful, pass along information.",
        ],
        before_model_callback=[token_guard, query_guard],
    ),
    "schedule": build_agent(
        _name="Scheduling_Assistant",
        _model="gemini",
        _description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
        _instruction=[
            "You are a helpful scheduling assistant.",
            "When the user asks for schedule recommendations,"
            "use the 'load_schedule' function to find class schedule information.",
        ],
        before_model_callback=[token_guard, query_guard],
    ),
    "greeting": build_agent(
        _name="Greeter",
        _model="gemini",
        _description="Handles simple greetings and hellos to start the conversation. "
        "Will lead the user to asking for career advice",
        _instruction=[
            "You are the Greeting Agent.",
            "Your task is to provide a friendly greeting using the 'say_hello' tool"
            "and also use the 'say_warning' tool.",
            "You should get the user to ask for career advice and do nothing else.",
        ],
        tools=[say_hello, say_warning],
        before_model_callback=[token_guard, query_guard],
    )
}

# Primary Orchestrator
orchestrator = build_agent(
    _name="BU_MET_Guide",
    _model="gemini",
    _description="An general agent that guides users to throughout the session.",
    _instruction=[
        "You are a helpful assistant designed for Boston University's Metropolitan College.",
        "You are specialized in helping students that are interested in or enrolled in the \
        Master's of Computer Information Systems program",
        "You're goal is to help students with selecting courses that are relevant to their declared \
        or intended major",
        "Questions not related to the Computer Science department of \
        Boston Unversity's Metropolitan College or advancing a career in a computer science \
        field will be politely refused."
        "You will answer the user to the best your abilities.",
        "You will query Gemini for information",
        "You will not store any private or sensitive information."
        "You will stick",
    ],
    sub_agents=list(SUB_AGENTS.values()),
    before_model_callback=[token_guard, query_guard],
    before_tool_callback=None,
    after_tool_callback=None,
    after_model_callback=None,
)