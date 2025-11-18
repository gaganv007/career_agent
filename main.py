# main.py

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

# Import your database components and models
from database import get_db, Base, engine 
from models import Course 

# --- 1. Define the API Schema (Pydantic Model) ---
class CourseResponse(BaseModel):
    # These fields MUST match the attribute names in your models.py file
    course_number: str
    course_name: str
    course_details: str
    # Note: 'id' is excluded here, but is used by SQLAlchemy

    class Config:
        # Allows Pydantic to read ORM objects (SQLAlchemy models)
        from_attributes = True

# --- 2. Initialize FastAPI Application ---
app = FastAPI()

# --- 3. Database Setup (Ensure tables exist) ---
Base.metadata.create_all(bind=engine)

# --- 4. Define the Endpoint ---
@app.get("/courses/", response_model=List[CourseResponse])
def read_courses(db: Session = Depends(get_db)):
    """
    Retrieves all courses from the PostgreSQL database.
    """
    # Query the database for all records in the 'courses' table
    courses = db.query(Course).all()
    
    # Returns the list of Course objects, serialized by CourseResponse
    return courses