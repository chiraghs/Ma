"""
MA Voice Companion - Official MCP Server
Built with official Python MCP SDK using the Streamable HTTP transport (MCP spec 2025-11-25).
Serves tools and MCP Apps (SEP-1865) interactive UI resources on port 8000 at path /mcp.
"""

import os
import sys
from typing import Any, Dict, Literal

# Ensure server module directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.mcpserver import MCPServer
from db import init_db
from resources import UI_RESOURCES
from tools import (
    baby_summary_tool,
    log_feed_tool,
    log_sleep_tool,
    mood_checkin_tool,
    partner_tasks_tool,
    trend_check_tool,
)

# Compatibility alias for FastMCP
FastMCP = MCPServer

# Initialize server
mcp = MCPServer(
    name="MA Voice Companion",
    version="1.0.0",
    instructions="Voice companion and non-judgmental supporter for new mothers."
)


# ---------------------------------------------------------
# Tool Registrations with Typing & Docstrings
# ---------------------------------------------------------

@mcp.tool()
def log_feed(
    feed_type: Literal["breast_left", "breast_right", "bottle", "solid"],
    minutes_or_ml: int,
    note: str = ""
) -> Dict[str, Any]:
    """
    Log a baby feeding session. Warm, brief, non-judgmental.
    
    Args:
        feed_type: Nursing side or bottle/solids ('breast_left', 'breast_right', 'bottle', 'solid')
        minutes_or_ml: Duration in minutes for nursing, or amount in ml for bottle/solids
        note: Optional note (e.g., 'burped well', 'pumped milk', 'calm feed')
    """
    return log_feed_tool(feed_type=feed_type, minutes_or_ml=minutes_or_ml, note=note)


@mcp.tool()
def log_sleep(
    start: str,
    end: str,
    note: str = ""
) -> Dict[str, Any]:
    """
    Log baby sleep or nap interval using natural time strings (e.g. '1am', '2:30pm', 'now').
    
    Args:
        start: Start time (e.g. '1pm', '10:30pm', '2 hours ago')
        end: End time (e.g. '2:15pm', 'now', '7am')
        note: Optional context (e.g. 'crib nap', 'contact nap')
    """
    return log_sleep_tool(start=start, end=end, note=note)


@mcp.tool()
def baby_summary(
    period: Literal["last_night", "today", "yesterday", "week"] = "today"
) -> Dict[str, Any]:
    """
    Get a warm, plain-language summary of baby's feeding and sleep rhythm.
    
    Args:
        period: Summary time period ('last_night', 'today', 'yesterday', 'week')
    """
    return baby_summary_tool(period=period)


@mcp.tool()
def mood_checkin(
    feeling: str,
    score: int,
    note: str = ""
) -> Dict[str, Any]:
    """
    Record mother's emotional well-being check-in with empathetic, guilt-free listening.
    Monitors for signs of distress or exhaustion.
    
    Args:
        feeling: How mom describes feeling (e.g., 'exhausted', 'calm', 'overwhelmed', 'peaceful')
        score: Rating from 1 (very depleted/struggling) to 5 (energized/peaceful)
        note: Optional reflection or thoughts
    """
    return mood_checkin_tool(feeling=feeling, score=score, note=note)


@mcp.tool()
def trend_check(
    days: int = 7
) -> Dict[str, Any]:
    """
    Analyze past days of mood check-ins and rest to flag sustained low mood or extreme sleep loss.
    Provides compassionate care suggestions and partner task recommendations.
    
    Args:
        days: Number of days to review (default: 7)
    """
    return trend_check_tool(days=days)


@mcp.tool()
def partner_tasks(
    action: Literal["assign", "list", "complete"] = "list",
    task: str = "",
    assignee: str = "Partner"
) -> Dict[str, Any]:
    """
    Coordinate family support tasks so mom is not doing everything alone.
    
    Args:
        action: 'assign' to create a task, 'list' to view pending tasks, 'complete' to finish one
        task: Description of task or task ID to complete
        assignee: Name of helper (defaults to 'Partner')
    """
    return partner_tasks_tool(action=action, task=task, assignee=assignee)


# ---------------------------------------------------------
# MCP Apps UI Resource Registrations (SEP-1865)
# ---------------------------------------------------------

@mcp.resource("ui://ma/baby-summary-card")
def get_baby_summary_card() -> str:
    """Return interactive HTML card for baby rhythm timeline (SEP-1865)."""
    return UI_RESOURCES["ui://ma/baby-summary-card"]["html"]


@mcp.resource("ui://ma/mood-trend-card")
def get_mood_trend_card() -> str:
    """Return interactive HTML card for mother's mood trend (SEP-1865)."""
    return UI_RESOURCES["ui://ma/mood-trend-card"]["html"]


@mcp.resource("ui://ma/partner-tasks-card")
def get_partner_tasks_card() -> str:
    """Return interactive HTML card for partner support checklist (SEP-1865)."""
    return UI_RESOURCES["ui://ma/partner-tasks-card"]["html"]


# ---------------------------------------------------------
# Server Entrypoint
# ---------------------------------------------------------

def main():
    port = int(os.environ.get("MCP_PORT", 8005))
    print("=" * 60)
    print("🌸 MA Voice Companion - Official MCP Server (FastMCP)")
    print("⚡ Transport: Streamable HTTP (Specification 2025-11-25)")
    print(f"📍 Endpoint: http://127.0.0.1:{port}/mcp")
    print("=" * 60)
    
    init_db()
    
    # Run over Streamable HTTP transport
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=port,
        streamable_http_path="/mcp"
    )


if __name__ == "__main__":
    main()
