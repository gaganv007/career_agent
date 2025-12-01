"""
Module to build agents using instructions from an Excel file.
Includes functions to load instructions, format them, and create an agent.
"""

# pylint: disable=import-error
import logging
import pandas as pd
from pathlib import Path

# LLM Tools / Functions
from google.adk.agents import Agent, LlmAgent
from google.genai import types

# Configuration
from agents.config import LLM_MODEL

logger = logging.getLogger("AgentLogger")


def load_excel_instructions(excel_file_name: str) -> pd.DataFrame:
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


def get_instructions(
    agent_name: str, data_type: str, excel_file_name: str = "agent_instructions.xlsx"
) -> list[str] | str:
    """Retrieve instructions or description for a given agent from the Excel file."""
    try:
        df = load_excel_instructions(excel_file_name)
        agent_row = df[df["AgentName"] == agent_name]
        if agent_row.empty:
            raise ValueError(f"Agent '{agent_name}' not found in '{excel_file_name}'")

        return format_instructions(agent_row[data_type.capitalize()].values[0])
    except Exception as e:
        error = f"Error loading instructions for agent '{agent_name}': {e}"
        logger.error(error)
        raise Exception(error)


def setup_content_config(**kwargs) -> types.GenerateContentConfig:
    """Setup content generation to configure response settings for the agent."""
    config = types.GenerateContentConfig(
        temperature=kwargs.pop("temperature", 0.25),
        max_output_tokens=kwargs.pop("max_output_tokens", 750),
        top_p=kwargs.pop("top_p", 0.8),
        top_k=kwargs.pop("top_k", 350),
        safety_settings=kwargs.pop(
            "safety_settings",
            [
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                )
            ],
        ),
        **kwargs,
    )

    return config


def build_agent(
    name: str,
    model: str = str(LLM_MODEL),
    content_config: types.GenerateContentConfig | None = None,
    **kwargs,
) -> Agent:
    """Build and return an agent with specified configurations."""

    excel_file_name = kwargs.pop("excel_file_name", "agent_instructions.xlsx")
    content_config = (
        setup_content_config() if content_config is None else content_config
    )

    try:
        agent = LlmAgent(
            name=name,
            model=model,
            description=kwargs.pop(
                "description",
                str(get_instructions(name, "description", excel_file_name)),
            ),
            instruction=kwargs.pop(
                "instructions", get_instructions(name, "instructions", excel_file_name)
            ),
            generate_content_config=content_config,
            **kwargs,
        )
        agent.name = name
        logger.info(f"Agent '{name}' created")

        return agent
    except Exception as e:
        error = f"Error Creating Agent {name}: {e}"
        logger.error(error)
        raise Exception(error)
