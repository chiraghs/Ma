"""
Safety Layer for MA Voice Companion.
Detects distress, feelings of hopelessness, thoughts of self-harm or harming baby,
and triggers warm, compassionate care responses with configurable helplines.
Never provides medical diagnoses or dosages.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
HELPLINES_PATH = os.path.join(CONFIG_DIR, "helplines.json")

# Core keywords signaling urgent crisis or thoughts of self-harm / harming baby
CRITICAL_DISTRESS_KEYWORDS = [
    r"\bhurt (myself|the baby|her|him|my baby)\b",
    r"\bharm (myself|the baby|her|him|my baby)\b",
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bend it all\b",
    r"\bdon'?t want to be here\b",
    r"\bwant to disappear\b",
    r"\bwish i were dead\b",
    r"\bbetter off without me\b",
    r"\bshake (the baby|her|him)\b",
    r"\bdie\b",
    r"\bsuicid(e|al)\b",
]

# Secondary keywords signaling deep postpartum distress, despair, or exhaustion
POSTPARTUM_DISTRESS_KEYWORDS = [
    r"\bcan'?t do this anymore\b",
    r"\bhopeless\b",
    r"\bworthless\b",
    r"\bfailing (as a mom|her|him|my baby)\b",
    r"\bterrible mother\b",
    r"\bdrowning\b",
    r"\bunbearable\b",
    r"\bcrying all day\b",
    r"\bpanic attack\b",
    r"\bnever get better\b",
]


def load_helplines() -> List[Dict[str, Any]]:
    """Load configurable helplines from config/helplines.json."""
    if os.path.exists(HELPLINES_PATH):
        try:
            with open(HELPLINES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("helplines", [])
        except Exception:
            pass
    # Fallback default emergency hotlines
    return [
        {
            "name": "National Maternal Mental Health Hotline",
            "phone": "1-833-852-6262",
            "text": "1-833-852-6262",
            "description": "24/7 free, confidential support for new moms."
        },
        {
            "name": "988 Suicide & Crisis Lifeline",
            "phone": "988",
            "text": "988",
            "description": "24/7 immediate crisis support."
        }
    ]


def detect_distress_keywords(text: str) -> Dict[str, Any]:
    """Scan text for critical and postpartum distress keywords."""
    text_lower = text.lower()
    
    # Check critical self-harm or harm to baby
    for pattern in CRITICAL_DISTRESS_KEYWORDS:
        if re.search(pattern, text_lower):
            return {
                "matched": True,
                "severity": "critical",
                "pattern": pattern
            }
            
    # Check secondary postpartum despair keywords
    for pattern in POSTPARTUM_DISTRESS_KEYWORDS:
        if re.search(pattern, text_lower):
            return {
                "matched": True,
                "severity": "high",
                "pattern": pattern
            }
            
    return {"matched": False, "severity": "none"}


def evaluate_distress(feeling: str, score: int, note: str = "") -> Dict[str, Any]:
    """
    Evaluate a single mood check-in for signs of serious distress.
    Returns care response and helpline details if distress is detected.
    """
    combined_text = f"{feeling} {note}".strip()
    keyword_result = detect_distress_keywords(combined_text)
    
    is_critical = keyword_result["severity"] == "critical"
    is_high_keyword = keyword_result["severity"] == "high"
    is_severe_score = score == 1

    if is_critical:
        helplines = load_helplines()
        mama_line = helplines[0]["phone"] if helplines else "1-833-852-6262"
        care_response = (
            f"I hear how much pain you're in right now, and you do not have to carry this alone. "
            f"Please reach out right now to a doctor, midwife, or call/text the Maternal Mental Health Hotline at {mama_line} or 988. "
            f"You and your baby matter so much, and there is caring support ready for you."
        )
        return {
            "is_distress": True,
            "severity": "critical",
            "care_response": care_response,
            "helplines": helplines
        }

    if is_high_keyword or (is_severe_score and keyword_result["matched"]):
        helplines = load_helplines()
        mama_line = helplines[0]["phone"] if helplines else "1-833-852-6262"
        care_response = (
            f"I'm listening, and I want you to know how deeply valid and heavy this feels right now. "
            f"Please consider checking in with your doctor, midwife, or calling the Maternal Mental Health line at {mama_line} today. "
            f"You deserve warmth, care, and extra hands to hold you."
        )
        return {
            "is_distress": True,
            "severity": "high",
            "care_response": care_response,
            "helplines": helplines
        }

    return {"is_distress": False}


def evaluate_trend_distress(moods: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate a historical list of mood check-ins for sustained severe distress.
    """
    if not moods:
        return {"is_distress": False}

    # Check any recent check-in for critical keywords
    for m in moods:
        combined = f"{m.get('feeling', '')} {m.get('note', '')}"
        kw = detect_distress_keywords(combined)
        if kw["severity"] == "critical":
            return evaluate_distress(m.get("feeling", ""), m.get("score", 1), m.get("note", ""))

    # Check for sustained low scores: 3 or more consecutive checkins with score <= 2
    scores = [m.get("score", 3) for m in moods]
    if len(scores) >= 3 and all(s <= 2 for s in scores[-3:]):
        helplines = load_helplines()
        mama_line = helplines[0]["phone"] if helplines else "1-833-852-6262"
        care_response = (
            f"I notice your energy and spirits have felt very depleted over several days in a row. "
            f"Please share how you are feeling with your doctor, midwife, or call the 24/7 Maternal Health Hotline at {mama_line}. "
            f"Having sustained exhaustion or sadness is common, and you don't have to carry it on your own."
        )
        return {
            "is_distress": True,
            "severity": "sustained_low",
            "care_response": care_response,
            "helplines": helplines
        }

    return {"is_distress": False}
