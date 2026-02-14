import sys
import os
import sqlite3
import uuid
import json
from datetime import datetime, timedelta, timezone

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from core.solver.solver import VibeOptimizer
from core.solver.utils import flatten_template_to_slots, to_utc_iso, to_iso_now
from core.loader.config_loader import load_week_template
from core.planner.architect import VibeArchitect

# Paths
VIBE_DB_PATH = os.path.join(BASE_DIR, "data", "db", "vibe_core.db")
FLUID_DB_PATH = os.path.join(BASE_DIR, "gui", "fluid-calendar", "prisma", "dev.db")
ROUTINE_FILE = os.path.join(BASE_DIR, "data", "config", "routine.json")

def get_fluid_db():
    if not os.path.exists(FLUID_DB_PATH):
        raise FileNotFoundError(f"Fluid DB not found at: {FLUID_DB_PATH}")
    return sqlite3.connect(FLUID_DB_PATH)

def sync_routine_blocks(fluid_cursor, feed_id, current_date):
    """Sync Routine blocks for a SPECIFIC day to save CPU"""
    if not os.path.exists(ROUTINE_FILE): return
    try:
        with open(ROUTINE_FILE, "r", encoding="utf-8") as f:
            routine = json.load(f).get("routine_blocks", [])
    except Exception as e:
        return

    day_str = current_date.strftime("%Y-%m-%d")
    for block in routine:
        title = block['name']
        start_dt = datetime.strptime(f"{day_str} {block['start']}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{day_str} {block['end']}", "%Y-%m-%d %H:%M")
        if end_dt < start_dt: end_dt += timedelta(days=1)
        
        fluid_cursor.execute("SELECT id FROM CalendarEvent WHERE title = ? AND start LIKE ?", (title, f"{day_str}%"))
        if not fluid_cursor.fetchone():
            fluid_cursor.execute("INSERT INTO CalendarEvent (id, feedId, title, start, end, allDay, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, 0, ?, ?)", 
            (str(uuid.uuid4()), feed_id, title, to_utc_iso(start_dt), to_utc_iso(end_dt), to_iso_now(), to_iso_now()))

def run_planner():
    print("\n🏗️  Starting VibeOS Smart Planner (15-Day Lookahead)...")
    
    # 1. SETUP CONNECTIONS
    try:
        fluid_conn = get_fluid_db()
        fluid_cursor = fluid_conn.cursor()
        vibe_conn = sqlite3.connect(VIBE_DB_PATH)
        vibe_conn.row_factory = sqlite3.Row
        v_cursor = vibe_conn.cursor()
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        return

    # 2. GET USER & FEED
    fluid_cursor.execute("SELECT id FROM User LIMIT 1")
    user_row = fluid_cursor.fetchone()
    if not user_row:
        user_id = "user_default_" + str(uuid.uuid4())[:8]
        fluid_cursor.execute("INSERT INTO User (id, email, name) VALUES (?, ?, ?)", 
                             (user_id, "admin@vibeos.com", "Vibe Admin"))
        fluid_conn.commit()
    else:
        user_id = user_row[0]

    fluid_cursor.execute("SELECT id FROM CalendarFeed WHERE name = 'VibeOS' AND userId = ?", (user_id,))
    row = fluid_cursor.fetchone()
    feed_id = row[0] if row else str(uuid.uuid4())
    if not row:
        fluid_cursor.execute("INSERT INTO CalendarFeed (id, name, type, enabled, userId, createdAt, updatedAt) VALUES (?, 'VibeOS', 'LOCAL', 1, ?, ?, ?)", (feed_id, user_id, to_iso_now(), to_iso_now()))

    # 3. SMART PLANNING LOGIC (15 Days)
    template = load_week_template()
    architect = VibeArchitect(VIBE_DB_PATH)
    
    now = datetime.now()
    if now.hour > 20: now += timedelta(days=1)
    
    total_scheduled = 0
    LOOKAHEAD_DAYS = 15 # Bhai ka order: Max 15 days calculation

    # FETCH ALL PENDING once to manage in memory during this run
    v_cursor.execute("SELECT * FROM tasks WHERE status = 'PENDING' AND is_soft_deleted = 0 ORDER BY priority DESC, created_at ASC")
    backlog_pool = [dict(row) for row in v_cursor.fetchall()]

    if not backlog_pool:
        print("✨ No pending tasks found. Chill maar!")
        return

    for day_offset in range(LOOKAHEAD_DAYS):
        if not backlog_pool: break

        current_date = now + timedelta(days=day_offset)
        
        # A. Sync Routine for this specific day
        sync_routine_blocks(fluid_cursor, feed_id, current_date)

        # B. Get Slots for this day
        daily_slots = flatten_template_to_slots(template, current_date, days_ahead=1)
        if not daily_slots: continue

        # C. Get Balanced Batch for today (Uses Architect logic internally)
        # Hum yahan daily_batch simulate kar rahe hain from memory pool
        used_cats = {}
        day_batch = []
        remaining = []
        
        for task in backlog_pool:
            cat = task.get('category', 'General')
            if used_cats.get(cat, 0) < 1: # Limit: 1 task per category per day
                day_batch.append(task)
                used_cats[cat] = used_cats.get(cat, 0) + 1
            else:
                remaining.append(task)

        if not day_batch:
            backlog_pool = remaining
            continue

        # D. Run Optimizer for the day
        optimizer = VibeOptimizer(day_batch, daily_slots)
        schedule = optimizer.solve()

        if schedule:
            print(f"📅 Scheduling {current_date.strftime('%a, %d %b')}:")
            scheduled_ids = []
            for item in schedule:
                event_id = str(uuid.uuid4())
                fluid_cursor.execute("INSERT INTO CalendarEvent (id, feedId, title, start, end, allDay, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, 0, ?, ?)", 
                                     (event_id, feed_id, item['name'], to_utc_iso(item['start']), to_utc_iso(item['end']), to_iso_now(), to_iso_now()))
                
                v_cursor.execute("UPDATE tasks SET status = 'SCHEDULED', scheduled_start = ?, calendar_event_id = ? WHERE id = ?", 
                                 (to_utc_iso(item['start']), event_id, item['task_id']))
                
                print(f"   ✅ {item['name']} -> {item['start'].strftime('%H:%M')}")
                scheduled_ids.append(item['task_id'])
                total_scheduled += 1
            
            # Update backlog for next day's iteration
            backlog_pool = [t for t in day_batch if t['id'] not in scheduled_ids] + remaining
        else:
            backlog_pool = day_batch + remaining

    # 4. FINAL COMMIT
    fluid_conn.commit()
    vibe_conn.commit()
    fluid_conn.close()
    vibe_conn.close()
    
    print(f"\n✅ Planner Cycle Finished. {total_scheduled} tasks spread over 15 days. CPU is safe! 😎")

if __name__ == "__main__":
    run_planner()