"""
Module to define agent-related functions, such as database reads
"""

# pylint: disable=import-error
import os
import logging
from typing import List

import psycopg2
from setup.schemas import CourseResponse, ScheduleResponse

logger = logging.getLogger("AgentLogger")


def get_db_connection():
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    try:
        return psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=5432,
        )
    except:
        return False


def query_database(table_name: str, conditions: str | None):
    """
    Function to query a Postgresql Database

    Args:
        table_name (str): Name of the database to query; parameter get's inserted into the statement string
        conditions (str): the conditions to filter for 'table_name'; parameter get's inserted into the statement string

    Returns:
        the results from the database in json format
    """
    logger.debug(f"--- Database Call to {table_name} ---\nWHERE {conditions}")

    try:
        conn = get_db_connection()
        if conn:
            print("Connection to the PostgreSQL established successfully.")
        else:
            raise Exception("Connection to the PostgreSQL encountered an error.")

        curr = conn.cursor()
        statement = f"SELECT * FROM {table_name}"
        if conditions is not None and len(conditions) > 0:
            statement += f" WHERE {conditions}"
        statement += ";"

        curr.execute(statement)
        data = curr.fetchall()
        curr.close()

        logger.debug(f"--- Database results -> {data}")
        return data
    except Exception as e:
        logger.error(f"Error retrieving courses from database: {e}")
        raise


def get_courses(conditions: str) -> List[CourseResponse]:
    """
    Function to query a Postgresql Database for course information and return as CourseResponse models

    Args:
        conditions (str): the conditions to filter by; should be formatted for use in a postgresql statement

    Returns:
        List[CourseResponse]: list of CourseResponse models containing course information
    """
    logger.debug(f"--- Function Call 'get_courses' ---\nWHERE {conditions}")

    try:
        rows = query_database(table_name="courses", conditions=conditions)

        # Convert raw database rows to CourseResponse model instances
        courses = []
        for row in rows:
            course = CourseResponse(
                course_number=row[0], course_name=row[1], course_details=row[2]
            )
            courses.append(course)

        logger.debug(f"Retrieved {len(courses)} courses from database")
        return courses

    except Exception as e:
        logger.error(f"Error retrieving courses from database: {e}")
        raise


def get_schedule(conditions: str) -> List[ScheduleResponse]:
    """
    Function to query a Postgresql Database for course information

    Args:
        conditions (str): the conditions to filter by; should be formatted for use in a postgresql statement

    Returns:
        List[ScheduleResponse]: list of CourseResponse models containing course information
    """
    logger.debug(f"--- Function Call 'get_schedule' ---\nWHERE {conditions}")

    try:
        rows = query_database(table_name="schedule", conditions=conditions)

        # Convert raw database rows to CourseResponse model instances
        sessions = []
        for row in rows:
            session = ScheduleResponse(
                session_number=row[0], 
                course_number=row[1], 
                day_of_week=row[2],
                location=row[3]
            )
            sessions.append(session)

        logger.debug(f"Retrieved {len(sessions)} class sessions from database")
        return sessions

    except Exception as e:
        logger.error(f"Error retrieving class sessions from database: {e}")
        raise
