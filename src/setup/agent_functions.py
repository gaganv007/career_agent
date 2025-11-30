"""
Module to define agent-related functions, such as database reads
"""

# pylint: disable=import-error
import os
import requests
import json
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval

logger = logging.getLogger("AgentLogger")

# Dependency function for FastAPI
def get_db_connection():
    DATABASE_URL = os.getenv("DATABASE_URL") 
    if DATABASE_URL is None:
        raise ValueError("DATABASE_URL not found in .env file. Please check your .env setup.")

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_all_courses_tool(API_URL):
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


def get_course_details_tool(API_URL, course_number: str) -> str:
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