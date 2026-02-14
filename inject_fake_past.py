import sqlite3
import os
import uuid
from datetime import datetime, timedelta, timezone

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLUID_DB_PATH = os.path.join("gui", "fluid-calendar", "prisma", "dev.dbcd")

def inject_past_task():
    print("🕰️ Time Machine Started...")
    
    conn = sqlite3.connect(FLUID_DB_PATH)
    cursor = conn.cursor()
    
    # 1. Get Feed ID
    cursor.execute("SELECT id FROM CalendarFeed WHERE name = 'VibeOS' LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print("❌ VibeOS Feed nahi mila. Architect run karo pehle.")
        return
    feed_id = row[0]

    # 2. Create a Task from YESTERDAY (Jo miss ho gaya)
    # Yesterday 2 PM
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    yesterday = yesterday.replace(hour=14, minute=0, second=0)
    
    start_str = yesterday.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_str = (yesterday + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    fake_title = "VibeOS: Old Legacy Code Review"
    event_id = str(uuid.uuid4())

    cursor.execute('''
        INSERT INTO CalendarEvent (id, feedId, title, start, end, allDay, createdAt, updatedAt)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?)
    ''', (event_id, feed_id, fake_title, start_str, end_str, now_str, now_str))
    
    conn.commit()
    conn.close()
    print(f"✅ Ek nakli task 'Yesterday' mein daal diya: {fake_title}")
    print("👉 Ab 'python core/loader/backlog_manager.py' chalao!")

if __name__ == "__main__":
    inject_past_task()