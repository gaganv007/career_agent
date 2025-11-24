"""
Module to build agents using instructions from an Excel file.
Includes functions to load instructions, format them, and create an agent.
"""

# pylint: disable=import-error
import logging
import pandas as pd
from pathlib import Path
from google.adk.agents import Agent, LlmAgent
from src.agents.config import LLM_MODEL

logger = logging.getLogger("AgentLogger")


def load_excel_instructions(
    excel_file_name: str = "agent_instructions.xlsx",
) -> pd.DataFrame:
    """Load agent instructions from an Excel file."""

    excel_file_path = Path(__file__).parent / excel_file_name
    logger.info(f"Loading instructions from {excel_file_path}")

    try:
        df = pd.read_excel(excel_file_path)
        return df
    except FileNotFoundError:
        error = f"'{excel_file_name}' not found at {excel_file_path}"
        logger.error(error)
        raise Exception(error)


def format_instructions(instruction_list: list[str]) -> str:
    """Format a list of instructions into a single string."""
    return str(" ".join(instruction_list))


def get_instructions(agent_name: str, data_type: str) -> list[str] | str:
    """Retrieve instructions or description for a given agent from the Excel file."""
    try:
        df = load_excel_instructions()
        agent_row = df[df["AgentName"] == agent_name]
        if agent_row.empty:
            raise ValueError(
                f"Agent '{agent_name}' not found in agent_instructions.xlsx"
            )

        return format_instructions(agent_row[data_type.capitalize()].values[0])
    except Exception as e:
        error = f"Error loading instructions for agent '{agent_name}': {e}"
        logger.error(error)
        raise Exception(error)


def build_agent(
    name: str,
    model: str = str(LLM_MODEL),
    **kwargs,
) -> Agent:

    try:
        agent = LlmAgent(
            name=name,
            model=model,
            description=kwargs.pop(
                "description", str(get_instructions(name, "description"))
            ),
            instruction=kwargs.pop(
                "instructions", get_instructions(name, "instructions")
            ),
            **kwargs,
        )
        agent.name = name
        logger.info(f"Agent '{name}' created")

        return agent
    except Exception as e:
        error = f"Error Creating Agent {name}: {e}"
        logger.error(error)
        raise Exception(error)
