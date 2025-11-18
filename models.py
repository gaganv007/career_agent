# models.py

from sqlalchemy import Column, Integer, String, Text
from database import Base # Use a dot to hint at local import

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