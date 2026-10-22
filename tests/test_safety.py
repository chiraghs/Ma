"""
Unit tests for Phase 2: Safety Layer for MA Voice Companion.
Tests:
1. Crisis phrases (direct self-harm, harming baby).
2. Negations ("I'm not going to hurt myself" treated with high caution).
3. Hopelessness & postpartum despair.
4. Normal tiredness (NO false alarm).
5. Trend-based triggers (sustained low scores over multiple days).
6. Presence of India-specific helplines (Tele-MANAS, Vandrevala Foundation) and doctor/midwife recommendation.
7. Medical non-advice guardrails (never diagnose, redirect dosages/symptoms to doctor/midwife).
"""

import os
import sys
import pytest

SERVER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server")
sys.path.insert(0, SERVER_PATH)

from safety import (
    detect_distress_keywords,
    detect_medical_inquiry,
    evaluate_distress,
    evaluate_trend_distress,
    load_helplines,
)
from tools import mood_checkin_tool, trend_check_tool


# -------------------------------------------------------------
# 1. Crisis Phrases (Direct Self-Harm / Harm to Baby)
# -------------------------------------------------------------

def test_crisis_phrase_direct_self_harm():
    res = evaluate_distress(feeling="desperate", score=1, note="I want to hurt myself")
    assert res["is_distress"] is True
    assert res["severity"] == "critical"
    assert "doctor" in res["care_response"].lower() or "midwife" in res["care_response"].lower()
    assert "14416" in res["care_response"] or "tele-manas" in res["care_response"].lower() or "9999 666 555" in res["care_response"]
    
    # Must never be cheerful or playful
    assert "yay" not in res["care_response"].lower()
    assert "great" not in res["care_response"].lower()
    assert "lovely" not in res["care_response"].lower()


def test_crisis_phrase_harm_to_baby():
    res = evaluate_distress(feeling="rage and tears", score=1, note="I feel like I want to shake the baby")
    assert res["is_distress"] is True
    assert res["severity"] == "critical"
    assert "reach out" in res["care_response"].lower()
    assert "doctor" in res["care_response"].lower() or "midwife" in res["care_response"].lower()


def test_crisis_phrase_want_to_die():
    res = evaluate_distress(feeling="empty", score=1, note="They would all be better off without me, I want to die")
    assert res["is_distress"] is True
    assert res["severity"] == "critical"


# -------------------------------------------------------------
# 2. Negations (Must Err on Side of Caution)
# -------------------------------------------------------------

def test_negation_self_harm_treated_with_caution():
    """
    Phrases like 'I'm not going to hurt myself' must not be brushed aside.
    The system must recognize distress and provide compassionate care resources.
    """
    res1 = evaluate_distress(feeling="numb", score=2, note="I'm not going to hurt myself, but I just feel so broken")
    assert res1["is_distress"] is True
    assert res1["severity"] == "negated_crisis"
    assert "care_response" in res1
    assert "doctor" in res1["care_response"].lower() or "midwife" in res1["care_response"].lower()

    res2 = evaluate_distress(feeling="overwhelmed", score=2, note="Don't worry I won't hurt the baby, just crying")
    assert res2["is_distress"] is True
    assert res2["severity"] == "negated_crisis"

    res3 = evaluate_distress(feeling="down", score=2, note="I'm not suicidal but everything is too dark")
    assert res3["is_distress"] is True


# -------------------------------------------------------------
# 3. Hopelessness & Postpartum Despair
# -------------------------------------------------------------

def test_hopelessness_and_despair():
    res = evaluate_distress(feeling="hopeless", score=2, note="I can't do this anymore, I'm a terrible mother")
    assert res["is_distress"] is True
    assert res["severity"] == "hopelessness"
    assert "care_response" in res
    assert "doctor" in res["care_response"].lower() or "midwife" in res["care_response"].lower()


def test_failing_as_a_mom():
    res = evaluate_distress(feeling="drowning", score=2, note="I am failing my baby every day")
    assert res["is_distress"] is True
    assert "care_response" in res


# -------------------------------------------------------------
# 4. Normal Tiredness (NO False Alarms)
# -------------------------------------------------------------

def test_normal_tiredness_no_false_alarm():
    """
    Routine newborn exhaustion must NOT trigger crisis mode.
    """
    # Case A: Normal tiredness with score 3
    res_a = evaluate_distress(feeling="tired", score=3, note="Up at 3am for a feed, ready for some coffee")
    assert res_a["is_distress"] is False

    # Case B: Sleepy with score 4
    res_b = evaluate_distress(feeling="sleepy", score=4, note="Baby took a 2 hour nap, feeling peaceful")
    assert res_b["is_distress"] is False

    # Case C: Just exhausted with score 3
    res_c = evaluate_distress(feeling="really exhausted", score=3, note="Long day of stroller walks and laundry")
    assert res_c["is_distress"] is False

    # Verify tool return for normal tired check-in
    tool_res = mood_checkin_tool(feeling="tired", score=3, note="Just a long day")
    assert "care_response" not in tool_res
    assert "tired" in tool_res["reply"].lower()


# -------------------------------------------------------------
# 5. Trend-Based Triggers
# -------------------------------------------------------------

def test_trend_distress_sustained_low_scores():
    """
    3 or more consecutive check-ins with score <= 2 must trigger proactive support.
    """
    low_moods = [
        {"feeling": "exhausted", "score": 2, "note": "crying spells"},
        {"feeling": "overwhelmed", "score": 2, "note": "body aches"},
        {"feeling": "drained", "score": 1, "note": "can't rest"},
    ]
    res = evaluate_trend_distress(low_moods)
    assert res["is_distress"] is True
    assert res["severity"] == "sustained_low"
    assert "care_response" in res
    assert "doctor" in res["care_response"].lower() or "midwife" in res["care_response"].lower()


def test_trend_distress_healthy_scores_no_alarm():
    """
    A stable series of moods should not trigger distress alarms.
    """
    steady_moods = [
        {"feeling": "peaceful", "score": 4, "note": ""},
        {"feeling": "managing well", "score": 4, "note": ""},
        {"feeling": "tired", "score": 3, "note": ""},
        {"feeling": "happy", "score": 5, "note": ""},
    ]
    res = evaluate_trend_distress(steady_moods)
    assert res["is_distress"] is False


# -------------------------------------------------------------
# 6. India Helplines Loaded & Present
# -------------------------------------------------------------

def test_india_helplines_configuration():
    helplines = load_helplines()
    assert len(helplines) >= 2
    
    names = [h["name"] for h in helplines]
    has_telemanas = any("Tele-MANAS" in n or "14416" in str(h.get("phone", "")) for h, n in zip(helplines, names))
    has_vandrevala = any("Vandrevala" in n or "9999 666 555" in str(h.get("phone", "")) for h, n in zip(helplines, names))
    
    assert has_telemanas, "Expected Tele-MANAS helpline in config"
    assert has_vandrevala, "Expected Vandrevala Foundation in config"


# -------------------------------------------------------------
# 7. Medical Non-Advice Guardrail
# -------------------------------------------------------------

def test_medical_guardrail_redirection():
    # Dosages
    med_query1 = detect_medical_inquiry("What is the dosage of calpol for a 3 month old?")
    assert med_query1 is not None
    assert "doctor" in med_query1.lower() or "midwife" in med_query1.lower()
    assert "dosage" not in med_query1.lower() or "cannot provide medical advice" in med_query1.lower()

    # Symptoms
    med_query2 = detect_medical_inquiry("Baby has high fever and breathing fast, is that dangerous?")
    assert med_query2 is not None
    assert "doctor" in med_query2.lower()

    # Non-medical baby question should not be blocked
    normal_query = detect_medical_inquiry("How many diapers do babies usually use in a week?")
    assert normal_query is None
