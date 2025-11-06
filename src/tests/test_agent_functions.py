import pytest
import json
import uuid
from datetime import datetime
from agents.functions import (
    _summarize_course_recommendations,
    _summarize_course_schedule,
    _summarize_skills_for_job,
    _summarize_career_path,
    _create_temporary_user_id,
    _summarize_user_memory,
    _store_user_memory,
    _get_user_memory_for_agent,
    _summarize_web_search
)

def test_summarize_course_recommendations():
    job_title = "Software Engineer"
    courses = [
        {
            "title": "Advanced Python Programming",
            "provider": "BU MET",
            "description": "Learn advanced Python concepts",
            "url": "https://example.com/python",
            "duration": "12 weeks",
            "difficulty": "Intermediate",
            "cost": "$3000",
            "topics": ["Python", "Programming"],
            "relevance_score": 0.95
        }
    ]
    
    result = _summarize_course_recommendations(job_title, courses)
    result_dict = json.loads(result)
    
    assert result_dict["job_title"] == "Software Engineer"
    assert len(result_dict["recommendations"]) == 1
    recommendation = result_dict["recommendations"][0]
    assert recommendation["title"] == "Advanced Python Programming"
    assert recommendation["provider"] == "BU MET"
    assert recommendation["recommended_for"] == "Software Engineer"

def test_summarize_course_recommendations_empty():
    result = _summarize_course_recommendations("Software Engineer", [])
    result_dict = json.loads(result)
    assert result_dict["job_title"] == "Software Engineer"
    assert len(result_dict["recommendations"]) == 0

def test_summarize_course_schedule():
    course = "CS633"
    schedule = [
        {
            "title": "Lecture 1",
            "date": "2025-11-05",
            "start_time": "18:00",
            "end_time": "20:45",
            "instructor": "Dr. Smith",
            "location": "Room 101",
            "url": "https://example.com/lecture1"
        }
    ]
    
    result = _summarize_course_schedule(course, schedule)
    result_dict = json.loads(result)
    
    assert result_dict["course"] == "CS633"
    assert len(result_dict["sessions"]) == 1
    session = result_dict["sessions"][0]
    assert session["session_title"] == "Lecture 1"
    assert session["instructor"] == "Dr. Smith"
    assert session["sequence"] == 0

def test_summarize_course_schedule_empty():
    result = _summarize_course_schedule("CS633", [])
    result_dict = json.loads(result)
    assert result_dict["course"] == "CS633"
    assert len(result_dict["sessions"]) == 0

def test_summarize_skills_for_job():
    job_title = "Data Scientist"
    skills = [
        {
            "name": "Python",
            "category": "technical",
            "proficiency_level": "advanced",
            "importance": "high",
            "years_experience_needed": "3",
            "recommended_training": ["CS521", "CS622"],
            "notes": "Essential skill",
            "relevance_score": 0.9
        }
    ]
    
    result = _summarize_skills_for_job(job_title, skills)
    result_dict = json.loads(result)
    
    assert result_dict["job_title"] == "Data Scientist"
    assert len(result_dict["skills"]) == 1
    skill = result_dict["skills"][0]
    assert skill["name"] == "Python"
    assert skill["category"] == "technical"
    assert skill["proficiency_level"] == "advanced"

def test_summarize_career_path():
    job_title = "Software Architect"
    path = [
        {
            "title": "Junior Developer",
            "description": "Entry level position",
            "expected_duration": "2 years",
            "recommended_skills": ["Python", "Java"],
            "prerequisites": ["BS in Computer Science"],
            "next_positions": ["Senior Developer"]
        }
    ]
    
    result = _summarize_career_path(job_title, path)
    result_dict = json.loads(result)
    
    assert result_dict["job_title"] == "Software Architect"
    assert len(result_dict["career_path"]) == 1
    step = result_dict["career_path"][0]
    assert step["title"] == "Junior Developer"
    assert step["expected_duration"] == "2 years"
    assert step["sequence"] == 0

def test_create_temporary_user_id():
    user_id = _create_temporary_user_id()
    assert user_id.startswith("tmp_")
    assert len(user_id) > 10  # Ensure UUID part is present

def test_summarize_user_memory():
    user_id = "test_user"
    profile = {
        "name": "John Doe",
        "email": "john@example.com",
        "declared_major": "Computer Science",
        "gpa": "3.8",
        "target_titles": ["Software Engineer"],
        "current_courses": ["CS633", "CS521"],
        "skills": ["Python", "Java"]
    }
    
    result = _summarize_user_memory(user_id, profile)
    result_dict = json.loads(result)
    
    assert result_dict["user_id"] == "test_user"
    assert result_dict["personal"]["name"] == "John Doe"
    assert result_dict["academic"]["declared_major"] == "Computer Science"

def test_store_and_get_user_memory():
    user_id = "test_store_user"
    profile = {
        "personal": {
            "name": "Jane Doe",
            "email": "jane@example.com"
        },
        "academic": {
            "declared_major": "Computer Science"
        }
    }
    
    # Test storing
    success = _store_user_memory(user_id, profile)
    assert success is True
    
    # Test retrieving
    result = _get_user_memory_for_agent(user_id)
    result_dict = json.loads(result)
    
    assert result_dict["user_id"] == user_id
    assert result_dict["profile"]["personal"]["name"] == "Jane Doe"
    
    # Test retrieving specific fields
    fields_result = _get_user_memory_for_agent(user_id, ["personal"])
    fields_dict = json.loads(fields_result)
    assert "academic" not in fields_dict["profile"]
    assert fields_dict["profile"]["personal"]["name"] == "Jane Doe"

def test_summarize_web_search():
    query = "python programming"
    results = [
        {
            "title": "Python Tutorial",
            "snippet": "Learn Python programming",
            "url": "https://example.com/python",
            "published": "2025-11-05",
            "relevance_score": 0.95
        }
    ]
    analysis = "Highly relevant results found"
    
    result = _summarize_web_search(query, results, analysis)
    result_dict = json.loads(result)
    
    assert result_dict["query"] == "python programming"
    assert len(result_dict["results"]) == 1
    assert result_dict["analysis"] == "Highly relevant results found"
    search_result = result_dict["results"][0]
    assert search_result["title"] == "Python Tutorial"
    assert search_result["domain"] == "example.com"

def test_summarize_web_search_empty():
    result = _summarize_web_search("empty query", [], None)
    result_dict = json.loads(result)
    assert result_dict["returned_count"] == 0
    assert len(result_dict["results"]) == 0
    assert result_dict["analysis"] is None

if __name__ == "__main__":
    pytest.main(["-v", __file__])