"""
Unit tests for Phase 1: Core MCP Tools and SQLite Storage for MA Voice Companion.
"""

from datetime import datetime, timedelta
import os
import sys
import pytest

# Add server to path
SERVER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server")
sys.path.insert(0, SERVER_PATH)

from db import get_connection, init_db
from seed import seed_database
from tools import (
    baby_summary_tool,
    log_feed_tool,
    log_sleep_tool,
    mood_checkin_tool,
    parse_natural_time,
    partner_tasks_tool,
    trend_check_tool,
)


@pytest.fixture(autouse=True)
def setup_test_db():
    seed_database()
    yield


def test_natural_time_parser():
    ref = datetime(2026, 10, 23, 15, 0, 0)
    
    t1 = parse_natural_time("1pm", reference_date=ref)
    assert t1.hour == 13
    assert t1.minute == 0
    
    t2 = parse_natural_time("10:30am", reference_date=ref)
    assert t2.hour == 10
    assert t2.minute == 30
    
    t3 = parse_natural_time("2 hours ago", reference_date=ref)
    assert t3.hour == 13


def test_log_feed_tool():
    res = log_feed_tool("breast_left", 15, note="calm feed")
    assert "Logged 15 minutes of breast left" in res["reply"]
    assert res["feed_id"] > 0
    assert res["_meta"]["ui"]["resourceUri"] == "ui://ma/baby-summary-card"

    res_bottle = log_feed_tool("bottle", 120, note="formula")
    assert "Logged 120 ml of bottle" in res_bottle["reply"]


def test_log_sleep_tool():
    res = log_sleep_tool("1pm", "2:30pm", note="crib nap")
    assert "Logged Maya's sleep from 1:00 PM to 2:30 PM (1h 30m)" in res["reply"]
    assert res["duration_minutes"] == 90
    assert res["_meta"]["ui"]["resourceUri"] == "ui://ma/baby-summary-card"


def test_baby_summary_tool():
    res = baby_summary_tool("today")
    assert "Maya had" in res["reply"]
    assert res["total_feeds"] >= 2
    assert res["total_sleep_hours"] > 0
    assert res["_meta"]["ui"]["resourceUri"] == "ui://ma/baby-summary-card"


def test_mood_checkin_normal():
    res = mood_checkin_tool("peaceful", 5, "Felt present and rested")
    assert "peaceful" in res["reply"].lower()
    assert res["score"] == 5
    assert res["_meta"]["ui"]["resourceUri"] == "ui://ma/mood-trend-card"


def test_trend_check_sustained_low():
    # Because seed script populated days with gradual dip to 2
    res = trend_check_tool(days=5)
    # Average score or consecutive low should flag support
    assert res["is_sustained_low"] is True
    assert "care_response" in res or "partner" in res["reply"].lower()
    assert res["_meta"]["ui"]["resourceUri"] == "ui://ma/mood-trend-card"


def test_partner_tasks_workflow():
    # Assign
    assigned = partner_tasks_tool("assign", "Pick up vitamin D drops", "Alex")
    assert "Pick up vitamin D drops" in assigned["reply"]
    task_id = assigned.get("id")

    # List
    listing = partner_tasks_tool("list")
    assert "Pick up vitamin D drops" in listing["reply"] or len(listing["tasks"]) > 0

    # Complete
    completed = partner_tasks_tool("complete", "vitamin D")
    assert "completed" in completed["reply"].lower()
