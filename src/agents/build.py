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
    _name: str,
    _model: str,
    _description: str,
    _instruction: list[str],
    **kwargs,
) -> Agent:

    try:
        agent = Agent(
            name=_name,
            model=select_model(_model),
            description=_description,
            instruction=format_instruction(_instruction),
            **kwargs,
        )
        agent.name = _name
        logger.info(f"Agent '{_name}' created")

        return agent
    except Exception as e:
        logger.error(f"Error Creating Agent {_name}: {e}")
        raise e
