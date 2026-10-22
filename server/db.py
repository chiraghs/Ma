"""
Database layer for MA Voice Companion using SQLite.
Stores mothers, babies, feeds, sleeps, mood_checkins, and partner_tasks.
All data is stored locally for maximum privacy.
"""

from datetime import datetime, timedelta
import os
import sqlite3
from typing import Any, Dict, List, Optional

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DB_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "ma.db")


def get_connection() -> sqlite3.Connection:
    """Ensure data directory exists and return a SQLite connection."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite schema for mothers, babies, feeds, sleeps, moods, and tasks."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS mothers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        timezone TEXT DEFAULT 'UTC',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS babies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mother_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        birth_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mother_id) REFERENCES mothers(id)
    );

    CREATE TABLE IF NOT EXISTS feeds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        baby_id INTEGER NOT NULL,
        feed_type TEXT NOT NULL CHECK(feed_type IN ('breast_left', 'breast_right', 'bottle', 'solid')),
        minutes_or_ml INTEGER NOT NULL,
        note TEXT DEFAULT '',
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (baby_id) REFERENCES babies(id)
    );

    CREATE TABLE IF NOT EXISTS sleeps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        baby_id INTEGER NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        duration_minutes INTEGER NOT NULL,
        note TEXT DEFAULT '',
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (baby_id) REFERENCES babies(id)
    );

    CREATE TABLE IF NOT EXISTS mood_checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mother_id INTEGER NOT NULL,
        feeling TEXT NOT NULL,
        score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
        note TEXT DEFAULT '',
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mother_id) REFERENCES mothers(id)
    );

    CREATE TABLE IF NOT EXISTS partner_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mother_id INTEGER NOT NULL,
        task TEXT NOT NULL,
        assignee TEXT NOT NULL DEFAULT 'Partner',
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'completed')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (mother_id) REFERENCES mothers(id)
    );
    """)

    conn.commit()
    conn.close()


# Database helper methods
def get_default_mother_and_baby() -> tuple[int, int]:
    """Return default mother_id and baby_id or create default if none exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM mothers LIMIT 1")
    row = cursor.fetchone()
    if row:
        mother_id = row["id"]
        cursor.execute("SELECT id FROM babies WHERE mother_id = ? LIMIT 1", (mother_id,))
        b_row = cursor.fetchone()
        baby_id = b_row["id"] if b_row else 1
        conn.close()
        return mother_id, baby_id

    # Create default demo mother & baby
    cursor.execute("INSERT INTO mothers (name) VALUES ('Sarah')")
    mother_id = cursor.lastrowid
    cursor.execute("INSERT INTO babies (mother_id, name, birth_date) VALUES (?, 'Maya', date('now', '-3 months'))", (mother_id,))
    baby_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return mother_id, baby_id


def add_feed(baby_id: int, feed_type: str, minutes_or_ml: int, note: str = "", logged_at: Optional[str] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    if logged_at:
        cursor.execute(
            "INSERT INTO feeds (baby_id, feed_type, minutes_or_ml, note, logged_at) VALUES (?, ?, ?, ?, ?)",
            (baby_id, feed_type, minutes_or_ml, note, logged_at)
        )
    else:
        cursor.execute(
            "INSERT INTO feeds (baby_id, feed_type, minutes_or_ml, note) VALUES (?, ?, ?, ?)",
            (baby_id, feed_type, minutes_or_ml, note)
        )
    feed_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return feed_id


def add_sleep(baby_id: int, start_time: str, end_time: str, duration_minutes: int, note: str = "", logged_at: Optional[str] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    if logged_at:
        cursor.execute(
            "INSERT INTO sleeps (baby_id, start_time, end_time, duration_minutes, note, logged_at) VALUES (?, ?, ?, ?, ?, ?)",
            (baby_id, start_time, end_time, duration_minutes, note, logged_at)
        )
    else:
        cursor.execute(
            "INSERT INTO sleeps (baby_id, start_time, end_time, duration_minutes, note) VALUES (?, ?, ?, ?, ?)",
            (baby_id, start_time, end_time, duration_minutes, note)
        )
    sleep_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sleep_id


def add_mood_checkin(mother_id: int, feeling: str, score: int, note: str = "", logged_at: Optional[str] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    if logged_at:
        cursor.execute(
            "INSERT INTO mood_checkins (mother_id, feeling, score, note, logged_at) VALUES (?, ?, ?, ?, ?)",
            (mother_id, feeling, score, note, logged_at)
        )
    else:
        cursor.execute(
            "INSERT INTO mood_checkins (mother_id, feeling, score, note) VALUES (?, ?, ?, ?)",
            (mother_id, feeling, score, note)
        )
    checkin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return checkin_id


def get_feeds_in_range(baby_id: int, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM feeds WHERE baby_id = ? AND logged_at BETWEEN ? AND ? ORDER BY logged_at ASC",
        (baby_id, start_dt.strftime("%Y-%m-%d %H:%M:%S"), end_dt.strftime("%Y-%m-%d %H:%M:%S"))
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_sleeps_in_range(baby_id: int, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sleeps WHERE baby_id = ? AND start_time >= ? AND start_time <= ? ORDER BY start_time ASC",
        (baby_id, start_dt.strftime("%Y-%m-%d %H:%M:%S"), end_dt.strftime("%Y-%m-%d %H:%M:%S"))
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_moods_for_days(mother_id: int, days: int = 7) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    start_dt = datetime.now() - timedelta(days=days)
    cursor.execute(
        "SELECT * FROM mood_checkins WHERE mother_id = ? AND logged_at >= ? ORDER BY logged_at ASC",
        (mother_id, start_dt.strftime("%Y-%m-%d %H:%M:%S"))
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def manage_partner_tasks_db(mother_id: int, action: str, task: str = "", assignee: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    action = action.lower()

    if action == "assign":
        if not task:
            conn.close()
            return {"error": "Task description is required to assign a task."}
        assignee_name = assignee.strip() if assignee else "Partner"
        cursor.execute(
            "INSERT INTO partner_tasks (mother_id, task, assignee, status) VALUES (?, ?, ?, 'pending')",
            (mother_id, task, assignee_name)
        )
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"action": "assigned", "id": task_id, "task": task, "assignee": assignee_name, "status": "pending"}

    elif action == "complete":
        if not task:
            conn.close()
            return {"error": "Task name or ID required to complete."}
        
        # Check if task is an ID or description
        if task.isdigit():
            cursor.execute(
                "UPDATE partner_tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ? AND mother_id = ?",
                (int(task), mother_id)
            )
        else:
            cursor.execute(
                "UPDATE partner_tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE task LIKE ? AND mother_id = ? AND status = 'pending'",
                (f"%{task}%", mother_id)
            )
        updated = cursor.rowcount
        conn.commit()
        conn.close()
        return {"action": "completed", "matched_count": updated, "task_query": task}

    else:  # list
        cursor.execute(
            "SELECT id, task, assignee, status, created_at, completed_at FROM partner_tasks WHERE mother_id = ? ORDER BY status DESC, created_at DESC",
            (mother_id,)
        )
        tasks = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return {"action": "list", "tasks": tasks}
