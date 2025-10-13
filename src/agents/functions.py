import logging
import inspect

from setup.agent_logs import *
from typing import Optional  # Make sure to import Optional
from google.adk.tools.tool_context import ToolContext


def get_weather(city: str, tool_context: ToolContext) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    
    logging.info(f"--- Function '{inspect.stack()[0][3]}' called with: '{city}' ---")

    # --- Read preference from state ---
    preferred_unit = tool_context.state.get(
        "user_preference_temperature_unit", "Celsius"
    )  # Default to Celsius
    print(
        f"--- Tool: Reading state 'user_preference_temperature_unit': {preferred_unit} ---"
    )


    city_normalized = city.lower().replace(" ", "")  # Basic normalization

    # Mock weather data (always stored in Celsius internally)
    mock_weather_db = {
        "newyork": {"temp_c": 25, "condition": "sunny"},
        "london": {"temp_c": 15, "condition": "cloudy"},
        "tokyo": {"temp_c": 18, "condition": "light rain"},
    }

    if city_normalized in mock_weather_db:
        data = mock_weather_db[city_normalized]
        temp_c = data["temp_c"]
        condition = data["condition"]

        # Format temperature based on state preference
        if preferred_unit == "Fahrenheit":
            temp_value = (temp_c * 9 / 5) + 32  # Calculate Fahrenheit
            temp_unit = "°F"
        else:  # Default to Celsius
            temp_value = temp_c
            temp_unit = "°C"

        report = f"The weather in {city.capitalize()} is {condition} with a temperature of {temp_value:.0f}{temp_unit}."
        result = {"status": "success", "report": report}
        logging.info(
            f"--- Tool: Generated report in {preferred_unit}. Result: {result} ---"
        )

        # Example of writing back to state (optional for this tool)
        tool_context.state["last_city_checked_stateful"] = city
        logging.info(
            f"--- Tool: Updated state 'last_city_checked_stateful': {city} ---"
        )

        new_log_entry = prepare_entry(data=[{inspect.stack()[0][3]}, str(city), str(result['report'])],
        columns=["Function", "Requested_City", "Result"])
        append_df_to_excel(new_log_entry, sheet_name="Function Log")

        return result
    else:
        # Handle city not found
        error_msg = f"Sorry, I don't have weather information for '{city}'."
        new_log_entry = prepare_entry(data=[{inspect.stack()[0][3]}, str(city), str(error_msg)],
        columns=["Function", "Input", "Result"])
        append_df_to_excel(new_log_entry, sheet_name="Function Log")

        print(f"--- Tool: City '{city}' not found. ---")
        return {"status": "error", "error_message": error_msg}
    
    
def say_hello(name: Optional[str] = None) -> str:
    """Provides a simple greeting. If a name is provided, it will be used.

    Args:
        name (str, optional): The name of the person to greet. Defaults to a generic greeting if not provided.

    Returns:
        str: A friendly greeting message.
    """

    logging.info(f"--- Function '{inspect.stack()[0][3]}' called with: '{name}' ---")

    if name:
        greeting = f"Hello, {name}!"
    else:
        greeting = "Hello there!"

    new_log_entry = prepare_entry(data=[{inspect.stack()[0][3]}, str(name), str(greeting)],
        columns=["Function", "Input", "Result"])
    append_df_to_excel(new_log_entry, sheet_name="Function Log")
    return greeting


def say_goodbye() -> str:
    logging.info(f"--- Function '{inspect.stack()[0][3]}' called ---")
    return "Goodbye! Have a great day."
