"""
Module to setup agents with specific functions and constraints.
"""

# pylint: disable=import-error
import logging
from agents.build import build_agent
from google.adk.agents import ParallelAgent

# LLM Tools / Functions
from setup.web_funcs import (
    _summarize_skills_for_job,
    _summarize_course_schedule,
    _summarize_web_search,
    _summarize_user_memory,
    _summarize_course_recommendations,
)
from setup.util_funcs import (
    _process_uploaded_document,
    _create_temporary_user_id,
    _store_user_memory,
    _get_user_memory_for_agent,
)
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
SUB_AGENTS = {
    "advisor": ParallelAgent(
        name="Advisor_Agent",
        description="Runs multiple research agents in parallel to gather information."
        "Each sub-agent specializes in a different domain relevant to BU MET students."
        "The Advisor Agent coordinates these sub-agents to provide comprehensive answers"
        "to user queries regarding career advise, scheduling, and course recommendations." \
        "You pass this information back to the 'BU_MET_Guide' Agent.",
        sub_agents=[
            build_agent(
                name="Career_Agent",
                tools=[
                    _summarize_web_search,
                    _summarize_skills_for_job,
                    _get_user_memory_for_agent,
                ],
            ),
            build_agent(
                name="Course_Agent",
                tools=[
                    _summarize_web_search,
                    _summarize_course_recommendations,
                    _get_user_memory_for_agent,
                ],
            ),
            build_agent(
                name="Scheduling_Agent",
                tools=[
                    _summarize_web_search,
                    _summarize_course_schedule,
                    _get_user_memory_for_agent,
                ],
            ),
        ],
    ),
    "cs633": build_agent(
        name="CS633_Agent",
        tools=[_summarize_web_search, _get_user_memory_for_agent],
    ),
    "document": build_agent(
        name="Document_Agent",
        tools=[_get_user_memory_for_agent, _process_uploaded_document],
    ),
    "memory": build_agent(
        name="Memory_Agent",
        tools=[_summarize_user_memory, _store_user_memory, _get_user_memory_for_agent],
    ),
}

# Primary Orchestrator
orchestrator = build_agent(
    name="BU_MET_Guide",
    sub_agents=list(SUB_AGENTS.values()),
    before_model_callback=[token_guard, query_guard, rate_limiter],
    tools=[_create_temporary_user_id, _get_user_memory_for_agent],
)
