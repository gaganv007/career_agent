# ingest_data.py

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Import your local files
from database import Base, engine, SessionLocal
from models import Course 

# Load environment variables
load_dotenv() 

# --- Configuration ---
# [PERSONAL INFO] Replace with your actual Spreadsheet ID
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID") 
# [PERSONAL INFO] Replace with your actual Service Account file name
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
# Sheet is Course_Desc, data from A2 to C42
SHEET_RANGE = 'Course_Desc!A2:C43' 

# --- Sheets API Setup ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('sheets', 'v4', credentials=creds)

def read_google_sheet(spreadsheet_id, range_name):
    """Reads data from the specified Google Sheet range."""
    sheet = service.spreadsheets()
    # Note: We read the specified range which includes column headers in row 1
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    
    if not values:
        print('No data found in the specified range.')
        return None
    
    # The first row of the returned range contains headers (A1, B1, C1)
    # If your range is A2:C42, the first element of 'values' is row 2's data, not headers.
    
    # We must adjust the headers based on the column names we know
    headers = ['Course_Number', 'Course_Name', 'Course_Details'] 
    
    # We create a DataFrame using the known headers
    df = pd.DataFrame(values, columns=headers)
    
    # --- NO TYPE CONVERSION NEEDED ---
    # Since your data is all text, we skip numeric/integer conversion.
        
    return df.to_dict('records')

def ingest_data_to_postgres(data: list[dict], db: Session):
    """Inserts data into the PostgreSQL table with debug logging."""
    print(f"Attempting to ingest {len(data)} records...")
    successful_count = 0
    
    for row in data:
        try:
            # --- MAPPING: Sheet Headers (Keys) to Model Attributes (LHS) ---
            course = Course(
                course_number=row['Course_Number'],       
                course_name=row['Course_Name'],
                course_details=row['Course_Details']
            )
            db.add(course)
            successful_count += 1
            
        except Exception as e:
            # Catch and log specific insertion error
            print(f"FAILED TO INSERT ROW: {row}. Error: {e}")
            # Continue to next row
            
    # Commit all successful inserts at once
    try:
        db.commit()
        print(f"Ingestion complete. Successfully saved {successful_count} records to PostgreSQL.")
    except Exception as e:
        db.rollback()
        print(f"FATAL COMMIT ERROR: {e}")
        
    db.close()

if __name__ == "__main__":
    # 1. Ensure tables exist (creates them if they don't, based on models.py)
    Base.metadata.create_all(bind=engine)
    
    # 2. Read data from Google Sheets
    sheet_data = read_google_sheet(SPREADSHEET_ID, SHEET_RANGE)
    
    if sheet_data:
        # 3. Ingest data using a database session
        db = SessionLocal()
        ingest_data_to_postgres(sheet_data, db)