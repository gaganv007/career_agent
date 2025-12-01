"""
Models to seperate out information for the LLMs to recognize
"""

from typing import Optional
from pydantic import BaseModel


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
    course_number: str
    course_name: str
    course_details: str

    class Config:
        from_attributes = True


class ScheduleResponse(BaseModel):
    session_number: str
    course_number: str
    day_of_week: str
    location: str

    class Config:
        from_attributes = True
