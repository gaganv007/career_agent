from agents.build import build_agent
from agents.functions import *

# --- Agent Configuration ---
instructions = {
    "career_agent": [
        "You are a career advisor.",
        "When the user asks for career advice, ask what their desired title is."
        "Review web articles that give advice about achieving that tile.",
        "If the tool returns an error, inform the user politely. "
        "If the tool is successful, pass along information.",
    ],
    "schedule_agent": [
        "You are a helpful scheduling assistant.",
        "When the user asks for schedule recommendations,"
        "use the 'load_schedule' function to find class schedule information.",
    ],
    "greeting_agent": [
        "You are the Greeting Agent. Your ONLY task is to provide a friendly greeting using the 'say_hello' tool. Do nothing else.",
    ],
    "weather_agent": [
        "You are the main Weather Agent. Your job is to provide weather using 'get_weather'.",
        "The tool will format the temperature based on user preference stored in state.",
        "Delegate simple greetings to 'greeting_agent' and farewells to 'farewell_agent'.",
        "Handle only weather requests, greetings, and farewells.",
    ],
    "farewell_agent": [
        "You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message using the 'say_goodbye' tool. Do not perform any other actions."
    ],
}

SUB_AGENTS = {
    "greeting_agent": build_agent(
        _name="greeting_agent_v1",
        _model="gemini",
        _description="Handles simple greetings and hellos using the 'say_hello' tool",
        _instruction=instructions["greeting_agent"],
        _tools=[say_hello],
    ),
    "farewell_agent": build_agent(
        _name="farewell_agent_v1",
        _model="gemini",
        _description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
        _instruction=instructions["farewell_agent"],
        _tools=[say_goodbye],
    ),
}

AGENTS = {
    "career_agent": build_agent(
        _name="career_agent_v1",
        _model="gemini",
        _description="Provides career advice.",
        _instruction=instructions["career_agent"],
        _tools=[],
    ),
    "weather_agent": build_agent(
        _name="weather_agent_v1",
        _model="gemini",
        _description="Main agent: Provides weather (state-aware unit), delegates greetings/farewells, saves report to state.",
        _instruction=instructions["weather_agent"],
        _tools=[get_weather],
        _sub_agents=[SUB_AGENTS["greeting_agent"], SUB_AGENTS["farewell_agent"]],
        output_key="last_weather_report",
    ),
}
