# database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Get the URL from your .env file
# This will be None if the .env file is not found or key is missing
DATABASE_URL = os.getenv("DATABASE_URL") 

# Check to prevent the SQLAlchemy ArgumentError
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL not found in .env file. Please check your .env setup.")

# 2. Create the SQLAlchemy Engine
engine = create_engine(DATABASE_URL)

# 3. Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create the Base class for models
Base = declarative_base()

# Dependency function for FastAPI
def get_db():
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()