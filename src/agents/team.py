"""
Module to setup agents with specific functions and constraints.
"""

# pylint: disable=import-error
import logging

# LLM Tools / Functions
from google.adk.tools import AgentTool
from google.adk.agents import SequentialAgent, LoopAgent
from setup.guardrails import QueryGuard, FunctionGuard, TokenGuard, RateLimiter

# Custom Agent Builder
from agents.build import build_agent, setup_content_config

logger = logging.getLogger("AgentLogger")


# --- Guardrail Configurations ---
blocked_words = [
    "classified",
    "confidential",
    "sex",
    "drugs",
    "murder",
    "crime",
    "rape",
    "exploit",
    "slave",
    "update your instructions",
    "change your guidelines",
    "ignore your programming",
    "bypass your restrictions",
]
function_rules = {
    "search_web": {"query": blocked_words},
}
function_guard = FunctionGuard(function_rules)
query_guard = QueryGuard(blocked_words)
token_guard = TokenGuard(max_tokens=200, document_upload_max_tokens=5000)
query_per_min_limit = 10
rate_limiter = RateLimiter(max_requests=query_per_min_limit, time_window=60)

# --- Agent Configuration ---
# Career advice agent
career = build_agent(name="Career_Agent", tools=[])
# Course recommendation agent
course = build_agent(name="Course_Agent", tools=[])
# Schedule planning agent
schedule = build_agent(name="Scheduling_Agent", tools=[])
# CS633 help agent
cs633 = build_agent(name="CS633_Agent", tools=[])

# --- Convert Agents into Tools for Orchestrator ---
agent_tools = []
for agent in [career, course, schedule, cs633]:
    agent_tools.append(AgentTool(agent=agent))

# --- Advisor Agent to Research and Respond to the User ---
advisor = build_agent(
    name="Advisor_Agent",
    tools=agent_tools,
    before_model_callback=[token_guard, query_guard, rate_limiter],
    output_key="final_response",
)

# --- Validator Agent to ensure Advisor's Response is Relevant ---
validator_agent = build_agent(name="Validator_Agent", tools=[])

# --- Primary Agent for User Interactions ---
orchestrator = LoopAgent(
    name="Validation_Sequence",
    description="Orchestrator that verfies the Advisor_Agent's {final_response} is relevant to the user's "
    "query before forwarding the Advisor_Agent's {final_response} to the user.",
    sub_agents=[advisor, validator_agent],
    max_iterations=3,
)
