"""
Module to define agent-related functions, such as database reads
"""

# pylint: disable=import-error
import os
import logging
import psycopg2 as psy
from typing import List
from setup.schemas import CourseResponse, ScheduleResponse


logger = logging.getLogger("AgentLogger")


def get_db_connection():
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    try:
        return psy.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=5432,
        )
    except Exception as e:
        logger.error(f"❌ Failed to Connect to Cloud SQL: {e}")
        raise


def get_courses(conditions: str) -> List[CourseResponse]:
    """
    Function to query a the 'courses' table for course information and return as Course models
    Information returned includes the course number, course title, and course description.
    Course descriptions can analyzed to determine the key skills learned and developed within the course.

    Args:
        conditions (str): the conditions to filter by; should be formatted for use in a postgresql statement

    Returns:
        List[Course]: list of Course models containing course information
    """
    logger.debug(f"\t📢 Function call for 'get_courses'")

    conn = get_db_connection()
    logger.info("\t✅ Connection to Cloud SQL Successful")

    try:
        curr = conn.cursor()

        statement = f"SELECT * FROM courses"
        if conditions is not None and len(conditions) > 0:
            statement += f" WHERE {conditions}"
        statement += ";"

        logger.debug(f"\t📝 Executing Statement: '{statement}'")
        curr.execute(statement)
        data = curr.fetchall()
        logger.debug(f"\tℹ️ Pulled from database:\n'{data[100:]}...'")
        curr.close()

        # Format and Return Results
        courses = []
        for row in data:
            session = CourseResponse(
                course_number=row[0], course_name=row[1], course_details=row[2]
            )
            courses.append(session)

        return courses
    except Exception as e:
        logger.error(f"\t❌ Error Retreiving Courses: {e}")
        raise


def get_schedule(conditions: str) -> List[ScheduleResponse]:
    """
    Function to query a the 'schedule' table for schedule information and return as CourseResponse models

    Args:
        conditions (str): the conditions to filter by; should be formatted for use in a postgresql statement

    Returns:
        List[ScheduleResponse]: list of CourseResponse models containing course information
    """
    logger.debug(f"\t📢 Function call for 'get_schedule'")
    conn = get_db_connection()
    logger.info(f"\t✅ Connection to Cloud SQL Successful")

    try:
        curr = conn.cursor()

        # Create SELECT Statement
        statement = f"SELECT * FROM schedule"
        if conditions is not None and len(conditions) > 0:
            statement += f" WHERE {conditions}"
        statement += ";"
        
        logger.debug(f"\t📝 Executing Statement: '{statement}'")
        curr.execute(statement)
        data = curr.fetchall()
        logger.debug(f"\tℹ️ Pulled from database:\n'{data[100:]}...'")
        curr.close()

        # Format and Return Results
        sessions = []
        for row in data:
            session = ScheduleResponse(
                session_number=row[0],
                course_number=row[1],
                day_of_week=row[2],
                location=row[3],
            )
            sessions.append(session)
        return sessions

    except Exception as e:
        logger.error(f"\t❌ Error Retrieving Schedule: {e}")
        raise
