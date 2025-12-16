"""
Module to setup agents with specific functions and constraints.
"""

# pylint: disable=import-error
import logging

# LLM Tools / Functions
from google.adk.tools import AgentTool
from google.adk.agents import LoopAgent, BaseAgent, SequentialAgent


# Custom Agent Builder
from agents.build import build_agent, setup_content_config
from setup.agent_functions import get_courses, get_schedule, run_sql_query, search_faq
from setup.guardrails import QueryGuard, TokenGuard, RateLimiter, FunctionGuard

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

query_guard = QueryGuard(blocked_words)
token_guard = TokenGuard(max_tokens=100, document_upload_max_tokens=3500)
query_per_min_limit = 10
rate_limiter = RateLimiter(max_requests=query_per_min_limit, time_window=60)


# --- Agent Configuration ---
file_name = "agent_instructions.xlsx"

# Career Advice
career = build_agent(
    name="Career_Agent", tools=[], content_config=setup_content_config(temperature=0.1)
)

# Course Recommendations
course = build_agent(
    name="Course_Agent", tools=[get_courses, run_sql_query], file_name=file_name
)

# Schedule Planning
schedule = build_agent(
    name="Scheduling_Agent", tools=[get_schedule, run_sql_query], file_name=file_name
)

# Document Analysis
documents = build_agent(
    name="Document_Agent",
    file_name=file_name,
    content_config=setup_content_config(temperature=0.1),
)


# CS633 Topics
cs633 = build_agent(
    name="CS633_Agent",
    file_name=file_name,
    tools=[search_faq, get_courses],
    content_config=setup_content_config(temperature=0.1),
)

# --- Convert Agents into Tools for Orchestrator ---
agent_tools = []
for agent in [career, course, schedule, cs633, documents]:
    agent_tools.append(AgentTool(agent=agent))

# --- Advisor Agent to Research and Respond to the User ---
advisor = build_agent(
    name="Advisor_Agent",
    tools=agent_tools,
    before_model_callback=[token_guard, query_guard, rate_limiter],
    output_key="current_response",
)

# Validate Responses
validator = build_agent(
    name="Validator_Agent", output_key="pass_or_fail", file_name=file_name
)

# --- Primary Agent for User Interactions ---
orchestrator = SequentialAgent(
    name="Validation_Sequence", sub_agents=[advisor, validator]
)
