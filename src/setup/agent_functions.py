"""
Module to define agent-related functions, such as database reads
"""

# pylint: disable=import-error
import os
import logging
import psycopg2 as psy

from typing import List
from setup.schemas import CourseResponse, ScheduleResponse, FAQResponse


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


def get_table_names(conn=get_db_connection()):
    """Return a list of table names."""
    logger.debug(f"📢 Function call for 'get_table_names'")

    table_names = []
    curr = conn.cursor()
    tables = curr.execute(
        "SELECT table_name FROM information_schema.tables"
        " WHERE table_schema='public' AND table_type='BASE TABLE';"
    )

    for table in tables.fetchall():
        table_names.append(table[0])
    return table_names


def get_column_names(table_name, conn=get_db_connection()):
    """Return a list of column names."""
    logger.debug(f"📢 Function call for 'get_column_names'")

    column_names = []
    curr = conn.cursor()
    columns = curr.execute(
        f"SELECT column_name, data_type FROM information_schema.columns"
        f" WHERE table_name = {table_name};"
    )

    for col in columns.fetchall():
        column_names.append(col[0])
    return column_names


def get_database_info(conn=get_db_connection()):
    """Return a list of dicts containing the table name and columns for each table in the database."""
    table_dicts = []
    for table_name in get_table_names(conn):
        columns_names = get_column_names(conn, table_name)
        table_dicts.append({"table_name": table_name, "column_names": columns_names})
    return table_dicts


def run_sql_query(statement: str) -> List[CourseResponse]:
    """
    Function to query a the 'courses' table for course information and return as Course models
    Information returned includes the course number, course title, and course description.
    Course descriptions can analyzed to determine the key skills learned and developed within the course.

    Args:
        conditions (str): the conditions to filter by; should be formatted for use in a postgresql statement

    Returns:
        List[Course]: list of Course models containing course information
    """
    logger.debug(f"📢 Function call for 'run_sql_query'")
    conn = get_db_connection()
    logger.info("✅ Connection to Cloud SQL Successful")

    try:
        curr = conn.cursor()
        command = statement.split()[0]
        if command.lower() != "select":
            raise ValueError(f"Statement can only be a 'SELECT' statement")

        logger.debug(f"📝 Executing Statement: '{statement}'")
        curr.execute(statement)
        data = curr.fetchall()
        logger.debug(f"ℹ️ Pulled from database: '{str(data)[:100]}...'")
        curr.close()

        results = []
        for row in data:
            results.append(row)

        return results
    except Exception as e:
        logger.error(f"❌ Error Retreiving Courses: {e}")
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
    logger.debug(f"📢 Function call for 'get_courses'")

    conn = get_db_connection()
    logger.info("✅ Connection to Cloud SQL Successful")

    try:
        curr = conn.cursor()

        statement = f"SELECT * FROM courses"
        if conditions is not None and len(conditions) > 0:
            statement += f" WHERE {conditions}"
        statement += ";"

        logger.debug(f"📝 Executing Statement: '{statement}'")
        curr.execute(statement)
        data = curr.fetchall()
        logger.debug(f"ℹ️ Pulled from database: '{str(data)[:100]}...'")
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
        logger.error(f"❌ Error Retreiving Courses: {e}")
        raise


def get_schedule(conditions: str) -> List[ScheduleResponse]:
    """
    Function to query a the 'schedule' table for schedule information and return as ScheduleResponse models

    Args:
        conditions (str): the conditions to filter by; should be formatted for use in a postgresql statement

    Returns:
        List[ScheduleResponse]: list of ScheduleResponse models containing schedule information
    """
    logger.debug(f"📢 Function call for 'get_schedule'")
    conn = get_db_connection()
    logger.info(f"✅ Connection to Cloud SQL Successful")

    try:
        curr = conn.cursor()

        # Create SELECT Statement
        statement = f"SELECT * FROM schedule"
        if conditions is not None and len(conditions) > 0:
            statement += f" WHERE {conditions}"
        statement += ";"

        logger.debug(f"📝 Executing Statement: '{statement}'")
        curr.execute(statement)
        data = curr.fetchall()
        logger.debug(f"ℹ️ Pulled from database: '{str(data)[:100]}...'")
        curr.close()

        # Format and Return Results
        sessions = []
        for row in data:
            session = ScheduleResponse(
                course_number=row[0],
                day_of_week=row[1],
                start_time=row[2].strftime("%I:%M %p"),
                end_time=row[3].strftime("%I:%M %p"),
            )
            sessions.append(session)
        return sessions

    except Exception as e:
        logger.error(f"❌ Error Retrieving Schedule: {e}")
        raise


def search_faq(course_num: str) -> List[FAQResponse]:
    """
    Function to query a the 'schedule' table for schedule information and return as ScheduleResponse models

    Args:
        conditions (str): the conditions to filter by; should be formatted for use in a postgresql statement

    Returns:
        List[ScheduleResponse]: list of ScheduleResponse models containing schedule information
    """
    logger.debug(f"📢 Function call for 'search_faq'")
    conn = get_db_connection()
    logger.info(f"✅ Connection to Cloud SQL Successful")

    try:
        curr = conn.cursor()

        # Create SELECT Statement
        statement = f"SELECT * FROM faq where course_number ilike '%{course_num}%'"

        logger.debug(f"📝 Executing Statement: '{statement}'")
        curr.execute(statement)
        data = curr.fetchall()
        logger.debug(f"ℹ️ Pulled from database: '{str(data)[:100]}...'")
        curr.close()

        # Format and Return Results
        questions = []
        for row in data:
            session = FAQResponse(
                faq_id=row[0],
                question=row[1],
                answer=row[2],
                course_number=row[3],
            )
            questions.append(session)
        return questions

    except Exception as e:
        logger.error(f"❌ Error Retrieving FAQ: {e}")
        raise
