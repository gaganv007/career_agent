## Use this script to run the chat API Server
## Then open index.html through a web browser
## to interact with the agent via the UI

import os
import sys
import asyncio
import uvicorn
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# Add src directory to Python path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Fast API imports
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Google ADK
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# Custom modules
from setup.api_functions import parse_document
from setup.logger_config import setup_logging
from setup.schemas import ChatRequest, ChatResponse, DocumentUploadResponse
from agents.team import orchestrator, query_per_min_limit, token_guard

app = FastAPI(title="BU Agent API")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for session management
APP_NAME = "BU MET 633 Fall 2025 Term Project"
service = InMemorySessionService()
sessions = {}  # Store user sessions

logger = setup_logging()
logging.getLogger("google_genai.types").setLevel(logging.ERROR)


@app.on_event("startup")
async def startup_event():
    """Initialize logger on startup"""
    logger = setup_logging()
    print("BU Agent API Server Started")
    print("=" * 60)
    print("📍 API URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print(f"⚠️  Rate Limit: {query_per_min_limit} requests per minute")
    print(
        f"💡 Tip: Wait at least {60/query_per_min_limit:.2f} seconds between messages"
    )
    print("=" * 60 + "\n")


@app.get("/")
async def root():
    # Serve the main frontend
    index_path = Path(__file__).parent / "static" / "index.html"
    return FileResponse(index_path)


@app.get("/health")
async def health_check():
    # Health checks don't count against rate limit
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the BU Agent and get a response
    """
    try:
        user_id = request.user_id
        session_id = (
            request.session_id
            or f"session_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        logger.info(f"⚙️ User: {user_id}, Session: {session_id}")

        # Set token guard mode based on query source
        token_guard.set_document_mode(request.is_document_upload or False)
        logger.debug(
            f"📨 Query Type: {'File Upload' if request.is_document_upload else 'Direct Message'}"
        )

        # Create or get existing session
        session_key = f"{user_id}_{session_id}"
        if session_key not in sessions:
            # Create new session
            await service.create_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id, state={}
            )

            # Create runner for this session
            runner = Runner(
                agent=orchestrator,
                app_name=APP_NAME,
                session_service=service,
            )
            sessions[session_key] = runner
            logger.info(f"💻 Created new session: {session_key}")
        else:
            runner = sessions[session_key]

        # Add a small delay to prevent rapid-fire requests
        await asyncio.sleep(0.5)

        # Query the agent
        response = await query_agent(
            query=request.message,
            runner=runner,
            user_id=user_id,
            session_id=session_id,
        )

        logger.info(f"✅ Response sent successfully")

        return ChatResponse(response=response, session_id=session_id, user_id=user_id)

    except HTTPException:
        # Re-raise HTTP exceptions (like rate limit)
        raise

    except Exception as e:
        import traceback

        error_detail = f"Error: {str(e)}"
        logger.error(error_detail)
        logger.info(
            f"\n{'='*60}\nERROR in /chat endpoint:\n"
            f"{error_detail}\n\nTraceback:\n{traceback.format_exc()}\n{'='*60}\n"
        )


async def query_agent(query: str, runner, user_id, session_id) -> str:
    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response_text = "Agent did not produce a final response."
    logger.debug(f"✏️ {user_id} sent:\n'{query}'")

    # Key Concept: run_async executes the agent logic and yields Events.
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        logger.info(f"📊 Event Triggered: {event.__name__} (type: {type(event).__name__})")

        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            logger.info(f"✅ Received Final Response")

            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif (
                event.actions and event.actions.escalate
            ):  # Handle potential errors/escalations
                final_response_text = (
                    f"Agent escalated: {event.error_message or 'No specific message.'}"
                )
                logger.warning(f"⚠️ Agent Escalated: {final_response_text}")
            else:
                logger.error(f"❌ Final Response has No Content!")
            # Add more checks here if needed (e.g., specific error codes)
            break

    logger.debug(f"🔚 {event.author} replied:\n'{final_response_text}'")
    return f"{final_response_text}"


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {"active_sessions": len(sessions), "sessions": list(sessions.keys())}


@app.post("/upload-document", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), document_type: str = ""):
    """
    Upload and parse a document (PDF, DOCX, or TXT).
    The extracted text will be processed by the Document Agent.
    """
    try:
        # Read the uploaded file
        file_content = await file.read()

        # Determine file type from either the provided parameter or file extension
        if not document_type:
            file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
            document_type = file_ext

        # Validate file type
        supported_types = ["pdf", "docx", "txt", "text"]
        if document_type.lower() not in supported_types:
            raise ValueError(
                f"Unsupported file type: {document_type}. Supported types: {', '.join(supported_types)}"
            )

        # Parse the document
        extracted_text = parse_document(file_content, document_type)

        if not extracted_text or len(extracted_text.strip()) == 0:
            raise ValueError(
                "Document appears to be empty or no text could be extracted"
            )

        char_count = len(extracted_text)
        logger.info(
            f"📄 Document uploaded and parsed: {file.filename}"
            f"Type: {document_type}, Characters extracted: {char_count}"
        )

        return DocumentUploadResponse(
            success=True,
            message=f"Successfully parsed {document_type.upper()} document",
            extracted_text=extracted_text,
            character_count=char_count,
        )

    except ValueError as e:
        error_msg = str(e)
        logger.info(f"⚠️  Document upload validation error: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        import traceback

        error_msg = f"Error processing document: {str(e)}"
        logger.info(
            f"❌ Error in /upload-document endpoint:\n{error_msg}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=error_msg)


@app.delete("/session/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    """Delete a specific session"""
    session_key = f"{user_id}_{session_id}"
    if session_key in sessions:
        del sessions[session_key]
        return {"message": f"Session {session_key} deleted"}
    return {"message": "Session not found"}


app.mount(
    "/static", StaticFiles(directory=str(Path(__file__).parent / "static"), html=True)
)

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
