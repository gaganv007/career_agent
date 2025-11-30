# models.py
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

## API Models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "web_user"
    session_id: Optional[str] = None
    is_document_upload: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str


class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    extracted_text: str
    character_count: int


class CourseResponse(BaseModel):
    # These fields MUST match the attribute names in your models.py file
    course_number: str
    course_name: str
    course_details: str
    # Note: 'id' is excluded here, but is used by SQLAlchemy

    class Config:
        # Allows Pydantic to read ORM objects (SQLAlchemy models)
        from_attributes = True

## Database Models
class Course(Base):
    __tablename__ = "courses" 

    # 1. Primary Key: Auto-incrementing, unique ID
    id = Column(Integer, primary_key=True, index=True) 
    
    # 2. Course Number: Unique and indexed for fast lookups.
    #    Header: Course_Number (Must match in ingest_data.py)
    course_number = Column(String(50), unique=True, index=True) 
    
    # 3. Course Name: Standard text column.
    #    Header: Course_Name
    course_name = Column(String(255))
    
    # 4. Course Details: Use Text for potentially longer descriptions.
    #    Header: Course_Details
    course_details = Column(Text)

