import sys
import os
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# --- PATH SETUP ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- IMPORTS FROM BRAIN ---
try:
    from core.solver.engine import solve_schedule
except ImportError:
    def solve_schedule(tasks, day_name): return []

app = FastAPI(title="VibeOS 2026 API", version="IST.Fixed")

# --- DATABASE PATHS ---
BRAIN_DB_PATH = os.path.join("data", "vibeos.db")
FLUID_DB_PATH = os.path.join("gui", "fluid-calendar", "prisma", "dev.dbcd") 

# --- DATA MODELS ---
class TaskItem(BaseModel):
    id: Optional[int] = None
    name: str
    category: str = "Any"
    duration: int = 60

class ScheduleRequest(BaseModel):
    day: str = "Monday" 
    tasks: List[TaskItem]

# --- ROUTES ---
@app.get("/")
def health_check():
    return {"status": "Online", "mode": "IST Timezone Fixed 🇮🇳"}

@app.post("/plan_my_day")
def plan_day(request: ScheduleRequest):
    print(f"📥 Planning for: {request.day}...")
    try:
        task_list = [{"id": t.id if t.id else idx + 1, "name": t.name, "duration": t.duration, "category": t.category} for idx, t in enumerate(request.tasks)]

        schedule = solve_schedule(task_list, day_name=request.day)
        if "error" in schedule: return {"status": "failed", "message": schedule["error"]}

        save_to_brain_db(request.day, schedule)
        sync_to_fluid_calendar(request.day, schedule)
            
        return {"status": "success", "schedule": schedule, "message": "Synced to Fluid Calendar (IST Adjusted) ✅"}
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- HELPER FUNCTIONS ---
def save_to_brain_db(day, schedule):
    try:
        conn = sqlite3.connect(BRAIN_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedule WHERE day_date = ?", (day,))
        for item in schedule:
            cursor.execute('INSERT INTO schedule (task_id, day_date, start_time, category, end_time) VALUES (?, ?, ?, ?, ?)', 
                           (item['id'], day, item['start'], item['category'], "TBD"))
        conn.commit()
        conn.close()
    except Exception as e: print(f"⚠️ Brain DB Error: {e}")

def get_date_object(day_str):
    today = datetime.now()
    try:
        return datetime.strptime(day_str, "%Y-%m-%d")
    except ValueError: pass
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day_str in days:
        target_idx = days.index(day_str)
        current_idx = today.weekday()
        days_ahead = target_idx - current_idx
        if days_ahead <= 0: days_ahead += 7 
        return today + timedelta(days=days_ahead)
    return today 

# --- 🔥 THE FIX: IST to UTC CONVERTER ---
def to_utc_iso(dt_local):
    """
    Humara Local Time (IST) 09:00 hai.
    Browser usme +5:30 add karta hai.
    Isliye hum pehle hi -5:30 kar dete hain taaki balance ho jaye.
    09:00 - 5:30 = 03:30 sent to DB
    Browser: 03:30 + 5:30 = 09:00 displayed. Magic! ✨
    """
    dt_utc = dt_local - timedelta(hours=5, minutes=30)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def to_iso_simple(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def sync_to_fluid_calendar(day_str, schedule):
    print(f"🌊 Syncing to Fluid Calendar (IST Mode)...")
    if not os.path.exists(FLUID_DB_PATH):
        print(f"❌ Error: Fluid DB NOT FOUND")
        return

    try:
        conn = sqlite3.connect(FLUID_DB_PATH)
        cursor = conn.cursor()

        # A. Find User
        cursor.execute("SELECT id FROM User LIMIT 1")
        user_row = cursor.fetchone()
        if not user_row: return
        user_id = user_row[0]

        # B. Get/Create Feed
        cursor.execute("SELECT id FROM CalendarFeed WHERE name = 'VibeOS' AND userId = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            feed_id = row[0]
        else:
            feed_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO CalendarFeed (id, name, type, enabled, createdAt, updatedAt, userId)
                VALUES (?, 'VibeOS', 'LOCAL', 1, ?, ?, ?)
            ''', (feed_id, to_iso_simple(datetime.utcnow()), to_iso_simple(datetime.utcnow()), user_id))

        # C. Insert Events
        target_date = get_date_object(day_str)
        date_prefix = target_date.strftime("%Y-%m-%d")
        
        # Cleanup old events for this specific day to avoid duplicates
        # (Converting target date to epoch MS for query range is complex in SQLite, skipping for now)

        count = 0
        for task in schedule:
            event_id = str(uuid.uuid4())
            start_dt = datetime.strptime(f"{date_prefix} {task['start']}", "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=task['duration'])
            
            # 🔥 FIX: Using to_utc_iso to subtract 5.5 hours
            cursor.execute('''
                INSERT INTO CalendarEvent (
                    id, feedId, title, start, end, 
                    allDay, createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            ''', (
                event_id, 
                feed_id, 
                f"{task['name']} ({task['category']})", 
                to_utc_iso(start_dt),   # <--- -5.5 Hours
                to_utc_iso(end_dt),     # <--- -5.5 Hours
                to_iso_simple(datetime.utcnow()),
                to_iso_simple(datetime.utcnow())
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"✅ Synced {count} events (IST Corrected) to Fluid Calendar!")

    except Exception as e:
        print(f"❌ Fluid Sync Error: {e}")