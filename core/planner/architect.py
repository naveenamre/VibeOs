import sys
import os
import json
import sqlite3
import uuid
import glob
from datetime import datetime, timedelta, timezone

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUTS_DIR = os.path.join(DATA_DIR, "inputs")
FLUID_DB_PATH = os.path.join(BASE_DIR, "gui", "fluid-calendar", "prisma", "dev.dbcd")

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

# --- DATE HELPERS (WARNING FIXED) ---
def to_utc_iso(dt_local):
    """IST to UTC conversion for DB storage"""
    # Local time se 5:30 ghante ghatao taaki Calendar par sahi dikhe
    dt_utc = dt_local - timedelta(hours=5, minutes=30)
    # Use timezone-aware UTC object
    return dt_utc.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def to_iso_now():
    """Current UTC time in ISO format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

# --- THE ARCHITECT LOGIC ---
def distribute_syllabus():
    print("🏗️ Architect 2.0 (Smart Mode) Starting...")
    
    courses = load_all_inputs()
    week_template = load_week_template()
    
    if not courses:
        print("❌ No inputs found! Add files to 'data/inputs/'")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. User & Feed Setup
    cursor.execute("SELECT id FROM User LIMIT 1")
    user_row = cursor.fetchone()
    if not user_row: return
    user_id = user_row[0]

    cursor.execute("SELECT id FROM CalendarFeed WHERE name = 'VibeOS' AND userId = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        feed_id = row[0]
    else:
        feed_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO CalendarFeed (id, name, type, enabled, userId, createdAt, updatedAt) VALUES (?, 'VibeOS', 'LOCAL', 1, ?, ?, ?)", 
                       (feed_id, user_id, to_iso_now(), to_iso_now()))

    # 2. Get Existing Tasks (To avoid duplicates)
    # Hum title check karenge. Agar 'Chemistry: Intro' pehle se hai, toh wapas nahi dalenge.
    cursor.execute("SELECT title FROM CalendarEvent WHERE feedId = ?", (feed_id,))
    existing_titles = {row[0] for row in cursor.fetchall()}

    # 3. Start Planning
    current_date = datetime.now()
    if current_date.hour > 20: current_date += timedelta(days=1)
    
    new_tasks_count = 0
    
    for course in courses:
        course_name = course.get("course_name", "Unknown")
        category = course.get("category", "General")
        subtasks = course.get("subtasks", [])
        
        print(f"🔹 Scanning: {course_name}...")

        plan_date = current_date
        task_idx = 0
        
        while task_idx < len(subtasks):
            current_subtask = subtasks[task_idx]
            topic_name = current_subtask["topic"]
            topic_duration = current_subtask["duration"]
            
            # UNIQUE TITLE GENERATION
            full_title = f"{course_name}: {topic_name}"
            
            # 🔥 DUPLICATE CHECK
            if full_title in existing_titles:
                # print(f"   ⏭️ Skipped (Already Exists): {topic_name}")
                task_idx += 1
                continue

            day_name = plan_date.strftime("%A")
            date_str = plan_date.strftime("%Y-%m-%d")
            
            assigned = False
            if day_name in week_template:
                daily_slots = week_template[day_name]
                
                for slot in daily_slots:
                    if slot["category"] == category and topic_duration <= slot["duration"]:
                        
                        start_time_str = f"{date_str} {slot['start']}"
                        start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
                        end_dt = start_dt + timedelta(minutes=topic_duration)
                        
                        event_id = str(uuid.uuid4())
                        
                        cursor.execute('''
                            INSERT INTO CalendarEvent (id, feedId, title, start, end, allDay, createdAt, updatedAt)
                            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                        ''', (
                            event_id, feed_id, full_title, 
                            to_utc_iso(start_dt), to_utc_iso(end_dt),
                            to_iso_now(), to_iso_now()
                        ))
                        
                        print(f"   ✅ Scheduled: '{topic_name}' -> {day_name} {slot['start']}")
                        existing_titles.add(full_title) # Add to local cache
                        new_tasks_count += 1
                        task_idx += 1
                        assigned = True
                        break 
            
            # Agar aaj slot nahi mila ya assign ho gaya, agle din check karo
            if not assigned or task_idx < len(subtasks):
                 plan_date += timedelta(days=1)
            
            if (plan_date - current_date).days > 365: break

    conn.commit()
    conn.close()
    
    if new_tasks_count == 0:
        print("✨ Everything is up to date! No new tasks added.")
    else:
        print(f"🏗️ Done. Added {new_tasks_count} new tasks.")

if __name__ == "__main__":
    distribute_syllabus()