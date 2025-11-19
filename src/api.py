## Use this script to run the chat API Server
## Then open index.html through a web browser
## to interact with the agent via the UI

import sys
from pathlib import Path
import asyncio
import time
from collections import deque

# Add src directory to Python path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from typing import Optional
import uvicorn

from setup.logger_config import AgentLogger
from setup.interactions import query_agent
from agents.team import orchestrator

app = FastAPI(title="BU Agent API")
static_dir = Path(__file__).parent / "."  # Points to src/
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

# Enable CORS for frontend communication
## SS: Resource sharing between ???
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


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "web_user"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str


@app.on_event("startup")
async def startup_event():
    """Initialize logger on startup"""
    AgentLogger()
    print("\n" + "=" * 60)
    print("BU Agent API Server Started")
    print("=" * 60)
    print("📍 API URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("⚠️  Rate Limit: 8 requests per minute")
    print("💡 Tip: Wait at least 8 seconds between messages")
    print("=" * 60 + "\n")


@app.get("/")
async def root():
    return {
        "message": "BU Agent API is running",
        "rate_limit": "8 requests per minute",
        "endpoints": {
            "/chat": "POST - Send a message to the agent",
            "/health": "GET - Check server health",
            "/sessions": "GET - List active sessions",
        },
    }


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

        print(f"\n📨 Processing message from {user_id}: '{request.message[:50]}...'")

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
            print(f"✅ Created new session: {session_key}")
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

        print(f"✅ Response sent successfully")

        return ChatResponse(response=response, session_id=session_id, user_id=user_id)

    except HTTPException:
        # Re-raise HTTP exceptions (like rate limit)
        raise

    except Exception as e:
        import traceback

        error_detail = f"Error: {str(e)}"

        # Check if it's a Google API rate limit error
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print(f"\n⚠️  Google API Rate Limit Hit!")
            print("Solutions:")
            print("1. Wait 1 minute for quota to reset")
            print("2. Switch to a different model in .env")
            print("3. Reduce request frequency\n")

            raise HTTPException(
                status_code=429,
                detail="Google API quota exceeded. Please wait 60 seconds before trying again.",
            )

        print(
            f"\n{'='*60}\nERROR in /chat endpoint:\n{error_detail}\n\nTraceback:\n{traceback.format_exc()}\n{'='*60}\n"
        )
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {"active_sessions": len(sessions), "sessions": list(sessions.keys())}


@app.delete("/session/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    """Delete a specific session"""
    session_key = f"{user_id}_{session_id}"
    if session_key in sessions:
        del sessions[session_key]
        return {"message": f"Session {session_key} deleted"}
    return {"message": "Session not found"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
