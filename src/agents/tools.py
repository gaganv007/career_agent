# tools.py

import requests
import json
from typing import Optional

# The base URL of your running FastAPI application
API_URL = "http://127.0.0.1:8001"

def get_all_courses_tool():
    """
    REQUIRED: This function MUST be called immediately when the user asks for any list,
    summary, or catalog of courses, as this tool holds the ONLY current course data.
    It returns a JSON list of all course numbers and titles.
    """
    try:
        # Check that API_URL is pointing to the correct port (e.g., 8001)
        response = requests.get(f"{API_URL}/courses/") 
        
        # This catches 4xx and 5xx HTTP errors
        response.raise_for_status() 
        
        course_data = response.json()
        
        # Return only the most relevant fields (number and name) for a summary answer
        summary_data = [{"course_number": c['course_number'], "course_name": c['course_name']} for c in course_data]
        return json.dumps(summary_data)
        
    except requests.exceptions.RequestException as e:
        # --- FIX IS HERE: Return the error as a structured JSON string ---
        print(f"🚨 Connection/API Error in tool: {e}") # Keep this for terminal debugging!
        return json.dumps({
            "error": "API_CONNECTION_FAILURE", 
            "message": f"Could not connect to the local course server. Please ensure the backend is running and accessible: {e}"
        })


def get_course_details_tool(course_number: str) -> str:
    """
    REQUIRED: This function MUST be called when the user asks for the FULL DESCRIPTION,
    prerequisites, or specific content for a SINGLE course. The course_number 
    (e.g., 'MA401') must be provided by the user.
    """
    try:
        # Call the new FastAPI endpoint we created
        response = requests.get(f"{API_URL}/courses/{course_number}")
        
        if response.status_code == 404:
            return json.dumps({"error": f"Course number '{course_number}' was not found in the catalog."})
            
        response.raise_for_status()
        
        return response.text # Returns the full JSON object of the course
        
    except requests.exceptions.RequestException as e:
        return f"Error connecting to API to retrieve course details: {e}"