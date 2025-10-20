import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from typing import Optional
import uvicorn

from setup.logger_config import AgentLogger
from setup.interactions import query_agent
from agents.team import AGENT

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
    print("BU Agent API Server Started")
    print("Visit http://localhost:8000/docs for API documentation")

@app.get("/")
async def root():
    return {
        "message": "BU Agent API is running",
        "endpoints": {
            "/chat": "POST - Send a message to the agent",
            "/health": "GET - Check server health",
            "/sessions": "GET - List active sessions"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the BU Agent and get a response
    """
    try:
        user_id = request.user_id
        session_id = request.session_id or f"session_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create or get existing session
        session_key = f"{user_id}_{session_id}"
        if session_key not in sessions:
            # Create new session
            await service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
                state={}
            )
            
            # Create runner for this session
            runner = Runner(
                agent=AGENT,
                app_name=APP_NAME,
                session_service=service,
            )
            sessions[session_key] = runner
        else:
            runner = sessions[session_key]
        
        # Query the agent
        response = await query_agent(
            query=request.message,
            runner=runner,
            user_id=user_id,
            session_id=session_id,
        )
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            user_id=user_id
        )
        
    except Exception as e:
        import traceback
        error_detail = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"\n{'='*60}\nERROR in /chat endpoint:\n{error_detail}\n{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "active_sessions": len(sessions),
        "sessions": list(sessions.keys())
    }

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