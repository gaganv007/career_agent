# pylint: disable=import-error
import os
import json
import uuid
import logging

from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger("AgentLogger")


def _summarize_course_recommendations(job_title: str, courses: list[dict[str, Any]]):
    """
    Normalize a list of course recommendation dicts into a stable JSON structure
    consumable by a front-end (HTML/React). Returns a JSON string.

    Output schema:
    {
      "job_title": "<job title>",
      "recommendations": [
        {
          "id": "<id or index>",
          "title": "<course title>",
          "provider": "<provider/org>",
          "description": "<short description>",
          "url": "<link to course>",
          "duration": "<duration string>",
          "difficulty": "<level>",
          "cost": "<cost or null>",
          "topics": ["topic1", "topic2"],
          "relevance_score": <number or null>,
          "recommended_for": "<job title>"
        },
        ...
      ]
    }
    """
    try:
        result = {"job_title": job_title, "recommendations": []}
        for idx, course in enumerate(courses or []):
            # normalize common field names to a stable schema
            title = course.get("title") or course.get("name") or ""
            provider = (
                course.get("provider")
                or course.get("org")
                or course.get("organization")
                or ""
            )
            description = course.get("description") or course.get("summary") or ""
            url = (
                course.get("url")
                or course.get("link")
                or course.get("course_url")
                or ""
            )
            duration = course.get("duration") or course.get("length") or ""
            difficulty = course.get("difficulty") or course.get("level") or ""
            cost = (
                course.get("cost")
                if "cost" in course
                else course.get("price") if "price" in course else None
            )
            topics = course.get("topics") or course.get("tags") or []
            relevance = course.get("score") or course.get("relevance") or None
            course_id = course.get("id") or course.get("course_id") or str(idx)

            # normalize topics to list[str]
            if isinstance(topics, str):
                topics = [t.strip() for t in topics.split(",") if t.strip()]
            elif topics is None:
                topics = []

            normalized = {
                "id": course_id,
                "title": title,
                "provider": provider,
                "description": description,
                "url": url,
                "duration": duration,
                "difficulty": difficulty,
                "cost": cost,
                "topics": topics,
                "relevance_score": relevance,
                "recommended_for": job_title,
            }
            logger.debug(
                "Summarized course recommendation for %s: %s", course, normalized
            )
            result["recommendations"].append(normalized)

        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        logger.exception("Failed to summarize course recommendations: %s", exc)
        # Return a minimal valid JSON structure on error
        return json.dumps(
            {"job_title": job_title, "recommendations": []}, ensure_ascii=False
        )


def _summarize_course_schedule(course: str, schedule: list[dict[str, Any]]):
    """
    Normalize a course schedule into a stable JSON structure consumable by a front-end.
    Returns a JSON string.

    Output schema:
    {
      "course": "<course name or id>",
      "sessions": [
        {
          "id": "<id or index>",
          "session_title": "<title>",
          "date": "<date string or null>",
          "start_time": "<start time or null>",
          "end_time": "<end time or null>",
          "duration": "<duration string or null>",
          "instructor": "<instructor name or null>",
          "location": "<location or 'online' or null>",
          "url": "<link to session or null>",
          "notes": "<additional notes or null>",
          "sequence": <integer index>
        },
        ...
      ]
    }
    """
    try:
        result = {"course": course, "sessions": []}
        for idx, sess in enumerate(schedule or []):
            # normalize common field names
            session_title = (
                sess.get("title") or sess.get("session_title") or sess.get("name") or ""
            )
            date = sess.get("date") or sess.get("day") or None
            start_time = (
                sess.get("start_time") or sess.get("start") or sess.get("begin") or None
            )
            end_time = sess.get("end_time") or sess.get("end") or None
            duration = sess.get("duration") or sess.get("length") or None
            instructor = (
                sess.get("instructor")
                or sess.get("teacher")
                or sess.get("speaker")
                or None
            )
            location = (
                sess.get("location") or sess.get("place") or sess.get("venue") or None
            )
            url = sess.get("url") or sess.get("link") or sess.get("session_url") or None
            notes = (
                sess.get("notes")
                or sess.get("description")
                or sess.get("details")
                or None
            )
            session_id = sess.get("id") or sess.get("session_id") or str(idx)

            normalized = {
                "id": session_id,
                "session_title": session_title,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "instructor": instructor,
                "location": location,
                "url": url,
                "notes": notes,
                "sequence": idx,
            }
            logger.debug("Summarized course schedule: %s", normalized)
            result["sessions"].append(normalized)

        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        logger.exception("Failed to summarize course schedule: %s", exc)
        return json.dumps({"course": course, "sessions": []}, ensure_ascii=False)


def _summarize_skills_for_job(job_title: str, skills: list[dict[str, Any]]):
    """
    Normalize a list of skills for a job into a stable JSON structure.
    Returns a JSON string.

    Output schema:
    {
      "job_title": "<job title>",
      "skills": [
        {
          "id": "<id or index>",
          "name": "<skill name>",
          "category": "<technical/soft/other>",
          "proficiency_level": "<beginner/intermediate/advanced or score>",
          "importance": "<high/medium/low or numeric>",
          "years_experience_needed": "<years or null>",
          "recommended_training": ["course id", ...],
          "notes": "<additional notes or null>",
          "relevance_score": <number or null>
        },
        ...
      ]
    }
    """
    try:
        result = {"job_title": job_title, "skills": []}
        for idx, skill in enumerate(skills or []):
            name = skill.get("name") or skill.get("skill") or ""
            category = skill.get("category") or skill.get("type") or ""
            proficiency = (
                skill.get("proficiency")
                or skill.get("level")
                or skill.get("proficiency_level")
                or None
            )
            importance = skill.get("importance") or skill.get("priority") or None
            years = (
                skill.get("years_experience")
                or skill.get("years")
                or skill.get("experience")
                or None
            )
            recommended = (
                skill.get("recommended_training")
                or skill.get("recommended_courses")
                or skill.get("courses")
                or []
            )
            notes = skill.get("notes") or skill.get("description") or None
            relevance = skill.get("score") or skill.get("relevance") or None
            skill_id = skill.get("id") or skill.get("skill_id") or str(idx)

            # normalize recommended to list[str]
            if isinstance(recommended, str):
                recommended = [r.strip() for r in recommended.split(",") if r.strip()]
            elif recommended is None:
                recommended = []

            normalized = {
                "id": skill_id,
                "name": name,
                "category": category,
                "proficiency_level": proficiency,
                "importance": importance,
                "years_experience_needed": years,
                "recommended_training": recommended,
                "notes": notes,
                "relevance_score": relevance,
            }
            logger.debug("Summarized skills for job %s: %s", job_title, normalized)
            result["skills"].append(normalized)

        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        logger.exception("Failed to summarize skills for job %s: %s", job_title, exc)
        return json.dumps({"job_title": job_title, "skills": []}, ensure_ascii=False)


def _summarize_career_path(job_title: str, path: list[dict[str, Any]]):
    """
    Normalize a career path for a job into a stable JSON structure.
    Returns a JSON string.

    Output schema:
    {
      "job_title": "<job title>",
      "career_path": [
        {
          "id": "<id or index>",
          "title": "<position/title>",
          "description": "<summary of step>",
          "expected_duration": "<e.g., 1-2 years or months>",
          "recommended_skills": ["skill1", ...],
          "prerequisites": ["certification", ...],
          "next_positions": ["next role title", ...],
          "sequence": <integer index>
        },
        ...
      ]
    }
    """
    try:
        result = {"job_title": job_title, "career_path": []}
        for idx, step in enumerate(path or []):
            title = step.get("title") or step.get("position") or step.get("role") or ""
            description = step.get("description") or step.get("summary") or None
            duration = (
                step.get("expected_duration")
                or step.get("duration")
                or step.get("timeframe")
                or None
            )
            recommended_skills = (
                step.get("recommended_skills") or step.get("skills") or []
            )
            prerequisites = step.get("prerequisites") or step.get("requirements") or []
            next_positions = (
                step.get("next_positions")
                or step.get("next_roles")
                or step.get("promotions")
                or []
            )
            step_id = step.get("id") or step.get("step_id") or str(idx)

            # normalize lists
            def _to_list(v):
                if isinstance(v, str):
                    return [i.strip() for i in v.split(",") if i.strip()]
                return v or []

            recommended_skills = _to_list(recommended_skills)
            prerequisites = _to_list(prerequisites)
            next_positions = _to_list(next_positions)

            normalized = {
                "id": step_id,
                "title": title,
                "description": description,
                "expected_duration": duration,
                "recommended_skills": recommended_skills,
                "prerequisites": prerequisites,
                "next_positions": next_positions,
                "sequence": idx,
            }
            logger.debug("Summarized career path for job %s: %s", job_title, normalized)
            result["career_path"].append(normalized)

        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        logger.exception(
            "Failed to summarize career path for job %s: %s", job_title, exc
        )
        return json.dumps(
            {"job_title": job_title, "career_path": []}, ensure_ascii=False
        )


def _summarize_web_search(
    query: str,
    results: list[dict[str, Any]],
    analysis: Optional[str] = None,
    top_k: Optional[int] = None,
):
    """
    Normalize web search results and optional analysis into a stable JSON structure.
    Returns a JSON string.

    Output schema:
    {
      "query": "<search query>",
      "returned_count": <int>,
      "top_k": <int or null>,
      "timestamp": "<iso ts>",
      "results": [
        {
          "rank": <index starting at 0>,
          "title": "<page title>",
          "snippet": "<short snippet or summary>",
          "url": "<link>",
          "domain": "<source domain>",
          "published_at": "<date or null>",
          "content_type": "<html/pdf/rss/other or null>",
          "relevance_score": <number or null>,
          "raw": { ... original item ... }  # kept for debugging if needed
        },
        ...
      ],
      "analysis": "<aggregated analysis text or null>"
    }
    """
    try:
        iso_ts = datetime.now().isoformat() + "Z"
        normalized_results = []
        for idx, item in enumerate(results or []):
            if top_k is not None and idx >= top_k:
                break
            title = item.get("title") or item.get("headline") or item.get("name") or ""
            snippet = (
                item.get("snippet")
                or item.get("summary")
                or item.get("description")
                or ""
            )
            url = item.get("url") or item.get("link") or item.get("uri") or ""
            domain = None
            try:
                # derive domain if possible
                if url:
                    domain = url.split("//")[-1].split("/")[0]
            except Exception:
                domain = None
            published = (
                item.get("published")
                or item.get("published_at")
                or item.get("date")
                or None
            )
            content_type = item.get("type") or item.get("content_type") or None
            score = (
                item.get("score")
                or item.get("relevance")
                or item.get("relevance_score")
                or None
            )

            normalized = {
                "rank": idx,
                "title": title,
                "snippet": snippet,
                "url": url,
                "domain": domain,
                "published_at": published,
                "content_type": content_type,
                "relevance_score": score,
                "raw": item,
            }
            normalized_results.append(normalized)

        payload = {
            "query": query,
            "returned_count": len(results or []),
            "top_k": top_k if top_k is not None else None,
            "timestamp": iso_ts,
            "results": normalized_results,
            "analysis": analysis or None,
        }
        logger.debug("Summarized web search for query '%s': %s", query, payload)
        return json.dumps(payload, ensure_ascii=False)
    except Exception as exc:
        logger.exception(
            "Failed to summarize web search for query '%s': %s", query, exc
        )
        return json.dumps(
            {"query": query, "returned_count": 0, "results": [], "analysis": None},
            ensure_ascii=False,
        )
