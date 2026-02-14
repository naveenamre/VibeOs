import sqlite3
import os
import sys
from datetime import datetime, timezone, timedelta

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIBE_DB_PATH = os.path.join(BASE_DIR, "data", "db", "vibe_core.db")

# 🔥 FIX: Path corrected to 'dev.db' (Not dev.dbcd)
FLUID_DB_PATH = os.path.join(BASE_DIR, "gui", "fluid-calendar", "prisma", "dev.db")

def get_vibe_db():
    conn = sqlite3.connect(VIBE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_fluid_db():
    # Check if file exists
    if not os.path.exists(FLUID_DB_PATH):
        return None
    return sqlite3.connect(FLUID_DB_PATH)

def run_ghost_protocol():
    print("\n👻 Starting Ghost Protocol (Sync Check)...")
    
    vibe_conn = get_vibe_db()
    fluid_conn = get_fluid_db()

    if not fluid_conn:
        print("   ⚠️ Fluid DB not found. Skipping Ghost Protocol.")
        return
    
    v_cursor = vibe_conn.cursor()
    f_cursor = fluid_conn.cursor()

    # 🔥 SAFETY CHECK: Check if Table Exists
    try:
        f_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='CalendarEvent'")
        if not f_cursor.fetchone():
            print("   ⚠️ Fluid DB exists but tables are missing. Skipping Ghost Protocol.")
            return
    except Exception as e:
        print(f"   ❌ DB Connection Error: {e}")
        return

    # 1. Fetch all tasks that VibeOS thinks are SCHEDULED
    v_cursor.execute("""
        SELECT id, name, calendar_event_id, scheduled_start 
        FROM tasks 
        WHERE status = 'SCHEDULED' AND calendar_event_id IS NOT NULL
    """)
    vibe_tasks = v_cursor.fetchall()
    
    updates_count = 0
    deleted_count = 0

    for task in vibe_tasks:
        v_id = task['id']
        f_id = task['calendar_event_id']
        v_start = task['scheduled_start']

        # 2. Check logic in Fluid DB
        f_cursor.execute("SELECT start, end FROM CalendarEvent WHERE id = ?", (f_id,))
        f_event = f_cursor.fetchone()

        # CASE A: Event Deleted in Calendar ❌
        if not f_event:
            print(f"   🗑️  Task Deleted in UI: {task['name']} -> Moving to Backlog")
            
            # Change status to 'MISSED' (or PENDING if you want retry)
            v_cursor.execute("""
                UPDATE tasks 
                SET status = 'MISSED', 
                    is_soft_deleted = 1, 
                    calendar_event_id = NULL 
                WHERE id = ?
            """, (v_id,))
            deleted_count += 1

        # CASE B: Event Moved in Calendar ↔️
        else:
            f_start_str = f_event[0]
            
            if v_start != f_start_str:
                print(f"   🔄 Task Moved in UI: {task['name']}")
                print(f"      Old: {v_start} -> New: {f_start_str}")
                
                v_cursor.execute("UPDATE tasks SET scheduled_start = ? WHERE id = ?", (f_start_str, v_id))
                v_cursor.execute("INSERT INTO history_log (task_id, action, planned_start, actual_start) VALUES (?, 'MOVED', ?, ?)", 
                                 (v_id, v_start, f_start_str))
                updates_count += 1

    vibe_conn.commit()
    vibe_conn.close()
    fluid_conn.close()
    
    print(f"✅ Ghost Protocol Finished. Moved: {updates_count}, Backlogged: {deleted_count}")

if __name__ == "__main__":
    run_ghost_protocol()