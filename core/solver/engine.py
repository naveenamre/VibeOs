import sys
import os
import sqlite3
import uuid
from datetime import datetime, timedelta

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
FLUID_DB_PATH = os.path.join(BASE_DIR, "gui", "fluid-calendar", "prisma", "dev.dbcd")

# --- IMPORTS ---
from core.loader.task_loader import load_all_inputs
from core.loader.config_loader import load_week_template
from core.solver.solver import VibeOptimizer
from core.solver.utils import flatten_template_to_slots, to_utc_iso, to_iso_now

def get_db_connection():
    return sqlite3.connect(FLUID_DB_PATH)

def run_orchestrator():
    print("\n🚀 VibeOS Engine Starting...")

    # 1. LOAD DATA (Inputs & Config)
    tasks_raw = load_all_inputs()
    week_template = load_week_template()

    if not tasks_raw:
        print("❌ No tasks found. Add JSON files to 'data/inputs/'")
        return

    # 2. SETUP DATABASE & FEED
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get User ID
    cursor.execute("SELECT id FROM User LIMIT 1")
    user_row = cursor.fetchone()
    if not user_row:
        print("❌ System Error: No User found in Fluid Calendar DB.")
        return
    user_id = user_row[0]

    # Get/Create VibeOS Feed
    cursor.execute("SELECT id FROM CalendarFeed WHERE name = 'VibeOS' AND userId = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        feed_id = row[0]
    else:
        feed_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO CalendarFeed (id, name, type, enabled, userId, createdAt, updatedAt) VALUES (?, 'VibeOS', 'LOCAL', 1, ?, ?, ?)", 
                       (feed_id, user_id, to_iso_now(), to_iso_now()))

    # 3. PREPARE TASKS FOR SOLVER
    # (Flatten courses into individual task items)
    tasks_to_schedule = []
    
    print("🔍 Checking for duplicates...")
    for group_idx, course in enumerate(tasks_raw):
        course_name = course.get("course_name", "Unknown")
        category = course.get("category", "General")
        
        for order_idx, subtask in enumerate(course.get("subtasks", [])):
            full_title = f"{course_name}: {subtask['topic']}"
            
            # Check DB for Duplicates (Smart Check)
            cursor.execute("SELECT id FROM CalendarEvent WHERE title = ? AND feedId = ?", (full_title, feed_id))
            if cursor.fetchone():
                continue # Skip if already scheduled
            
            tasks_to_schedule.append({
                "name": full_title,
                "duration": subtask['duration'],
                "category": category,
                "group_id": group_idx, # Sequence maintain karne ke liye
                "order": order_idx,
                "feedId": feed_id
            })

    if not tasks_to_schedule:
        print("✨ All tasks are up to date! Nothing new to plan.")
        conn.close()
        return

    # 4. GENERATE SLOTS (Next 14 Days)
    now = datetime.now()
    if now.hour > 20: now += timedelta(days=1) # Agar raat hai toh kal se shuru karo
    
    available_slots = flatten_template_to_slots(week_template, now, days_ahead=14)

    if not available_slots:
        print("❌ Error: No slots available in Week Template.")
        return

    # 5. RUN SOLVER (The Brain) 🧠
    optimizer = VibeOptimizer(tasks_to_schedule, available_slots)
    schedule_result = optimizer.solve()

    # 6. SAVE RESULTS TO DB
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
            print(f"   🗓️  Booked: {item['title']} -> {item['start'].strftime('%a %H:%M')}")
            new_count += 1
    else:
        print("⚠️  Optimizer could not find a solution (Check slot durations/categories).")

    conn.commit()
    conn.close()
    print(f"\n✅ Engine Finished. Scheduled {new_count} new tasks.")

if __name__ == "__main__":
    run_orchestrator()