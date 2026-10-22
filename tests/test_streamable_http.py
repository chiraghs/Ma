"""
Integration test for MCP Streamable HTTP Transport (Specification 2025-11-25).
Spawns the MA Voice Companion server and validates JSON-RPC exchanges,
session ID persistence, tools listing, tool execution, and MCP Apps UI resource reading.
"""

import asyncio
import json
import os
import sys
import httpx
import pytest

SERVER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server")
sys.path.insert(0, SERVER_PATH)

from main import mcp
from seed import seed_database


@pytest.mark.anyio
async def test_mcp_streamable_http_lifecycle():
    seed_database()

    test_port = 8011
    base_url = f"http://127.0.0.1:{test_port}/mcp"

    # Start server as background task
    server_task = asyncio.create_task(
        mcp.run_streamable_http_async(
            host="127.0.0.1",
            port=test_port,
            streamable_http_path="/mcp"
        )
    )

    await asyncio.sleep(1)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Initialize Request
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "alexa-simulator", "version": "1.0.0"}
                }
            }
            init_res = await client.post(
                base_url,
                headers={"Accept": "application/json, text/event-stream"},
                json=init_payload
            )

            assert init_res.status_code == 200
            session_id = init_res.headers.get("mcp-session-id")
            assert session_id is not None, "Server MUST return mcp-session-id header"
            assert "2025-11-25" in init_res.text

            # Parse event-stream or json data
            print(f"✅ Step 1: Initialize passed. Session ID: {session_id}")

            session_headers = {
                "Accept": "application/json, text/event-stream",
                "MCP-Session-Id": session_id,
                "MCP-Protocol-Version": "2025-11-25"
            }

            # 2. Tools List Request
            tools_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            tools_res = await client.post(base_url, headers=session_headers, json=tools_payload)
            assert tools_res.status_code == 200
            assert "log_feed" in tools_res.text
            assert "log_sleep" in tools_res.text
            assert "baby_summary" in tools_res.text
            assert "mood_checkin" in tools_res.text
            assert "trend_check" in tools_res.text
            assert "partner_tasks" in tools_res.text
            print("✅ Step 2: tools/list verified all 6 MA tools registered.")

            # 3. Tools Call Request (baby_summary)
            call_payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "baby_summary",
                    "arguments": {"period": "today"}
                }
            }
            call_res = await client.post(base_url, headers=session_headers, json=call_payload)
            assert call_res.status_code == 200
            assert "Maya" in call_res.text
            print("✅ Step 3: tools/call baby_summary executed successfully.")

            # 4. Resources Read Request (MCP Apps UI Resource)
            res_payload = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {
                    "uri": "ui://ma/baby-summary-card"
                }
            }
            res_read = await client.post(base_url, headers=session_headers, json=res_payload)
            assert res_read.status_code == 200
            assert "Baby Maya's Day" in res_read.text
            print("✅ Step 4: resources/read ui://ma/baby-summary-card returned interactive HTML.")

    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
