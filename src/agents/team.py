"""
Module to setup agents with specific functions and constraints.
"""

# pylint: disable=import-error
import logging
from agents.build import build_agent

# LLM Tools / Functions
from google.adk.tools import AgentTool
from google.adk.agents import SequentialAgent
from setup.guardrails import QueryGuard, FunctionGuard, TokenGuard, RateLimiter

logger = logging.getLogger("AgentLogger")


# --- Guardrail Configurations ---
blocked_words = [
    "classified",
    "confidential",
    "private",
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
token_guard = TokenGuard(max_tokens=125)
query_per_min_limit = 10
rate_limiter = RateLimiter(max_requests=query_per_min_limit, time_window=60)

# --- Agent Configuration ---
career = build_agent(name="Career_Agent", tools=[])
course = build_agent(name="Course_Agent", tools=[])
schedule = build_agent(name="Scheduling_Agent", tools=[])
cs633 = build_agent(name="CS633_Agent", tools=[])

# --- Convert Agents into Tools for Orchestrator ---
agent_tools = []
for agent in [career, course, schedule, cs633]:
    agent_tools.append(AgentTool(agent=agent))

# --- Advisor Agent to select appropriate sub-agent ---
advisor = build_agent(
    name="Advisor_Agent",
    tools=agent_tools,
    before_model_callback=[token_guard, query_guard, rate_limiter],
    output_key="final_response"
)

# --- Validator Agent to ensure response quality ---
validator_agent = build_agent(
    name="Validator_Agent", 
    tools=[]
)

#--- Primary Agent for Uiser Interactions ---
orchestrator = SequentialAgent(
    name="Validation_Sequence",
    description="Orchestrator that verfies {final_response} is relevant before forwarding the response to the user.",
    sub_agents=[advisor, validator_agent]
)
