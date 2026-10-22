"""
Core MCP Tools for MA Voice Companion.
Implements typed, well-documented tools with MCP Apps (_meta.ui) metadata linkage.
"""

from datetime import datetime, time, timedelta
import re
from typing import Any, Dict, Literal, Optional
from dateutil import parser as dt_parser

from db import (
    add_feed,
    add_mood_checkin,
    add_sleep,
    get_default_mother_and_baby,
    get_feeds_in_range,
    get_moods_for_days,
    get_sleeps_in_range,
    manage_partner_tasks_db,
)

FeedType = Literal["breast_left", "breast_right", "bottle", "solid"]
PeriodType = Literal["last_night", "today", "yesterday", "week"]
TaskAction = Literal["assign", "list", "complete"]


def parse_natural_time(time_str: str, reference_date: Optional[datetime] = None) -> datetime:
    """
    Parse a natural time string like '1am', '2:30pm', '10pm', 'now', or 'yesterday 11pm'
    into an absolute datetime object.
    """
    time_str = time_str.strip().lower()
    ref = reference_date or datetime.now()

    if time_str == "now":
        return ref

    # Handle relative hours/minutes like "2 hours ago", "45 mins ago"
    rel_match = re.match(r"^(\d+)\s*(hour|hr|minute|min)s?\s*ago$", time_str)
    if rel_match:
        qty = int(rel_match.group(1))
        unit = rel_match.group(2)
        if "hour" in unit or "hr" in unit:
            return ref - timedelta(hours=qty)
        else:
            return ref - timedelta(minutes=qty)

    # Check for "yesterday" prefix
    is_yesterday = "yesterday" in time_str
    cleaned_str = time_str.replace("yesterday", "").strip()

    # Normalise bare numbers like '1' or '10' without am/pm
    if cleaned_str.isdigit():
        val = int(cleaned_str)
        cleaned_str = f"{val}:00"

    try:
        # Zero out minutes and seconds on default ref so '1pm' resolves to 1:00 PM, not 1:MM PM
        clean_ref = ref.replace(minute=0, second=0, microsecond=0)
        parsed = dt_parser.parse(cleaned_str, default=clean_ref)
        if is_yesterday:
            parsed = parsed - timedelta(days=1)
        return parsed
    except Exception:
        # Fallback to current time if unparseable
        return ref


def log_feed_tool(
    feed_type: FeedType,
    minutes_or_ml: int,
    note: str = ""
) -> Dict[str, Any]:
    """
    Log a baby feeding event (nursing, bottle, or solids).
    
    Args:
        feed_type: Type of feed ('breast_left', 'breast_right', 'bottle', 'solid')
        minutes_or_ml: Duration in minutes for nursing, or amount in ml for bottle/solids
        note: Optional extra details (e.g. 'burped well', 'formula', 'pumped milk')
        
    Returns:
        Confirmation message and feed record.
    """
    mother_id, baby_id = get_default_mother_and_baby()
    feed_id = add_feed(baby_id, feed_type, minutes_or_ml, note)

    unit = "minutes" if "breast" in feed_type else "ml"
    type_display = feed_type.replace("_", " ")
    
    reply = f"Logged {minutes_or_ml} {unit} of {type_display} for Maya."
    
    return {
        "reply": reply,
        "feed_id": feed_id,
        "feed_type": feed_type,
        "amount": minutes_or_ml,
        "unit": unit,
        "_meta": {
            "ui": {
                "resourceUri": "ui://ma/baby-summary-card",
                "visibility": ["model", "app"]
            }
        }
    }


def log_sleep_tool(
    start: str,
    end: str,
    note: str = ""
) -> Dict[str, Any]:
    """
    Log a baby sleep interval or nap.
    
    Args:
        start: Start time (natural format, e.g. '1pm', '10:30pm', '2 hours ago')
        end: End time (e.g. '2:15pm', 'now', '7am')
        note: Optional context (e.g. 'crib sleep', 'contact nap', 'fussy at start')
        
    Returns:
        Confirmation message and sleep duration details.
    """
    mother_id, baby_id = get_default_mother_and_baby()
    
    start_dt = parse_natural_time(start)
    end_dt = parse_natural_time(end)
    
    # If end is earlier than start on the same day (e.g. 10pm to 2am), shift end to next day
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
        
    duration_mins = max(1, int((end_dt - start_dt).total_seconds() / 60))
    hours = duration_mins // 60
    mins = duration_mins % 60
    
    duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"
    
    sleep_id = add_sleep(
        baby_id=baby_id,
        start_time=start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        end_time=end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        duration_minutes=duration_mins,
        note=note
    )
    
    reply = f"Logged Maya's sleep from {start_dt.strftime('%I:%M %p').lstrip('0')} to {end_dt.strftime('%I:%M %p').lstrip('0')} ({duration_str})."
    
    return {
        "reply": reply,
        "sleep_id": sleep_id,
        "duration_minutes": duration_mins,
        "duration_display": duration_str,
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "_meta": {
            "ui": {
                "resourceUri": "ui://ma/baby-summary-card",
                "visibility": ["model", "app"]
            }
        }
    }


def baby_summary_tool(period: PeriodType = "today") -> Dict[str, Any]:
    """
    Provide a warm, plain-language summary of baby's sleep and feeding rhythms.
    
    Args:
        period: Time window to summarize ('last_night', 'today', 'yesterday', 'week')
        
    Returns:
        Plain-language summary sentence and underlying rhythm metrics.
    """
    mother_id, baby_id = get_default_mother_and_baby()
    now = datetime.now()
    
    if period == "last_night":
        # Yesterday 8pm to Today 8am
        yesterday = now - timedelta(days=1)
        start_dt = datetime.combine(yesterday.date(), time(20, 0, 0))
        end_dt = datetime.combine(now.date(), time(8, 0, 0))
    elif period == "today":
        start_dt = datetime.combine(now.date(), time(0, 0, 0))
        end_dt = datetime.combine(now.date(), time(23, 59, 59))
    elif period == "yesterday":
        yesterday = now - timedelta(days=1)
        start_dt = datetime.combine(yesterday.date(), time(0, 0, 0))
        end_dt = datetime.combine(yesterday.date(), time(23, 59, 59))
    else:  # week
        start_dt = now - timedelta(days=7)
        end_dt = now
        
    feeds = get_feeds_in_range(baby_id, start_dt, end_dt)
    sleeps = get_sleeps_in_range(baby_id, start_dt, end_dt)
    
    total_feed_count = len(feeds)
    total_sleep_mins = sum(s.get("duration_minutes", 0) for s in sleeps)
    sleep_hrs = round(total_sleep_mins / 60, 1)
    
    # Find longest stretch of sleep
    longest_sleep_mins = max([s.get("duration_minutes", 0) for s in sleeps], default=0)
    longest_hrs = round(longest_sleep_mins / 60, 1)
    
    period_title = period.replace("_", " ")
    
    if total_feed_count == 0 and len(sleeps) == 0:
        summary_text = f"No events recorded yet for {period_title}."
    else:
        summary_text = (
            f"For {period_title}, Maya had {total_feed_count} feed{'s' if total_feed_count != 1 else ''} "
            f"and slept {sleep_hrs} hours total"
        )
        if longest_hrs > 0:
            summary_text += f", with a longest stretch of {longest_hrs} hours."
        else:
            summary_text += "."
            
    return {
        "reply": summary_text,
        "period": period,
        "total_feeds": total_feed_count,
        "total_sleep_hours": sleep_hrs,
        "longest_stretch_hours": longest_hrs,
        "feeds_list": feeds,
        "sleeps_list": sleeps,
        "_meta": {
            "ui": {
                "resourceUri": "ui://ma/baby-summary-card",
                "visibility": ["model", "app"]
            }
        }
    }


def mood_checkin_tool(feeling: str, score: int, note: str = "") -> Dict[str, Any]:
    """
    Record mother's emotional well-being check-in with empathetic acknowledgment.
    
    Args:
        feeling: How mom describes feeling (e.g. 'exhausted', 'calm', 'overwhelmed', 'peaceful')
        score: Rating from 1 (very depleted/struggling) to 5 (energized/peaceful)
        note: Optional extra thoughts or reflections
        
    Returns:
        Warm, non-judgmental acknowledgment and support prompt.
    """
    mother_id, baby_id = get_default_mother_and_baby()
    score = max(1, min(5, score))
    checkin_id = add_mood_checkin(mother_id, feeling, score, note)
    
    # We will hook this into safety layer in Phase 2
    from safety import evaluate_distress
    safety_result = evaluate_distress(feeling=feeling, score=score, note=note)
    if safety_result.get("is_distress"):
        return {
            "reply": safety_result["care_response"],
            "checkin_id": checkin_id,
            "feeling": feeling,
            "score": score,
            "care_response": safety_result["care_response"],
            "helplines": safety_result.get("helplines", []),
            "_meta": {
                "ui": {
                    "resourceUri": "ui://ma/mood-trend-card",
                    "visibility": ["model", "app"]
                }
            }
        }

    # Standard warm, empathetic companion acknowledgment
    if score <= 2:
        reply = f"Thank you for sharing that with me. It is completely okay to feel {feeling.lower()}—you're doing so much every single hour."
    elif score == 3:
        reply = f"I hear you. Feeling {feeling.lower()} is a gentle place to pause and take one quiet breath."
    else:
        reply = f"I'm glad you're feeling {feeling.lower()} today. Soak in this lovely moment."

    return {
        "reply": reply,
        "checkin_id": checkin_id,
        "feeling": feeling,
        "score": score,
        "_meta": {
            "ui": {
                "resourceUri": "ui://ma/mood-trend-card",
                "visibility": ["model", "app"]
            }
        }
    }


def trend_check_tool(days: int = 7) -> Dict[str, Any]:
    """
    Analyze recent mood and rest patterns over several days to offer proactive support.
    
    Args:
        days: Number of past days to analyze (default: 7)
        
    Returns:
        Supportive observation, average mood score, and practical partner suggestions.
    """
    mother_id, baby_id = get_default_mother_and_baby()
    moods = get_moods_for_days(mother_id, days)
    
    from safety import evaluate_trend_distress
    trend_safety = evaluate_trend_distress(moods)
    if trend_safety.get("is_distress"):
        return {
            "reply": trend_safety["care_response"],
            "care_response": trend_safety["care_response"],
            "helplines": trend_safety.get("helplines", []),
            "is_sustained_low": True,
            "severity": trend_safety.get("severity", "sustained_low"),
            "_meta": {
                "ui": {
                    "resourceUri": "ui://ma/mood-trend-card",
                    "visibility": ["model", "app"]
                }
            }
        }

    if not moods:
        return {
            "reply": "We don't have enough check-ins yet to see a trend. How are you feeling right now?",
            "trend": "insufficient_data"
        }
        
    scores = [m["score"] for m in moods]
    avg_score = round(sum(scores) / len(scores), 1)
    recent_feelings = [m["feeling"].lower() for m in moods[-3:]]
    
    # Detect sustained low mood (avg <= 2.2 or last 3 check-ins <= 2)
    is_sustained_low = (avg_score <= 2.2) or (len(scores) >= 3 and all(s <= 2 for s in scores[-3:]))
    
    if is_sustained_low:
        suggestion = "You've been holding a lot of weight over these past few days. Would you like me to ask your partner to take the next feed?"
    elif avg_score >= 3.8:
        suggestion = "Your rhythm over the past week has felt steady and gentle. You're doing wonderful work."
    else:
        suggestion = "You're moving through a busy patch with ups and downs. Remember you can ask for help whenever you need it."
        
    return {
        "reply": suggestion,
        "avg_score": avg_score,
        "checkins_analyzed": len(moods),
        "is_sustained_low": is_sustained_low,
        "recent_feelings": recent_feelings,
        "_meta": {
            "ui": {
                "resourceUri": "ui://ma/mood-trend-card",
                "visibility": ["model", "app"]
            }
        }
    }


def partner_tasks_tool(
    action: TaskAction = "list",
    task: str = "",
    assignee: str = ""
) -> Dict[str, Any]:
    """
    Coordinate and balance family support tasks so mom isn't doing everything alone.
    
    Args:
        action: 'assign', 'list', or 'complete'
        task: Description of task or task ID to complete
        assignee: Name of the person helping (defaults to 'Partner')
        
    Returns:
        Status of the task board or update confirmation.
    """
    mother_id, baby_id = get_default_mother_and_baby()
    res = manage_partner_tasks_db(mother_id, action, task, assignee)
    
    if action == "assign":
        reply = f"Added '{task}' to {res.get('assignee', 'partner')}'s tasks."
    elif action == "complete":
        reply = f"Marked task completed. Great teamwork!"
    else:
        tasks = res.get("tasks", [])
        pending = [t for t in tasks if t["status"] == "pending"]
        if pending:
            task_names = ", ".join([t["task"] for t in pending[:3]])
            reply = f"There are {len(pending)} open tasks for your partner: {task_names}."
        else:
            reply = "All partner tasks are caught up right now."
            
    res["reply"] = reply
    res["_meta"] = {
        "ui": {
            "resourceUri": "ui://ma/partner-tasks-card",
            "visibility": ["model", "app"]
        }
    }
    return res
