"""
Module to define agent-related functions, such as database reads
"""

# pylint: disable=import-error
import logging
import sqlalchemy
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval

logger = logging.getLogger("AgentLogger")
