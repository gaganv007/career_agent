"""
Module defining back-end utility functions for managing user memory,
retreiving information, processing documents, and
extracting structured information.

!!!!!WIP!!!!!
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

logger = logging.getLogger("AgentLogger")

