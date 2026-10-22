"""
Safety Layer for MA Voice Companion (Phase 2).
Provides:
1. Crisis and distress detection (self-harm, harm to baby, hopelessness).
2. Errs on the side of caution for negations ("I'm not going to hurt myself").
3. Distinguishes normal postpartum tiredness to avoid false alarms.
4. Generates warm, non-diagnostic care responses with India-specific helplines.
5. Strict medical non-advice guardrails.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
HELPLINES_PATH = os.path.join(CONFIG_DIR, "helplines.json")

# 1. Critical crisis patterns: self-harm, harming baby, wanting to end life
CRITICAL_DISTRESS_PATTERNS = [
    r"\bhurt (myself|the baby|her|him|my baby|my child)\b",
    r"\bharm (myself|the baby|her|him|my baby|my child)\b",
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bend it all\b",
    r"\bwant to die\b",
    r"\bwish (i was|i were) dead\b",
    r"\bdon'?t want to (live|be alive|be here)\b",
    r"\bbetter off without me\b",
    r"\bshake (the baby|her|him|my baby)\b",
    r"\bsuicid(e|al)\b",
]

# 2. Negations of self-harm or harm: Must NOT be brushed aside (err on caution)
NEGATION_CRISIS_PATTERNS = [
    r"\b(not|never|wouldn'?t|don'?t|won'?t)\s+(actually\s+)?(hurt|harm|kill)\s+(myself|the baby|her|him|my baby)\b",
    r"\bnot\s+going\s+to\s+(hurt|harm|kill)\s+(myself|the baby|her|him|my baby)\b",
    r"\bnot\s+suicidal\s+but\b",
    r"\bdon'?t\s+worry\s+i\s+won'?t\s+do\s+anything\s+stupid\b",
    r"\bi('?m|\s+am)\s+not\s+(gonna|going to)\s+do\s+anything\s+(crazy|stupid|harmful)\b",
]

# 3. Postpartum despair and hopelessness
HOPELESSNESS_PATTERNS = [
    r"\bcan'?t do this anymore\b",
    r"\bcan'?t take this anymore\b",
    r"\bhopeless\b",
    r"\bworthless\b",
    r"\bfailing (as a mom|as a mother|her|him|my baby)\b",
    r"\bterrible mother\b",
    r"\bbad mother\b",
    r"\bdrowning\b",
    r"\bunbearable\b",
    r"\bcrying all (day|night|time)\b",
    r"\bwant to disappear\b",
    r"\bgiving up\b",
    r"\bnever get better\b",
    r"\bregret (having|my) baby\b",
]

# 4. Normal tiredness indicators (should NOT trigger false alarms when unaccompanied by crisis phrases)
NORMAL_TIREDNESS_PATTERNS = [
    r"\b(just|a bit|little|kind of|really)?\s*(tired|sleepy|drowsy|exhausted|worn out)\b",
    r"\bneed (coffee|a nap|some sleep|a break)\b",
    r"\blong night\b",
]

# 5. Medical question patterns: Require gentle redirection to doctor/midwife
MEDICAL_QUESTION_PATTERNS = [
    r"\b(dosage|dose|mg|ml)\s+of\b",
    r"\b(calpol|paracetamol|tylenol|ibuprofen|antibiotic|medicine|medication)\b",
    r"\b(fever of|high fever|coughing blood|rash on|breathing fast|infection)\b",
    r"\bis (it|this) safe to (give|take)\b",
    r"\bdiagnos(e|is)\b",
]


def load_helplines() -> List[Dict[str, Any]]:
    """Load helplines from config/helplines.json with safe fallbacks."""
    if os.path.exists(HELPLINES_PATH):
        try:
            with open(HELPLINES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("helplines", [])
        except Exception:
            pass
    # Fallback India helplines
    return [
        {
            "name": "Tele-MANAS (Govt. of India National Mental Health Helpline)",
            "phone": "14416 / 1800-891-4416",
            "hours": "24/7, Toll-Free",
            "description": "24/7 comprehensive psychological support in 20+ Indian languages."
        },
        {
            "name": "Vandrevala Foundation Helpline",
            "phone": "+91 9999 666 555",
            "hours": "24/7 Free & Confidential",
            "description": "Mental health and crisis intervention counseling."
        }
    ]


def format_helpline_string(helplines: List[Dict[str, Any]]) -> str:
    """Format the primary helplines for concise voice or text inclusion."""
    if not helplines:
        return "Tele-MANAS at 14416 or Vandrevala Foundation at +91 9999 666 555"
    primary = helplines[0]
    sec = helplines[2] if len(helplines) > 2 else (helplines[1] if len(helplines) > 1 else primary)
    return f"{primary['name']} at {primary['phone']} (toll-free) or {sec['name']} at {sec.get('phone', '')}"


def detect_medical_inquiry(text: str) -> Optional[str]:
    """Detect medical queries and return gentle non-diagnostic redirection."""
    text_lower = text.lower()
    for pattern in MEDICAL_QUESTION_PATTERNS:
        if re.search(pattern, text_lower):
            return (
                "Please check with your doctor, pediatrician, or midwife right away for medical questions or dosages. "
                "I cannot provide medical advice or diagnoses, but I am always here to support your daily rhythm."
            )
    return None


def detect_distress_keywords(text: str) -> Dict[str, Any]:
    """
    Examine text for critical crisis, negated crisis mentions, and hopelessness.
    Differentiates normal tiredness.
    """
    text_lower = text.lower()

    # 1. Check for negations first (e.g. "I'm not going to hurt myself")
    for pattern in NEGATION_CRISIS_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "matched": True,
                "severity": "negated_crisis",
                "pattern": pattern,
                "reason": "Mention of self-harm or harm with negation (erring on caution)"
            }

    # 2. Check for explicit critical self-harm or harm to baby
    for pattern in CRITICAL_DISTRESS_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "matched": True,
                "severity": "critical",
                "pattern": pattern,
                "reason": "Direct mention of self-harm, harming baby, or ending life"
            }

    # 3. Check for hopelessness / postpartum despair
    for pattern in HOPELESSNESS_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "matched": True,
                "severity": "hopelessness",
                "pattern": pattern,
                "reason": "Postpartum despair, feeling worthless, or inability to cope"
            }

    return {"matched": False, "severity": "none"}


def evaluate_distress(feeling: str, score: int, note: str = "") -> Dict[str, Any]:
    """
    Evaluate a single mood check-in for signs of serious distress.
    Returns care response and helpline details if distress is detected.
    """
    combined_text = f"{feeling} {note}".strip()
    kw_result = detect_distress_keywords(combined_text)
    helplines = load_helplines()
    hl_str = format_helpline_string(helplines)

    # CRITICAL or NEGATED CRISIS: immediate support first, ZERO cheerfulness
    if kw_result["severity"] in ("critical", "negated_crisis"):
        care_response = (
            f"I hear how much pain and weight you're carrying right now, and you do not have to be alone in this. "
            f"Please reach out right now to your doctor, midwife, or a trusted person, or call {hl_str}. "
            f"You and your baby matter so much, and compassionate support is ready for you right now."
        )
        return {
            "is_distress": True,
            "severity": kw_result["severity"],
            "reason": kw_result.get("reason", "Crisis indicator"),
            "care_response": care_response,
            "helplines": helplines
        }

    # HOPELESSNESS or SEVERE SCORE (score=1 with any negative expression)
    if kw_result["severity"] == "hopelessness" or (score == 1 and feeling.strip()):
        care_response = (
            f"I hear you, and what you are feeling is deeply real and heavy right now. "
            f"Please contact your doctor, midwife, or a trusted person today, or connect with {hl_str}. "
            f"You don't have to carry this exhaustion on your own, and asking for support is strength."
        )
        return {
            "is_distress": True,
            "severity": "hopelessness" if kw_result["severity"] == "hopelessness" else "score_1_distress",
            "reason": kw_result.get("reason", "Severe low score check-in"),
            "care_response": care_response,
            "helplines": helplines
        }

    # Normal tiredness (e.g. score 2-5 without crisis or despair phrases)
    return {"is_distress": False}


def evaluate_trend_distress(moods: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate a multi-day series of mood check-ins.
    Flags sustained low scores (3+ consecutive check-ins <= 2, or average <= 2.2).
    """
    if not moods:
        return {"is_distress": False}

    helplines = load_helplines()
    hl_str = format_helpline_string(helplines)

    # First check if any individual entry has critical or hopelessness keywords
    for m in moods:
        combined = f"{m.get('feeling', '')} {m.get('note', '')}"
        kw = detect_distress_keywords(combined)
        if kw["severity"] in ("critical", "negated_crisis"):
            return evaluate_distress(m.get("feeling", ""), m.get("score", 1), m.get("note", ""))

    scores = [m.get("score", 3) for m in moods]
    avg_score = round(sum(scores) / len(scores), 2)
    has_three_consecutive_low = len(scores) >= 3 and all(s <= 2 for s in scores[-3:])
    has_low_average = len(scores) >= 3 and avg_score <= 2.2

    if has_three_consecutive_low or has_low_average:
        care_response = (
            f"I notice your energy and spirits have felt very depleted over several days in a row. "
            f"Please share how you are feeling with your doctor, midwife, or a trusted person today, or call {hl_str}. "
            f"Sustained exhaustion and sadness is very real, and you deserve extra hands and care to hold you."
        )
        return {
            "is_distress": True,
            "severity": "sustained_low",
            "avg_score": avg_score,
            "consecutive_low": has_three_consecutive_low,
            "care_response": care_response,
            "helplines": helplines
        }

    return {"is_distress": False}
