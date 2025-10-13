import logging
import agents.functions as functions
from google.adk.agents import Agent
from setup.config import MODEL_GEMINI_2_0_FLASH, MODEL_OPENAI_GPT_4


def format_instruction(instruction_list: list[str]) -> str:
    return " ".join(instruction_list)


def format_tools(tools_list: list[str]):
    tools = []
    for tool in tools_list:
        if hasattr(functions, tool):
            tools.append(getattr(functions, tool))
    return tools


def select_model(model_name: str) -> str:
    if "gemini" in model_name.lower():
        return MODEL_GEMINI_2_0_FLASH
    else:
        return MODEL_OPENAI_GPT_4


def build_agent(
    _name: str,
    _model: str,
    _description: str,
    _instruction: list[str],
    _tools: list,
    _sub_agents: list = [],
    **kwargs,
) -> Agent:

    try:
        agent = Agent(
            name=_name,
            model=select_model(_model),
            description=_description,
            instruction=format_instruction(_instruction),
            tools=_tools,
            sub_agents=_sub_agents,
            **kwargs,
        )
        logging.info(
            f"✅ Agent '{_name}' created with model '{_model}' and tools: {_tools}"
        )
        return agent
    except Exception as e:
        logging.error(f"❌ Error Creating Agent {_name}: {e}")
        raise e
