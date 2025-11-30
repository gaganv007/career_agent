# agent_runner.py

import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Import your tool functions from the tools.py file
from agents.tools import get_all_courses_tool, get_course_details_tool

SYSTEM_INSTRUCTION = (
    "You are the authoritative Course Catalog Agent. Your task is to provide current and accurate course data. "
    "For any question about specific courses (numbers, names, descriptions, or the catalog), "
    "you MUST call the Course Tool first. "
    "If the tool returns a definitive 'not found' or an error, you may then attempt to answer the user's question "
    "using your general knowledge or politely state the course is unavailable. "
    "You are the Course_Agent."
)
AVAILABLE_TOOLS = [get_all_courses_tool, get_course_details_tool]

# Load environment variables for API Key
load_dotenv() 

# 2. Setup the Gemini Client and Tools
try:
    client = genai.Client()
except Exception as e:
    print(f"Error initializing Gemini client. Is GEMINI_API_KEY set? {e}")
    exit()

# List of all Python functions the model can use
AVAILABLE_TOOLS = [get_all_courses_tool, get_course_details_tool]

def run_agent_conversation(prompt: str):
    """
    Handles the multi-step function calling process with the Gemini model.
    """
    print(f"\nUser: {prompt}")

    # Start a chat session with the tools attached
    tool_config = types.GenerateContentConfig(
        tools=AVAILABLE_TOOLS,
        system_instruction = SYSTEM_INSTRUCTION
    )
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=tool_config
    )
    
    # Send the initial user message
    response = chat.send_message(prompt)
    
    # --- Function Calling Loop ---
    # The loop continues as long as the model keeps requesting function calls
    while response.function_calls:
        
        function_responses = []
        
        # 3. Process all requested function calls from the model's response
        for function_call in response.function_calls:
            
            tool_name = function_call.name
            tool_args = dict(function_call.args)
            
            print(f"\n🤖 Gemini called Tool: {tool_name} with args: {tool_args}")
            
            # 4. Execute the actual Python function (the tool)
            try: # <--- START OF ERROR HANDLING
                if tool_name == "get_all_courses_tool":
                    result = get_all_courses_tool()
                elif tool_name == "get_course_details_tool":
                    # Ensure the course_number argument is passed correctly
                    result = get_course_details_tool(**tool_args)
                else:
                    result = json.dumps({"error": f"Tool '{tool_name}' not found."})
            
            except Exception as e: # <--- CATCH ALL ERRORS
                import traceback
                
                # 🚨 This is the critical line to show the error in the console! 🚨
                print(f"🚨🚨 PYTHON EXCEPTION during tool execution: {e}") 
                traceback.print_exc() 
                
                # Return a failure message to the model
                result = json.dumps({"error": f"Internal tool execution failed: {e}"}) 
            
            print(f"✅ Tool Result: (First 100 chars) {result[:100]}...")

            # 5. Prepare the function response part to send back to the model
            function_responses.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": result},
                )
            )

        # 6. Send the tool results back to the model
        response = chat.send_message(function_responses)
    
    # 7. Print the final, human-readable response from the model
    print(f"\n✨ Final Answer: {response.text}")

if __name__ == "__main__":
    # --- EXECUTION STEPS ---
    
    # 1. Make sure your FastAPI server is running in a separate terminal!
    #    Command: uvicorn main:app --reload

    # 2. Run the ingestion script if you haven't recently
    #    Command: python ingest_data.py
    
    # --- Example Prompts to Test the Tools ---
    
    # A. Tests the `get_all_courses_tool`
    run_agent_conversation("Give me a list of all course numbers available in the catalog.")

    # B. Tests the `get_course_details_tool` with a known course
    #    (You must replace 'CS633' with a real course number from your data!)
    run_agent_conversation("I need the full description for course MA401.") 
    
    # C. Tests the error handling
    run_agent_conversation("What is the description for a course called XYZ999?")