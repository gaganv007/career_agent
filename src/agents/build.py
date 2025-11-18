# pylint: disable=import-error
import logging
from google.adk.agents import Agent
from setup.config import MODEL_GEMINI_2_0_FLASH

logger = logging.getLogger("AgentLogger")


def format_instruction(instruction_list: list[str]) -> str:
    return " ".join(instruction_list)


def select_model(model_name: str) -> str:
    if "gemini" in model_name.lower():
        return str(MODEL_GEMINI_2_0_FLASH)
    else:
        raise ValueError(f"Unsupported model: {model_name}")


def build_agent(
    name: str,
    model: str,
    description: str,
    instruction: list[str],
    **kwargs,
) -> Agent:

    try:
        agent = Agent(
            name=name,
            model=select_model(model),
            description=description,
            instruction=format_instruction(instruction),
            **kwargs,
        )
        agent.name = name
        logger.info(f"Agent '{name}' created")

        return agent
    except Exception as e:
        logger.error(f"Error Creating Agent {name}: {e}")
        raise e
