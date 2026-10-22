"""
Seed script for MA Voice Companion.
Generates realistic 5-day demo history for:
- Mother: Sarah
- Baby: Maya (3 months old)
- Feeds (breast left/right, bottles)
- Sleep cycles (night stretches, naps)
- Gradual dip in mood (4 -> 4 -> 3 -> 2 -> 2) so trend_check flags it
- Partner support tasks
"""

from datetime import datetime, time, timedelta
import os
import sys

# Ensure server module directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import (
    add_feed,
    add_mood_checkin,
    add_sleep,
    get_connection,
    init_db,
    manage_partner_tasks_db,
)


def seed_database() -> None:
    print("🌱 Initializing SQLite database...")
    init_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clean previous demo records to allow clean re-seeding
    cursor.execute("DELETE FROM partner_tasks")
    cursor.execute("DELETE FROM mood_checkins")
    cursor.execute("DELETE FROM sleeps")
    cursor.execute("DELETE FROM feeds")
    cursor.execute("DELETE FROM babies")
    cursor.execute("DELETE FROM mothers")
    conn.commit()

    print("👩 Creating demo mother 'Sarah' and 3-month-old baby 'Maya'...")
    cursor.execute("INSERT INTO mothers (name) VALUES ('Sarah')")
    mother_id = cursor.lastrowid

    three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO babies (mother_id, name, birth_date) VALUES (?, 'Maya', ?)",
        (mother_id, three_months_ago)
    )
    baby_id = cursor.lastrowid
    conn.commit()
    conn.close()

    now = datetime.now()

    print("🍼 Seeding 5 days of realistic feeding, sleep, and mood history...")

    # Day 1 (4 days ago) - Good energy, stable sleep
    day1 = now - timedelta(days=4)
    add_feed(baby_id, "breast_left", 15, "good latch", logged_at=(day1.replace(hour=7, minute=15)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_right", 15, "satisfied", logged_at=(day1.replace(hour=10, minute=30)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "bottle", 120, "pumped milk", logged_at=(day1.replace(hour=14, minute=0)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_left", 20, "bedtime feed", logged_at=(day1.replace(hour=19, minute=30)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_right", 15, "night wake", logged_at=(day1.replace(hour=23, minute=45)).strftime("%Y-%m-%d %H:%M:%S"))

    add_sleep(baby_id, (day1.replace(hour=8, minute=30)).strftime("%Y-%m-%d %H:%M:%S"), (day1.replace(hour=10, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), 90, "morning nap")
    add_sleep(baby_id, (day1.replace(hour=12, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), (day1.replace(hour=13, minute=30)).strftime("%Y-%m-%d %H:%M:%S"), 90, "crib nap")
    add_sleep(baby_id, (day1.replace(hour=20, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), (day1.replace(hour=23, minute=30)).strftime("%Y-%m-%d %H:%M:%S"), 210, "first night stretch")
    add_mood_checkin(mother_id, "peaceful", 4, "Maya smiled at me during tummy time", logged_at=(day1.replace(hour=20, minute=30)).strftime("%Y-%m-%d %H:%M:%S"))

    # Day 2 (3 days ago) - Steady
    day2 = now - timedelta(days=3)
    add_feed(baby_id, "breast_left", 15, "morning nursing", logged_at=(day2.replace(hour=6, minute=45)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "bottle", 110, "formula", logged_at=(day2.replace(hour=10, minute=15)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_right", 15, "afternoon feed", logged_at=(day2.replace(hour=13, minute=45)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "bottle", 120, "evening bottle", logged_at=(day2.replace(hour=18, minute=30)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_left", 15, "dream feed", logged_at=(day2.replace(hour=22, minute=15)).strftime("%Y-%m-%d %H:%M:%S"))

    add_sleep(baby_id, (day2.replace(hour=8, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), (day2.replace(hour=9, minute=30)).strftime("%Y-%m-%d %H:%M:%S"), 90, "contact nap")
    add_sleep(baby_id, (day2.replace(hour=14, minute=30)).strftime("%Y-%m-%d %H:%M:%S"), (day2.replace(hour=16, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), 90, "stroller nap")
    add_sleep(baby_id, (day2.replace(hour=19, minute=30)).strftime("%Y-%m-%d %H:%M:%S"), (day2.replace(hour=22, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), 150, "evening sleep")
    add_mood_checkin(mother_id, "managing well", 4, "Partner made coffee, feeling supported", logged_at=(day2.replace(hour=19, minute=0)).strftime("%Y-%m-%d %H:%M:%S"))

    # Day 3 (2 days ago) - Frequent night waking starts, tiredness creeps in (Score 2)
    day3 = now - timedelta(days=2)
    add_feed(baby_id, "breast_left", 20, "cluster feed", logged_at=(day3.replace(hour=2, minute=30)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_right", 15, "fussy morning", logged_at=(day3.replace(hour=7, minute=0)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "bottle", 90, "stopped early", logged_at=(day3.replace(hour=11, minute=30)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_left", 15, "", logged_at=(day3.replace(hour=15, minute=0)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "bottle", 100, "", logged_at=(day3.replace(hour=19, minute=0)).strftime("%Y-%m-%d %H:%M:%S"))

    add_sleep(baby_id, (day3.replace(hour=0, minute=30)).strftime("%Y-%m-%d %H:%M:%S"), (day3.replace(hour=2, minute=15)).strftime("%Y-%m-%d %H:%M:%S"), 105, "woke crying")
    add_sleep(baby_id, (day3.replace(hour=3, minute=30)).strftime("%Y-%m-%d %H:%M:%S"), (day3.replace(hour=6, minute=15)).strftime("%Y-%m-%d %H:%M:%S"), 165, "restless")
    add_sleep(baby_id, (day3.replace(hour=12, minute=30)).strftime("%Y-%m-%d %H:%M:%S"), (day3.replace(hour=13, minute=15)).strftime("%Y-%m-%d %H:%M:%S"), 45, "short nap")
    add_mood_checkin(mother_id, "tired and overwhelmed", 2, "Up twice in the night, body aches", logged_at=(day3.replace(hour=20, minute=0)).strftime("%Y-%m-%d %H:%M:%S"))

    # Day 4 (Yesterday) - Growth spurt, minimal sleep, low mood (Score 2)
    day4 = now - timedelta(days=1)
    add_feed(baby_id, "breast_left", 15, "", logged_at=(day4.replace(hour=1, minute=45)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_right", 20, "", logged_at=(day4.replace(hour=4, minute=15)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "bottle", 120, "", logged_at=(day4.replace(hour=8, minute=30)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_left", 15, "", logged_at=(day4.replace(hour=12, minute=0)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "bottle", 110, "", logged_at=(day4.replace(hour=16, minute=0)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "breast_right", 15, "", logged_at=(day4.replace(hour=20, minute=0)).strftime("%Y-%m-%d %H:%M:%S"))

    add_sleep(baby_id, (day4.replace(hour=2, minute=15)).strftime("%Y-%m-%d %H:%M:%S"), (day4.replace(hour=4, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), 105, "short stretch")
    add_sleep(baby_id, (day4.replace(hour=5, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), (day4.replace(hour=7, minute=15)).strftime("%Y-%m-%d %H:%M:%S"), 135, "woke up tired")
    add_sleep(baby_id, (day4.replace(hour=13, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), (day4.replace(hour=14, minute=0)).strftime("%Y-%m-%d %H:%M:%S"), 60, "nap")
    add_mood_checkin(mother_id, "overwhelmed and exhausted", 2, "Crying spells today, feel like I can't catch up on sleep", logged_at=(day4.replace(hour=21, minute=15)).strftime("%Y-%m-%d %H:%M:%S"))

    # Day 5 (Today) - Sustained low mood (Score 2) for trend_check demo
    day5_start = datetime.combine(now.date(), time(0, 30, 0))
    add_feed(baby_id, "breast_right", 20, "early nursing", logged_at=(day5_start + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"))
    add_feed(baby_id, "bottle", 120, "morning feed", logged_at=(day5_start + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"))

    add_sleep(baby_id, day5_start.strftime("%Y-%m-%d %H:%M:%S"), (day5_start + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), 120, "night sleep")
    add_mood_checkin(mother_id, "drained and crying", 2, "Barely slept, feeling very alone today", logged_at=(day5_start + timedelta(hours=1, minutes=15)).strftime("%Y-%m-%d %H:%M:%S"))

    print("🤝 Seeding partner support tasks...")
    manage_partner_tasks_db(mother_id, "assign", "Sterilize and prep evening bottles", "Alex (Partner)")
    manage_partner_tasks_db(mother_id, "assign", "Pick up size 2 diapers from store", "Alex (Partner)")
    manage_partner_tasks_db(mother_id, "assign", "Take 4:00 AM baby shift so mom can sleep", "Alex (Partner)")
    manage_partner_tasks_db(mother_id, "assign", "Fold washed baby onesies", "Alex (Partner)")
    manage_partner_tasks_db(mother_id, "complete", "Fold washed baby onesies")

    print("✅ Seed complete! Maya's rhythm, Sarah's mood dip, and partner tasks are ready.")


if __name__ == "__main__":
    seed_database()
