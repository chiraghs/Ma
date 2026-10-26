"""
MA Agent Layer (AWS Builder & Alexa+ Companion).
Connects to the MA MCP Server over Streamable HTTP (2025-11-25) as an MCP client.
Orchestrates tools using Amazon Bedrock / Strands Agents SDK with built-in
voice-first constraints, Night Mode detection, and safety guardrails.
"""

from datetime import datetime
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
import httpx

# Automatically load environment variables from .env
load_dotenv()
try:
    import boto3
except ImportError:
    boto3 = None

# Ensure server module is accessible for direct fallback / safety imports
SERVER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server")
if SERVER_PATH not in sys.path:
    sys.path.insert(0, SERVER_PATH)

from safety import detect_distress_keywords, detect_medical_inquiry, evaluate_distress

# System Prompt encoding MA's core principles
SYSTEM_PROMPT = """You are "MA", a compassionate, warm, non-judgmental voice companion and supporter for new mothers, designed for Alexa+.

CORE PRINCIPLES:
1. Companion, not tracker: Warm, empathetic, non-judgmental. Never judge feeding choices (breast vs bottle vs formula) or sleep patterns.
2. Voice-first brevity:
   - Daytime: Exactly 1 to 2 short sentences.
   - Night mode (10:00 PM to 6:00 AM, or when mom is exhausted/feeding at night): Exactly ONE short, soothing sentence.
3. Not medical advice: Never provide medical diagnoses, treatment advice, or drug dosages. For any symptom or medical inquiry, always gently state: "Please check with your doctor, pediatrician, or midwife."
4. Route distress to care response: If mother expresses severe despair, hopelessness, or thoughts of self-harm, prioritize immediate support and care resources. Never be cheerful or dismissive.
5. Action-oriented: Call the appropriate tool when she mentions feeds, sleeps, how she's feeling, checking rhythms, or partner tasks.
"""

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8005/mcp")
DEFAULT_BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")


def is_night_mode_now() -> bool:
    """Return True if local time is between 10:00 PM (22:00) and 6:00 AM."""
    now_hour = datetime.now().hour
    return now_hour >= 22 or now_hour < 6


class MaMCPDirectClient:
    """
    Lightweight, robust Streamable HTTP MCP Client (MCP 2025-11-25 compliant).
    Maintains session with the FastMCP / MCPServer over Streamable HTTP.
    """

    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self._tools: List[Dict[str, Any]] = []

    async def initialize(self) -> str:
        """Perform MCP initialize handshake and extract session ID."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                self.base_url,
                headers={"Accept": "application/json, text/event-stream"},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {},
                        "clientInfo": {"name": "ma-agent-client", "version": "1.0.0"}
                    }
                }
            )
            res.raise_for_status()
            self.session_id = res.headers.get("mcp-session-id")
            return self.session_id or ""

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Fetch list of tools from the MCP server."""
        if not self.session_id:
            await self.initialize()

        headers = {
            "Accept": "application/json, text/event-stream",
            "MCP-Session-Id": self.session_id or "",
            "MCP-Protocol-Version": "2025-11-25"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                self.base_url,
                headers=headers,
                json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            )
            # Parse response from event-stream or json
            data = self._parse_jsonrpc_body(res.text)
            self._tools = data.get("result", {}).get("tools", [])
            return self._tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool on the MCP server via Streamable HTTP POST."""
        if not self.session_id:
            await self.initialize()

        headers = {
            "Accept": "application/json, text/event-stream",
            "MCP-Session-Id": self.session_id or "",
            "MCP-Protocol-Version": "2025-11-25"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                self.base_url,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments}
                }
            )
            data = self._parse_jsonrpc_body(res.text)
            result = data.get("result", {})
            return result

    def _parse_jsonrpc_body(self, raw_text: str) -> Dict[str, Any]:
        """Parse either application/json or SSE text/event-stream data lines."""
        if raw_text.startswith("event:") or "data:" in raw_text:
            for line in raw_text.splitlines():
                if line.startswith("data:"):
                    json_str = line[len("data:"):].strip()
                    try:
                        return json.loads(json_str)
                    except Exception:
                        pass
        try:
            return json.loads(raw_text)
        except Exception:
            return {}


class MaVoiceAgent:
    """
    MA Voice Agent connecting Alexa+ prompts to Amazon Bedrock & MCP Tools.
    """

    def __init__(self, mcp_client: Optional[MaMCPDirectClient] = None):
        self.mcp_client = mcp_client or MaMCPDirectClient()

    @property
    def has_bedrock(self) -> bool:
        """Dynamically detect whether active AWS credentials or profile are configured."""
        return bool(
            os.environ.get("AWS_ACCESS_KEY_ID") or 
            os.environ.get("AWS_PROFILE")
        )

    async def process_message(
        self,
        message: str,
        is_night_mode: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Process user message, execute safety checks, invoke Bedrock or internal loop,
        execute MCP tools over Streamable HTTP, and format response.
        """
        # 1. Determine Night Mode
        night_mode = is_night_mode if is_night_mode is not None else is_night_mode_now()

        # 2. Safety Interception: Check for medical inquiries
        med_redirect = detect_medical_inquiry(message)
        if med_redirect:
            reply = med_redirect if not night_mode else "Please check with your doctor or midwife right away."
            return {
                "reply": reply,
                "tool_calls": [],
                "is_night_mode": night_mode,
                "safety_triggered": True
            }

        # 3. Safety Interception: Check for crisis/distress keywords (including negations)
        kw = detect_distress_keywords(message)
        if kw["matched"]:
            # Route to care response immediately
            distress_eval = evaluate_distress(feeling=message, score=1)
            care_reply = distress_eval.get("care_response", "")
            return {
                "reply": care_reply,
                "tool_calls": [],
                "is_night_mode": night_mode,
                "safety_triggered": True,
                "helplines": distress_eval.get("helplines", [])
            }

        # 4. Invoke Live Amazon Bedrock Converse API if AWS credentials are configured
        if self.has_bedrock:
            bedrock_res = await self._call_bedrock(message, night_mode)
            if bedrock_res is not None:
                return bedrock_res

        # 5. Intent & Tool Selection Loop (Local Fallback)
        tool_calls: List[Dict[str, Any]] = []
        intent, args = self._classify_intent(message)

        if intent:
            try:
                tool_res = await self.mcp_client.call_tool(intent, args)
                # Unwrap structured response or content
                content = tool_res.get("content", [])
                text_content = ""
                if isinstance(content, list) and content:
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_content = item.get("text", "")
                            break
                        elif hasattr(item, "text"):
                            text_content = item.text
                            break

                tool_calls.append({
                    "name": intent,
                    "args": args,
                    "result": tool_res
                })

                # If tool returned structured reply
                if text_content:
                    try:
                        parsed = json.loads(text_content)
                        raw_reply = parsed.get("reply", text_content)
                    except Exception:
                        raw_reply = text_content
                else:
                    raw_reply = tool_res.get("reply", "Recorded for you.")

                # Format voice reply (1 sentence in night mode, 1-2 daytime)
                reply = self._enforce_brevity(raw_reply, is_night_mode=night_mode)
                return {
                    "reply": reply,
                    "tool_calls": tool_calls,
                    "is_night_mode": night_mode,
                    "safety_triggered": False
                }

            except Exception as e:
                # Fallback to local tools if server not reached
                from tools import (
                    baby_summary_tool,
                    log_feed_tool,
                    log_sleep_tool,
                    mood_checkin_tool,
                    partner_tasks_tool,
                    trend_check_tool,
                )
                local_map = {
                    "log_feed": log_feed_tool,
                    "log_sleep": log_sleep_tool,
                    "baby_summary": baby_summary_tool,
                    "mood_checkin": mood_checkin_tool,
                    "trend_check": trend_check_tool,
                    "partner_tasks": partner_tasks_tool,
                }
                fn = local_map.get(intent)
                if fn:
                    res = fn(**args)
                    tool_calls.append({"name": intent, "args": args, "result": res})
                    reply = self._enforce_brevity(res.get("reply", ""), is_night_mode=night_mode)
                    return {
                        "reply": reply,
                        "tool_calls": tool_calls,
                        "is_night_mode": night_mode,
                        "safety_triggered": False
                    }

        # Conversational warm support reply if no tool matched
        conversational_reply = self._generate_conversational_reply(message, night_mode)
        return {
            "reply": conversational_reply,
            "tool_calls": [],
            "is_night_mode": night_mode,
            "safety_triggered": False
        }

    def _classify_intent(self, text: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Natural language intent classifier routing to MCP tools."""
        t = text.lower()

        # Feed Logging
        if any(w in t for w in ["feed", "fed", "nursed", "nursing", "bottle", "breast"]):
            minutes_or_ml = 15  # default
            numbers = re.findall(r"\b\d+\b", t)
            if numbers:
                minutes_or_ml = int(numbers[0])

            feed_type = "bottle" if "bottle" in t or "ml" in t or "oz" in t else (
                "breast_right" if "right" in t else "breast_left"
            )
            return "log_feed", {"feed_type": feed_type, "minutes_or_ml": minutes_or_ml, "note": text}

        # Sleep Logging
        if any(w in t for w in ["slept", "sleep", "nap", "woke", "waking", "asleep"]):
            if "summary" in t or "how much" in t or "did baby" in t:
                return "baby_summary", {"period": "today"}
            return "log_sleep", {"start": "1 hour ago", "end": "now", "note": text}

        # Baby Summary
        if any(w in t for w in ["summary", "rhythm", "how was", "how did", "how many feeds", "how much sleep"]):
            period = "last_night" if "night" in t else ("yesterday" if "yesterday" in t else "today")
            return "baby_summary", {"period": period}

        # Mood Check-in
        if any(w in t for w in ["i feel", "feeling", "mood", "exhausted", "tired", "happy", "calm", "sad"]):
            score = 3
            if any(w in t for w in ["exhausted", "depleted", "crying", "awful", "drained"]):
                score = 2
            elif any(w in t for w in ["good", "happy", "peaceful", "great", "rested"]):
                score = 5
            elif any(w in t for w in ["okay", "managing", "fine"]):
                score = 3
            return "mood_checkin", {"feeling": text, "score": score, "note": ""}

        # Trend Check
        if any(w in t for w in ["trend", "how have i been", "past few days", "check on me", "low mood"]):
            return "trend_check", {"days": 7}

        # Partner Tasks
        if any(w in t for w in ["partner", "husband", "tasks", "chore", "help", "assign", "bottles", "diapers"]):
            action = "assign" if any(w in t for w in ["assign", "tell", "ask him", "ask her", "add"]) else "list"
            return "partner_tasks", {"action": action, "task": text, "assignee": "Partner"}

        return None, {}

    def _enforce_brevity(self, text: str, is_night_mode: bool) -> str:
        """Enforce 1 sentence for night mode, 1-2 short sentences daytime."""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        if is_night_mode:
            return sentences[0] if sentences else text
        return " ".join(sentences[:2]) if len(sentences) >= 2 else text

    def _generate_conversational_reply(self, message: str, is_night_mode: bool) -> str:
        """Warm conversational response adhering to companion principles."""
        if is_night_mode:
            return "Rest gently, mama; you're doing a wonderful job tonight."
        return "I'm right here with you. Take one quiet breath—you're doing so much good work today."

    def _mcp_to_bedrock_tools(self, mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform standard MCP JSON Schema tools into Amazon Bedrock Converse toolSpec format."""
        bedrock_tools = []
        for tool in mcp_tools:
            name = tool.get("name", "")
            desc = tool.get("description", "")
            schema = tool.get("inputSchema", {})
            properties = {}
            for p_name, p_val in schema.get("properties", {}).items():
                if isinstance(p_val, dict):
                    prop_entry = {
                        "type": p_val.get("type", "string"),
                        "description": p_val.get("description", "")
                    }
                    if "enum" in p_val:
                        prop_entry["enum"] = p_val["enum"]
                    properties[p_name] = prop_entry
            bedrock_tools.append({
                "toolSpec": {
                    "name": name,
                    "description": desc,
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": properties,
                            "required": schema.get("required", [])
                        }
                    }
                }
            })
        return bedrock_tools

    async def _call_bedrock(self, message: str, night_mode: bool) -> Optional[Dict[str, Any]]:
        """
        Invoke Amazon Bedrock Converse API with real MCP tools.
        Returns response dict or None if AWS is unconfigured or fails.
        """
        if not boto3 or not (os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE")):
            return None

        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
        model_id = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

        try:
            client = boto3.client("bedrock-runtime", region_name=region)
            mcp_tools = await self.mcp_client.list_tools()
            bedrock_tools = self._mcp_to_bedrock_tools(mcp_tools)
            tool_config = {"tools": bedrock_tools} if bedrock_tools else None
            system_prompt = SYSTEM_PROMPT + (
                "\nCURRENT STATUS: Circadian Night Mode is ACTIVE. Respond in exactly ONE short, soothing sentence."
                if night_mode else
                "\nCURRENT STATUS: Daytime. Respond in 1 to 2 short sentences."
            )
            messages = [{"role": "user", "content": [{"text": message}]}]
            kwargs = {
                "modelId": model_id,
                "messages": messages,
                "system": [{"text": system_prompt}]
            }
            if tool_config:
                kwargs["toolConfig"] = tool_config

            response = client.converse(**kwargs)
            output_msg = response.get("output", {}).get("message", {})
            stop_reason = response.get("stopReason")
            tool_calls = []

            if stop_reason == "tool_use":
                content_blocks = output_msg.get("content", [])
                tool_results_content = []
                for block in content_blocks:
                    if "toolUse" in block:
                        tool_use = block["toolUse"]
                        tool_use_id = tool_use["toolUseId"]
                        tool_name = tool_use["name"]
                        tool_input = tool_use.get("input", {})

                        tool_res = await self.mcp_client.call_tool(tool_name, tool_input)
                        tool_calls.append({
                            "name": tool_name,
                            "args": tool_input,
                            "result": tool_res
                        })
                        tool_results_content.append({
                            "toolResult": {
                                "toolUseId": tool_use_id,
                                "content": [{"json": tool_res}]
                            }
                        })

                messages.append(output_msg)
                messages.append({
                    "role": "user",
                    "content": tool_results_content
                })
                follow_up = client.converse(
                    modelId=model_id,
                    messages=messages,
                    system=[{"text": system_prompt}]
                )
                follow_up_blocks = follow_up.get("output", {}).get("message", {}).get("content", [])
                raw_reply = "".join(b.get("text", "") for b in follow_up_blocks if "text" in b)
            else:
                content_blocks = output_msg.get("content", [])
                raw_reply = "".join(b.get("text", "") for b in content_blocks if "text" in b)

            if raw_reply:
                reply = self._enforce_brevity(raw_reply, is_night_mode=night_mode)
                return {
                    "reply": reply,
                    "tool_calls": tool_calls,
                    "is_night_mode": night_mode,
                    "safety_triggered": False,
                    "bedrock_used": True,
                    "model_id": model_id
                }
        except Exception as e:
            print(f"[Bedrock Notice] Live AWS call not reached ({e}). Using local fallback loop.")
            return None
        return None
