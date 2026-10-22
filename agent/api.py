"""
MA Voice Companion Agent API (FastAPI).
Exposes POST /chat endpoint for Alexa+ simulation and web interface.
Connects to MA MCP Server over Streamable HTTP.
"""

import os
import sys
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure agent and server packages are on path
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(AGENT_DIR)
SERVER_DIR = os.path.join(ROOT_DIR, "server")

for p in (AGENT_DIR, ROOT_DIR, SERVER_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from agent import MaMCPDirectClient, MaVoiceAgent

app = FastAPI(
    title="MA Voice Companion Agent API",
    description="Alexa+ Agent endpoint coordinating Amazon Bedrock & MCP Tools for new mothers",
    version="1.0.0"
)

# Enable CORS for the Alexa+ simulator web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton instances
mcp_client = MaMCPDirectClient()
voice_agent = MaVoiceAgent(mcp_client=mcp_client)


class ChatRequest(BaseModel):
    message: str
    is_night_mode: Optional[bool] = None


class ToolCallRecord(BaseModel):
    name: str
    args: Dict[str, Any]
    result: Dict[str, Any]


class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[Dict[str, Any]]
    is_night_mode: bool
    safety_triggered: bool = False
    helplines: Optional[List[Dict[str, Any]]] = None


@app.get("/health")
async def health_check():
    """Health check endpoint showing agent status and MCP server connection."""
    return {
        "status": "healthy",
        "service": "MA Voice Agent",
        "mcp_server": mcp_client.base_url,
        "bedrock_configured": voice_agent.has_bedrock
    }


@app.get("/tools")
async def get_tools():
    """Retrieve all available MCP tools from the connected Streamable HTTP server."""
    try:
        tools = await mcp_client.list_tools()
        return {"tools": tools}
    except Exception as e:
        return {"error": str(e), "tools": []}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Main conversational endpoint for Alexa+ voice simulator.
    Processes user voice or text input, evaluates distress/safety,
    calls MCP tools, and returns voice-ready 1-2 sentence replies.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = await voice_agent.process_message(
        message=req.message.strip(),
        is_night_mode=req.is_night_mode
    )

    return ChatResponse(
        reply=result["reply"],
        tool_calls=result.get("tool_calls", []),
        is_night_mode=result.get("is_night_mode", False),
        safety_triggered=result.get("safety_triggered", False),
        helplines=result.get("helplines")
    )


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🤖 MA Voice Companion Agent API")
    print("📍 Running on: http://127.0.0.1:8001")
    print("📡 Connected to MCP Server: http://127.0.0.1:8000/mcp")
    print("=" * 60)
    uvicorn.run("api:app", host="127.0.0.1", port=8001, reload=True)
