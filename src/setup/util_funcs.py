"""
Module defining back-end utility functions for managing user memory,
retreiving information, processing documents, and 
extracting structured information.
"""

# pylint: disable=import-error
import io
import logging
import pandas as pd
import pdfplumber
import uuid
import json

from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext
from google.genai import types

from typing import Any, Optional
from datetime import datetime

from setup.web_funcs import _summarize_user_memory

logger = logging.getLogger("AgentLogger")

# simple in-memory store for Memory_Agent (keeps structured user profiles)
_MEMORY_STORE: dict[str, dict[str, Any]] = {}


def _create_temporary_user_id(prefix: str = "tmp") -> str:
    """
    Create a temporary user_id for the session, initialize a minimal memory entry if missing,
    and return the user_id. The ID is stable for the session and suitable to pass to sub-agents.
    """
    user_id = f"{prefix}_{uuid.uuid4().hex}"
    iso_ts = datetime.now().isoformat() + "Z"
    # Initialize minimal profile entry if not present
    if user_id not in _MEMORY_STORE:
        _MEMORY_STORE[user_id] = {
            "personal": {},
            "academic": {},
            "career_goals": {},
            "schedule": {},
            "completed_coursework": [],
            "professional": {},
            "identifiers": {},
            "meta": {"created": iso_ts, "last_updated": iso_ts},
        }
        logger.debug("Created temporary user_id %s with initial memory entry", user_id)

    return user_id


def _store_user_memory(user_id: str, profile: dict[str, Any]) -> bool:
    """
    Merge incoming profile into the in-memory store for user_id.
    Returns True on success.
    """
    try:
        existing = _MEMORY_STORE.get(user_id, {})

        # shallow merge: prefer incoming non-None values, merge dictionaries conservatively
        def merge_dict(dst: dict, src: dict):
            for k, v in (src or {}).items():
                if v is None:
                    continue
                if isinstance(v, dict) and isinstance(dst.get(k), dict):
                    merge_dict(dst[k], v)
                else:
                    dst[k] = v

        # convert summarized profile into structured form before storing
        # if profile already appears to be normalized (has 'personal' or 'academic'), merge directly
        if "personal" in profile or "academic" in profile:
            merged = existing.copy()
            merge_dict(merged, profile)
            _MEMORY_STORE[user_id] = merged
        else:
            # normalize incoming freeform profile then merge
            normalized_json = _summarize_user_memory(user_id, profile)
            normalized = json.loads(normalized_json)
            merged = existing.copy()
            merge_dict(merged, normalized)
            _MEMORY_STORE[user_id] = merged

        logger.debug("Stored user memory for %s: %s", user_id, _MEMORY_STORE[user_id])
        return True
    except Exception as exc:
        logger.exception("Failed to store user memory for %s: %s", user_id, exc)
        return False


def _get_user_memory_for_agent(user_id: str, fields: Optional[list[str]] = None):
    """
    Retrieve the stored memory for user_id. If fields is provided, return only those top-level keys.
    Returns a JSON string.
    """
    try:
        data = _MEMORY_STORE.get(user_id)
        if not data:
            return json.dumps({"user_id": user_id, "profile": None}, ensure_ascii=False)

        if fields:
            subset = {"user_id": user_id, "profile": {k: data.get(k) for k in fields}}
            return json.dumps(subset, ensure_ascii=False)

        logger.debug("Retrieved full user memory for %s: %s", user_id, data)
        return json.dumps({"user_id": user_id, "profile": data}, ensure_ascii=False)
    except Exception as exc:
        logger.exception("Failed to retrieve user memory for %s: %s", user_id, exc)
        return json.dumps({"user_id": user_id, "profile": None}, ensure_ascii=False)


def _process_uploaded_document(
    user_id: str,
    file_name: str,
    file_content: str,
    file_type: str,
    file_size: Optional[int] = None,
) -> dict[str, Any]:
    """
    Scan and extract relevant information from an uploaded file.
    Categorizes data and forwards to memory agent for storage.
    Returns a dict with extraction results.

    Args:
        user_id: User identifier for memory storage
        file_name: Original file name
        file_content: File content as string
        file_type: MIME type (e.g., 'application/pdf', 'text/plain', 'text/csv')
        file_size: Optional file size in bytes

    Returns:
        {
            "status": "success" or "error",
            "file_name": "<name>",
            "file_type": "<type>",
            "extracted_data": {...categorized data...},
            "message": "<details>",
            "memory_updated": <bool>
        }
    """
    try:
        logger.info(
            "Processing uploaded document for user %s: %s (%s)",
            user_id,
            file_name,
            file_type,
        )

        extracted = {
            "academic": {},
            "professional": {},
            "skills": [],
            "certifications": [],
            "raw_text": "",
        }

        # Extract content based on file type
        if file_type == "text/plain":
            extracted["raw_text"] = file_content
            _extract_text_data(file_content, extracted)
        elif file_type == "text/csv":
            extracted["raw_text"] = file_content
            _extract_csv_data(file_content, extracted)
        elif file_type == "application/pdf":
            # For PDF, file_content should already be extracted text
            extracted["raw_text"] = file_content
            _extract_text_data(file_content, extracted)
        elif "text" in file_type:
            extracted["raw_text"] = file_content
            _extract_text_data(file_content, extracted)
        else:
            logger.warning("Unsupported file type for user %s: %s", user_id, file_type)
            return {
                "status": "error",
                "file_name": file_name,
                "file_type": file_type,
                "extracted_data": {},
                "message": f"Unsupported file type: {file_type}",
                "memory_updated": False,
            }

        # Store extracted data in memory
        profile_update = {
            "uploaded_documents": [
                {
                    "file_name": file_name,
                    "file_type": file_type,
                    "file_size": file_size,
                    "processed_at": datetime.now().isoformat() + "Z",
                    "extracted_summary": extracted,
                }
            ]
        }

        # Merge extracted academic/professional data into profile
        if extracted.get("academic"):
            profile_update["academic"] = {
                **_MEMORY_STORE.get(user_id, {}).get("academic", {}),
                **extracted["academic"],
            }
        if extracted.get("professional"):
            profile_update["professional"] = {
                **_MEMORY_STORE.get(user_id, {}).get("professional", {}),
                **extracted["professional"],
            }
        if extracted.get("skills"):
            existing_skills = (
                _MEMORY_STORE.get(user_id, {}).get("professional", {}).get("skills", [])
            )
            profile_update.setdefault("professional", {})["skills"] = (
                existing_skills + extracted["skills"]
            )
        if extracted.get("certifications"):
            profile_update.setdefault("professional", {})["certifications"] = extracted[
                "certifications"
            ]

        memory_stored = _store_user_memory(user_id, profile_update)

        logger.info(
            "Successfully processed document for user %s: %s",
            user_id,
            file_name,
        )
        return {
            "status": "success",
            "file_name": file_name,
            "file_type": file_type,
            "extracted_data": extracted,
            "message": "Document processed and memory updated",
            "memory_updated": memory_stored,
        }
    except Exception as exc:
        logger.exception(
            "Failed to process uploaded document for user %s: %s", user_id, exc
        )
        return {
            "status": "error",
            "file_name": file_name,
            "file_type": file_type,
            "extracted_data": {},
            "message": f"Processing failed: {str(exc)}",
            "memory_updated": False,
        }


def _extract_text_data(content: str, extracted: dict[str, Any]) -> None:
    """
    Extract structured data from plain text content.
    Looks for common keywords and patterns for academic/professional info.
    """
    try:
        text_lower = content.lower()
        lines = content.split("\n")

        # Simple keyword-based extraction
        for line in lines:
            line_lower = line.lower()

            # Academic extraction
            if any(
                kw in line_lower
                for kw in ["gpa", "grade", "major", "degree", "graduation"]
            ):
                extracted["academic"]["source"] = "uploaded document"
                if "gpa" in line_lower:
                    # Try to extract GPA value
                    parts = line.split(":")
                    if len(parts) > 1:
                        extracted["academic"]["gpa"] = parts[-1].strip()
                if "major" in line_lower:
                    parts = line.split(":")
                    if len(parts) > 1:
                        extracted["academic"]["declared_major"] = parts[-1].strip()
                if "graduation" in line_lower:
                    parts = line.split(":")
                    if len(parts) > 1:
                        extracted["academic"]["graduation_year"] = parts[-1].strip()

            # Professional extraction
            if any(
                kw in line_lower
                for kw in ["experience", "employment", "job", "position", "worked"]
            ):
                extracted["professional"]["source"] = "uploaded document"

            # Skills extraction
            if any(
                kw in line_lower for kw in ["skills:", "competencies:", "expertise:"]
            ):
                parts = line.split(":")
                if len(parts) > 1:
                    skills_str = parts[-1].strip()
                    skills_list = [
                        s.strip() for s in skills_str.split(",") if s.strip()
                    ]
                    extracted["skills"].extend(skills_list)

            # Certifications extraction
            if any(
                kw in line_lower
                for kw in ["certification", "certified", "certificate", "credential"]
            ):
                extracted["certifications"].append(line.strip())

        logger.debug("Extracted text data: %s", extracted)
    except Exception as exc:
        logger.warning("Error extracting text data: %s", exc)


def _extract_csv_data(content: str, extracted: dict[str, Any]) -> None:
    """
    Extract structured data from CSV content.
    Assumes CSV has headers and processes rows for relevant data.
    """
    try:
        lines = content.strip().split("\n")
        if not lines:
            return

        # Parse header
        headers = [h.strip().lower() for h in lines[0].split(",")]

        # Look for relevant columns
        for row_idx, line in enumerate(lines[1:], 1):
            values = [v.strip() for v in line.split(",")]
            row_dict = dict(zip(headers, values))

            # Academic data
            if any(col in headers for col in ["gpa", "major", "degree"]):
                for col in ["gpa", "major", "degree", "graduation_year"]:
                    if col in headers and row_dict.get(col):
                        extracted["academic"][col] = row_dict[col]

            # Skills data
            if any(col in headers for col in ["skill", "skills", "competency"]):
                for col in ["skill", "skills", "competency"]:
                    if col in headers and row_dict.get(col):
                        skill = row_dict[col].strip()
                        if skill and skill not in extracted["skills"]:
                            extracted["skills"].append(skill)

            # Certifications
            if any(col in headers for col in ["certification", "certificate"]):
                for col in ["certification", "certificate"]:
                    if col in headers and row_dict.get(col):
                        cert = row_dict[col].strip()
                        if cert and cert not in extracted["certifications"]:
                            extracted["certifications"].append(cert)

        logger.debug("Extracted CSV data: %s", extracted)
    except Exception as exc:
        logger.warning("Error extracting CSV data: %s", exc)
