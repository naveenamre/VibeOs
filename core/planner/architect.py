import sys
import os
import json
import sqlite3
import uuid
import glob
from datetime import datetime, timedelta, timezone

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)  # Ensure core modules are discoverable

DATA_DIR = os.path.join(BASE_DIR, "data")
INPUTS_DIR = os.path.join(DATA_DIR, "inputs")
FLUID_DB_PATH = os.path.join(BASE_DIR, "gui", "fluid-calendar", "prisma", "dev.dbcd")

# --- IMPORT OPTIMIZER ---
try:
    from core.solver.optimizer import VibeOptimizer
except ImportError:
    print("❌ Error: Could not import VibeOptimizer. Make sure 'core/solver/optimizer.py' exists.")
    sys.exit(1)

# --- SMART LOADERS ---
def load_week_template():
    path = os.path.join(DATA_DIR, "week_template.json")
    if not os.path.exists(path): return {}
    with open(path, "r") as f: return json.load(f)

def load_all_inputs():
    master_syllabus = []
    if not os.path.exists(INPUTS_DIR):
        os.makedirs(INPUTS_DIR)
        return []

    json_files = glob.glob(os.path.join(INPUTS_DIR, "*.json"))
    if not json_files: return []

    print(f"📂 Found {len(json_files)} input files...")
    for file_path in json_files:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list): master_syllabus.extend(data)
                elif isinstance(data, dict): master_syllabus.append(data)
        except Exception as e:
            print(f"   ❌ Error loading {os.path.basename(file_path)}: {e}")
    return master_syllabus

def get_db_connection():
    return sqlite3.connect(FLUID_DB_PATH)

# --- DATE HELPERS ---
def to_utc_iso(dt_local):
    """IST to UTC conversion for DB storage (-5:30)"""
    # Local time se 5:30 ghante ghatao taaki Calendar par sahi dikhe
    dt_utc = dt_local - timedelta(hours=5, minutes=30)
    # Use timezone-aware UTC object
    return dt_utc.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def to_iso_now():
    """Current UTC time in ISO format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def flatten_week_template_to_slots(week_template, start_date, days_ahead=14):
    """
    Template (Mon/Tue...) ko Actual Date Slots (2026-02-14 09:00...) mein convert karta hai.
    """
    slots = []
    current = start_date
    for _ in range(days_ahead):
        day_name = current.strftime("%A")
        date_str = current.strftime("%Y-%m-%d")
        
        if day_name in week_template:
            for s in week_template[day_name]:
                # Parse Start Time
                try:
                    start_dt = datetime.strptime(f"{date_str} {s['start']}", "%Y-%m-%d %H:%M")
                    end_dt = start_dt + timedelta(minutes=s['duration'])
                    
                    slots.append({
                        "start": start_dt,
                        "end": end_dt,
                        "category": s['category'],
                        "original_duration": s['duration']
                    })
                except ValueError:
                    print(f"⚠️ Invalid time format in template for {day_name}: {s['start']}")
                    
        current += timedelta(days=1)
    
    # Sort slots by time (Zaroori hai sequence ke liye)
    slots.sort(key=lambda x: x['start'])
    return slots

# --- THE ARCHITECT LOGIC ---
def distribute_syllabus():
    print("🏗️ Architect 3.0 (OR-Tools Integrated) Starting...")
    
    # 1. Load Data
    raw_courses = load_all_inputs()
    week_template = load_week_template()
    
    if not raw_courses:
        print("❌ No inputs found! Add files to 'data/inputs/'")
        return

    # 2. Connect DB & Get Feed ID
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get User ID
    cursor.execute("SELECT id FROM User LIMIT 1")
    user_row = cursor.fetchone()
    if not user_row:
        print("❌ No User found in DB. Please sign up in Fluid Calendar first.")
        return
    user_id = user_row[0]

    # Get Feed ID
    cursor.execute("SELECT id FROM CalendarFeed WHERE name = 'VibeOS' AND userId = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        feed_id = row[0]
    else:
        feed_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO CalendarFeed (id, name, type, enabled, userId, createdAt, updatedAt) VALUES (?, 'VibeOS', 'LOCAL', 1, ?, ?, ?)", 
                       (feed_id, user_id, to_iso_now(), to_iso_now()))

    # 3. PREPARE DATA FOR OPTIMIZER
    # Flatten Tasks
    tasks_to_schedule = []
    
    for group_idx, course in enumerate(raw_courses):
        course_name = course.get("course_name", "Unknown")
        category = course.get("category", "General")
        
        for order_idx, subtask in enumerate(course.get("subtasks", [])):
            full_title = f"{course_name}: {subtask['topic']}"
            
            # Check Duplicate (DB Call) - Avoid re-scheduling existing tasks
            cursor.execute("SELECT id FROM CalendarEvent WHERE title = ? AND feedId = ?", (full_title, feed_id))
            if cursor.fetchone():
                continue # Skip existing
            
            tasks_to_schedule.append({
                "name": full_title,
                "duration": subtask['duration'],
                "category": category,
                "group_id": group_idx, # Sequence maintain karne ke liye
                "order": order_idx,
                "feedId": feed_id
            })

    if not tasks_to_schedule:
        print("✨ No new tasks to schedule. Everything is up to date!")
        conn.close()
        return

    # Flatten Slots (Agles 14 din ke slots generate karo)
    now = datetime.now()
    if now.hour > 20: now += timedelta(days=1) # Agar raat ho gayi hai, kal se shuru karo
    
    available_slots = flatten_week_template_to_slots(week_template, now, days_ahead=14)

    if not available_slots:
        print("❌ No slots available in week_template.json!")
        conn.close()
        return

    # 4. RUN OPTIMIZER 🧠
    optimizer = VibeOptimizer(tasks_to_schedule, available_slots)
    schedule_result = optimizer.solve()

    # 5. WRITE TO DB
    new_count = 0
    if schedule_result:
        for item in schedule_result:
            event_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO CalendarEvent (id, feedId, title, start, end, allDay, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            ''', (
                event_id, feed_id, item['title'], 
                to_utc_iso(item['start']), to_utc_iso(item['end']),
                to_iso_now(), to_iso_now()
            ))
            print(f"   ✅ Optimized: {item['title']} -> {item['start'].strftime('%a %H:%M')}")
            new_count += 1
    else:
        print("⚠️ Optimizer could not find a solution for pending tasks.")

    conn.commit()
    conn.close()
    print(f"🏗️ Optimization Done. Scheduled {new_count} tasks.")

if __name__ == "__main__":
    distribute_syllabus()