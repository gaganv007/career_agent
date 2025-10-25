# pylint: disable=import-error
import os
import logging
from typing import Any

from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AgentLogger")

ask_vertex_retrieval = VertexAiRagRetrieval(
    name="retrieve_rag_documentation",
    description=(
        "Use this tool to retrieve documentation and reference materials for the question from the RAG corpus,"
    ),
    rag_resources=[
        rag.RagResource(
            # please fill in your own rag corpus
            # here is a sample rag corpus for testing purpose
            # e.g. projects/123/locations/us-central1/ragCorpora/456
            rag_corpus=os.environ.get("RAG_CORPUS")
        )
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.6,
)


def _summarize_course_recommendations(
    self, job_title: str, courses: list[dict[str, Any]]
) -> str:
    """
    Generates an HTML table for course recommendations.
    """
    if not courses:
        return f"<p>No available BU MET courses fit your schedule for the {job_title} path.</p>"

    table_rows = "".join(
        [
            f"<tr>"
            f"<td>{c['course_code']}</td>"
            f"<td>{c['title']}</td>"
            f"<td>{c.get('description', '—')}</td>"
            f"<td>{c.get('schedule', '—')}</td>"
            f"</tr>"
            for c in courses[:5]
        ]
    )

    html_table = (
        f"<h3>Recommended Courses for {job_title}</h3>"
        f"<table border='1' style='border-collapse:collapse;width:100%;text-align:left;'>"
        f"<thead><tr>"
        f"<th>Course Code</th><th>Title</th><th>Description</th><th>Schedule</th>"
        f"</tr></thead>"
        f"<tbody>{table_rows}</tbody></table>"
    )
    return html_table
